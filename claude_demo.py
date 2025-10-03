import os
import sys
import json
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
 from rich.console import Console
 from rich.panel import Panel
 from rich.text import Text
 from rich.markdown import Markdown
 from rich.prompt import Prompt
 print("✓ Rich package found")
 RICH_AVAILABLE = True
except ImportError:
 print("❌ Missing 'rich' package. Install with: pip install rich")
 print("Falling back to basic console output...")
 RICH_AVAILABLE = False


class ClaudeChatClient:
 def __init__(self, api_key: Optional[str] = None):
     """Initialize the Claude chat client."""
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
         print("  python claude_chat.py")
         sys.exit(1)

     # Initialize the Anthropic client
     try:
         # On Windows, disable SSL verification due to common certificate issues
         if sys.platform == 'win32':
             import urllib3
             urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
             self.client = anthropic.Anthropic(api_key=self.api_key,
                http_client=httpx.Client(verify=False))
             print("✓ Connected to Anthropic API (SSL verification disabled on Windows)")
         else:
             self.client = anthropic.Anthropic(api_key=self.api_key,
        http_client=httpx.Client(verify=certifi.where()))
             print("✓ Connected to Anthropic API")
     except Exception as e:
         print(f"❌ Error initializing Anthropic client: {e}")
         sys.exit(1)

 def send_message(self, message: str, model: str = "claude-sonnet-4-5-20250929") -> str:
     """Send a message to Claude and return the response."""
     try:
         response = self.client.messages.create(
             model=model,
             max_tokens=4000,
             temperature=0.7,
             messages=[
                 {
                     "role": "user",
                     "content": message
                 }
             ]
         )
         return response.content[0].text
     except Exception as e:
         print(f"❌ Error sending message: {e}")
         return None

 def display_response_rich(self, user_message: str, claude_response: str):
     """Display the conversation with rich formatting."""
     # Display user message
     user_panel = Panel(
         Text(user_message, style="cyan"),
         title="[bold blue]Your Message",
         border_style="blue",
         padding=(1, 2)
     )
     self.console.print(user_panel)

     # Display Claude's response
     if claude_response:
         # Try to render as markdown if it contains markdown formatting
         try:
             if any(marker in claude_response for marker in ['```', '**', '*', '#', '-', '1.']):
                 claude_content = Markdown(claude_response)
             else:
                 claude_content = Text(claude_response, style="white")
         except:
             claude_content = Text(claude_response, style="white")

         response_panel = Panel(
             claude_content,
             title="[bold green]Claude's Response",
             border_style="green",
             padding=(1, 2)
         )
         self.console.print(response_panel)

     self.console.print()  # Add spacing

 def display_response_basic(self, user_message: str, claude_response: str):
     """Display the conversation with basic formatting."""
     print("\n" + "="*80)
     print("🧑 YOUR MESSAGE:")
     print("-" * 40)
     print(user_message)
     print("\n" + "="*80)
     print("🤖 CLAUDE'S RESPONSE:")
     print("-" * 40)
     if claude_response:
         print(claude_response)
     else:
         print("No response received.")
     print("="*80 + "\n")

 def display_response(self, user_message: str, claude_response: str):
     """Display the conversation nicely formatted."""
     if RICH_AVAILABLE:
         self.display_response_rich(user_message, claude_response)
     else:
         self.display_response_basic(user_message, claude_response)

 def interactive_chat(self):
     """Start an interactive chat session."""
     if RICH_AVAILABLE:
         self.console.print(
             Panel(
                 "[bold yellow]Claude 4.5 Chat Client[/bold yellow]\n"
                 "Type your messages and press Enter to send.\n"
                 "Type 'quit', 'exit', or 'q' to end the session.",
                 title="Welcome",
                 border_style="yellow"
             )
         )
     else:
         print("\n" + "="*80)
         print("🚀 CLAUDE 4.5 CHAT CLIENT")
         print("="*80)
         print("Type your messages and press Enter to send.")
         print("Type 'quit', 'exit', or 'q' to end the session.")
         print("="*80)

     while True:
         try:
             # Get user input
             if RICH_AVAILABLE:
                 user_input = Prompt.ask("\n[bold cyan]You")
             else:
                 user_input = input("\n🧑 You: ").strip()

             # Check for exit commands
             if user_input.lower() in ['quit', 'exit', 'q']:
                 if RICH_AVAILABLE:
                     self.console.print("[yellow]Goodbye![/yellow]")
                 else:
                     print("👋 Goodbye!")
                 break

             if not user_input.strip():
                 continue

             # Show thinking indicator
             if RICH_AVAILABLE:
                 with self.console.status("[bold green]Claude is thinking..."):
                     response = self.send_message(user_input)
             else:
                 print("⏳ Claude is thinking...")
                 response = self.send_message(user_input)

             # Display the conversation
             self.display_response(user_input, response)

         except KeyboardInterrupt:
             if RICH_AVAILABLE:
                 self.console.print("\n[yellow]Chat interrupted. Goodbye![/yellow]")
             else:
                 print("\n👋 Chat interrupted. Goodbye!")
             break
         except Exception as e:
             print(f"❌ Unexpected error: {e}")

 def single_message(self, message: str):
     """Send a single message and display the response."""
     if RICH_AVAILABLE:
         self.console.print(
             Panel(
                 "[bold yellow]Claude 4.5 Single Message[/bold yellow]",
                 title="Mode",
                 border_style="yellow"
             )
         )
         with self.console.status("[bold green]Claude is thinking..."):
             response = self.send_message(message)
     else:
         print("\n" + "="*80)
         print("🚀 CLAUDE 4.5 SINGLE MESSAGE")
         print("="*80)
         print("⏳ Claude is thinking...")
         response = self.send_message(message)

     self.display_response(message, response)


def main():
 """Main function to run the Claude chat client."""
 import argparse

 parser = argparse.ArgumentParser(description="Claude 4.5 Chat Client")
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

 args = parser.parse_args()

 print("🚀 Initializing Claude Chat Client...")

 # Initialize the client
 client = ClaudeChatClient(api_key=args.api_key)

 # Run based on arguments
 if args.message:
     client.single_message(args.message)
 else:
     client.interactive_chat()


if __name__ == "__main__":
 main()