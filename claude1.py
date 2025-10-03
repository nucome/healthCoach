import os
import sys
import socket
from typing import Optional

import certifi
import httpx

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Check for required packages
try:
 import anthropic
 print("✓ Anthropic package found")
except ImportError:
 print("❌ Missing 'anthropic' package. Install with: pip install anthropic")
 sys.exit(1)

try:
 import requests
 print("✓ Requests package found")
 REQUESTS_AVAILABLE = True
except ImportError:
 print("❌ Missing 'requests' package. Install with: pip install requests")
 REQUESTS_AVAILABLE = False

try:
 from rich.console import Console
 from rich.panel import Panel
 from rich.text import Text
 from rich.markdown import Markdown
 from rich.prompt import Prompt, Confirm
 from rich.table import Table
 print("✓ Rich package found")
 RICH_AVAILABLE = True
except ImportError:
 print("❌ Missing 'rich' package. Install with: pip install rich")
 print("Falling back to basic console output...")
 RICH_AVAILABLE = False


class NetworkDiagnostics:
 """Network diagnostic utilities."""

 @staticmethod
 def test_internet_connection():
     """Test basic internet connectivity."""
     try:
         socket.create_connection(("8.8.8.8", 53), timeout=5)
         return True, "Internet connection: OK"
     except OSError:
         return False, "No internet connection detected"

 @staticmethod
 def test_dns_resolution(hostname="api.anthropic.com"):
     """Test DNS resolution for Anthropic API."""
     try:
         socket.gethostbyname(hostname)
         return True, f"DNS resolution for {hostname}: OK"
     except socket.gaierror:
         return False, f"DNS resolution failed for {hostname}"

 @staticmethod
 def test_anthropic_api_reachability():
     """Test if Anthropic API endpoint is reachable."""
     if not REQUESTS_AVAILABLE:
         return None, "Requests package not available for API testing"

     try:
         # On Windows, disable SSL verification
         verify_ssl = False if sys.platform == 'win32' else certifi.where()
         if sys.platform == 'win32':
             import urllib3
             urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

         response = requests.get(
             "https://api.anthropic.com/v1/messages",
             headers={"anthropic-version": "2023-06-01"},
             timeout=10,
             verify=verify_ssl
         )
         # We expect a 400, 401, or 405 response, not 200, since we're not sending proper auth/data
         if response.status_code in [400, 401, 405]:
             return True, f"Anthropic API endpoint reachable (status: {response.status_code})"
         else:
             return False, f"Unexpected response from API (status: {response.status_code})"
     except requests.exceptions.RequestException as e:
         return False, f"Cannot reach Anthropic API: {e}"

 @staticmethod
 def run_full_diagnostics():
     """Run complete network diagnostics."""
     results = []

     # Test internet connection
     success, message = NetworkDiagnostics.test_internet_connection()
     results.append(("Internet", success, message))

     # Test DNS resolution
     success, message = NetworkDiagnostics.test_dns_resolution()
     results.append(("DNS", success, message))

     # Test API reachability
     success, message = NetworkDiagnostics.test_anthropic_api_reachability()
     results.append(("API Endpoint", success, message))

     return results


class ClaudeChatClientDiagnostic:
 def __init__(self, api_key: Optional[str] = None):
     """Initialize the Claude chat client with diagnostics."""
     if RICH_AVAILABLE:
         self.console = Console()

     # Get API key from environment variable or parameter
     self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

     if not self.api_key:
         print("❌ Error: No API key found!")
         print("Please set the ANTHROPIC_API_KEY environment variable or pass it as a parameter.")
         print("You can get an API key from: https://console.anthropic.com/")
         print("\nExample usage:")
         print("  export ANTHROPIC_API_KEY=your_api_key_here")
         print("  python claude_chat_diagnostic.py")
         sys.exit(1)

     # Initialize the Anthropic client
     try:
         # On Windows, disable SSL verification due to common certificate issues
         if sys.platform == 'win32':
             import urllib3
             urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
             self.client = anthropic.Anthropic(api_key=self.api_key,
        http_client=httpx.Client(verify=False))
             print("✓ Connected to Anthropic API client (SSL verification disabled on Windows)")
         else:
             self.client = anthropic.Anthropic(api_key=self.api_key,
        http_client=httpx.Client(verify=certifi.where()))
             print("✓ Connected to Anthropic API client")
     except Exception as e:
         print(f"❌ Error initializing Anthropic client: {e}")
         sys.exit(1)

 def run_diagnostics(self):
     """Run network diagnostics and display results."""
     if RICH_AVAILABLE:
         self.console.print("\n[bold yellow]🔍 Running Network Diagnostics...[/bold yellow]")
     else:
         print("\n🔍 Running Network Diagnostics...")

     results = NetworkDiagnostics.run_full_diagnostics()

     if RICH_AVAILABLE:
         table = Table(title="Network Diagnostic Results")
         table.add_column("Test", style="cyan")
         table.add_column("Status", justify="center")
         table.add_column("Details", style="white")

         for test_name, success, message in results:
             status = "[green]✓ PASS[/green]" if success else "[red]✗ FAIL[/red]" if success is not None else "[yellow]? SKIP[/yellow]"
             table.add_row(test_name, status, message)

         self.console.print(table)
     else:
         print("\nDiagnostic Results:")
         print("-" * 60)
         for test_name, success, message in results:
             status = "✓ PASS" if success else "✗ FAIL" if success is not None else "? SKIP"
             print(f"{test_name:<15} | {status:<7} | {message}")

     # Check if all critical tests passed
     critical_tests = [r for r in results if r[0] in ["Internet", "DNS"]]
     all_critical_passed = all(r[1] for r in critical_tests if r[1] is not None)

     if not all_critical_passed:
         if RICH_AVAILABLE:
             self.console.print("\n[red]⚠️  Critical network issues detected. API calls may fail.[/red]")
         else:
             print("\n⚠️  Critical network issues detected. API calls may fail.")

     return all_critical_passed

 def send_message(self, message: str, model: str = "claude-sonnet-4-5-20250929") -> str:
     """Send a message to Claude with detailed error handling."""
     try:
         if RICH_AVAILABLE:
             with self.console.status("[bold green]Sending message to Claude..."):
                 response = self.client.messages.create(
                     model=model,
                     max_tokens=4000,
                     temperature=0.7,
                     messages=[{"role": "user", "content": message}]
                 )
         else:
             print("⏳ Sending message to Claude...")
             response = self.client.messages.create(
                 model=model,
                 max_tokens=4000,
                 temperature=0.7,
                 messages=[{"role": "user", "content": message}]
             )

         return response.content[0].text

     except anthropic.APIConnectionError as e:
         print(f"❌ Connection error: {e}")
         print("\n🔧 Troubleshooting suggestions:")
         print("   1. Check your internet connection")
         print("   2. Try running diagnostics: python claude_chat_diagnostic.py --diagnose")
         print("   3. Check if you're behind a firewall or proxy")
         print("   4. Try a different network (mobile hotspot)")
         return None

     except anthropic.RateLimitError as e:
         print(f"❌ Rate limit error: {e}")
         print("   Please wait a moment and try again.")
         return None

     except anthropic.APIStatusError as e:
         print(f"❌ API error (status {e.status_code}): {e.message}")
         if e.status_code == 401:
             print("   Check your API key is correct and active")
         elif e.status_code == 429:
             print("   You've hit the rate limit, please wait")
         return None

     except anthropic.AuthenticationError as e:
         print(f"❌ Authentication error: {e}")
         print("   Your API key may be invalid or expired")
         print("   Get a new key from: https://console.anthropic.com/")
         return None

     except Exception as e:
         print(f"❌ Unexpected error: {e}")
         print(f"   Error type: {type(e).__name__}")
         print("\n🔧 Try running diagnostics to identify the issue:")
         print("   python claude_chat_diagnostic.py --diagnose")
         return None

 def test_simple_message(self):
     """Test with a simple message."""
     test_message = "Hello! Can you respond with just 'Connection successful' to test our connection?"

     if RICH_AVAILABLE:
         self.console.print(f"\n[bold blue]🧪 Testing with message:[/bold blue] {test_message}")
     else:
         print(f"\n🧪 Testing with message: {test_message}")

     response = self.send_message(test_message)

     if response:
         if RICH_AVAILABLE:
             self.console.print(Panel(response, title="[green]✓ Test Successful", border_style="green"))
         else:
             print("\n" + "="*60)
             print("✓ TEST SUCCESSFUL - Claude's Response:")
             print("-" * 60)
             print(response)
             print("="*60)
         return True
     else:
         if RICH_AVAILABLE:
             self.console.print("[red]✗ Test failed - no response received[/red]")
         else:
             print("✗ Test failed - no response received")
         return False


def main():
 """Main function with diagnostic options."""
 import argparse

 parser = argparse.ArgumentParser(description="Claude 4.5 Chat Client with Diagnostics")
 parser.add_argument(
     "--message", "-m",
     type=str,
     help="Send a single message instead of starting interactive chat"
 )
 parser.add_argument(
     "--api-key", "-k",
     type=str,
     help="Anthropic API key (overrides environment variable)"
 )
 parser.add_argument(
     "--model",
     type=str,
     default="claude-sonnet-4-5-20250929",
     help="Claude model to use (default: claude-sonnet-4-5-20250929)"
 )
 parser.add_argument(
     "--diagnose", "-d",
     action="store_true",
     help="Run network diagnostics only"
 )
 parser.add_argument(
     "--test", "-t",
     action="store_true",
     help="Run a simple connection test"
 )

 args = parser.parse_args()

 print("🚀 Initializing Claude Chat Client (Diagnostic Mode)...")

 # Initialize the client
 client = ClaudeChatClientDiagnostic(api_key=args.api_key)

 # Run diagnostics if requested
 if args.diagnose:
     client.run_diagnostics()
     return

 # Run test if requested
 if args.test:
     client.run_diagnostics()
     client.test_simple_message()
     return

 # Run based on arguments
 if args.message:
     print("\n🔍 Running quick diagnostics...")
     diagnostics_passed = client.run_diagnostics()

     if diagnostics_passed or input("\nDiagnostics failed. Continue anyway? (y/N): ").lower().startswith('y'):
         response = client.send_message(args.message)
         if response:
             print("\n" + "="*60)
             print("CLAUDE'S RESPONSE:")
             print("="*60)
             print(response)
             print("="*60)


if __name__ == "__main__":
 main()