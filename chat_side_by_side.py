import asyncio
import json
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import aiohttp
import threading

# API Keys - Load from environment or use defaults
API_KEYS = {
    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'openai': os.getenv('OPENAI_API_KEY'),
    'google': os.getenv('GOOGLE_API_KEY')
}

# Prompt history file
HISTORY_FILE = 'prompt_history.json'
MAX_HISTORY = 10


def load_prompt_history():
    """Load prompt history from file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle legacy format with objects
                if data and isinstance(data[0], dict):
                    # Migrate old format to new format (just strings)
                    prompts = [entry['prompt'] for entry in data if 'prompt' in entry]
                    # Remove duplicates while preserving order
                    seen = set()
                    result = []
                    for p in prompts:
                        if p not in seen:
                            seen.add(p)
                            result.append(p)
                    return result
                return data
        except:
            return []
    return []


def save_prompt_history(history):
    """Save prompt history to file."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[-MAX_HISTORY:], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save prompt history: {e}")


def add_prompt_to_history(prompt_text):
    """Add a new prompt to history, avoiding duplicates."""
    history = load_prompt_history()

    # Remove existing occurrence of this prompt (if any)
    history = [p for p in history if p != prompt_text]

    # Add the prompt to the end (most recent)
    history.append(prompt_text)

    save_prompt_history(history)
    return history

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Multi-Model Comparison</title>
    <style>
        :root {
            color-scheme: light dark;
            --bg: #f4f4f4;
            --fg: #222;
            --accent: #2563eb;
            --card-bg: #ffffff;
            --border: #d4d4d4;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--fg);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        header {
            background: var(--card-bg);
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
        }

        header h1 {
            margin: 0;
            font-size: 1.5rem;
            letter-spacing: 0.02em;
        }

        header p {
            margin: 0.5rem 0 0;
            color: #555;
            font-size: 0.95rem;
        }

        .input-section {
            background: var(--card-bg);
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .prompt-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            gap: 1rem;
        }

        label {
            font-weight: 550;
            font-size: 0.95rem;
            display: block;
            margin: 0;
        }

        .history-container {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-shrink: 0;
        }

        .history-label {
            font-size: 0.85rem;
            color: #666;
            white-space: nowrap;
        }

        select {
            border-radius: 10px;
            border: 1px solid var(--border);
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            background: rgba(255, 255, 255, 0.9);
            cursor: pointer;
            min-width: 200px;
        }

        select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
        }

        textarea {
            width: 100%;
            border-radius: 10px;
            border: 1px solid var(--border);
            padding: 0.75rem 1rem;
            font: inherit;
            transition: border 0.2s ease;
            background: rgba(255, 255, 255, 0.9);
            min-height: 120px;
            resize: vertical;
        }

        textarea:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
        }

        button {
            appearance: none;
            border: none;
            background: var(--accent);
            color: white;
            padding: 0.9rem 1.6rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.1s ease, box-shadow 0.2s ease;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        button:disabled {
            background: #94a3b8;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        button:not(:disabled):hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }

        .responses-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
        }

        .model-card {
            background: var(--card-bg);
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }

        .model-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.6);
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .model-checkbox {
            width: 18px;
            height: 18px;
            cursor: pointer;
            flex-shrink: 0;
        }

        .model-name {
            font-weight: 600;
            font-size: 1rem;
            margin: 0;
            flex: 1;
        }

        .model-card.disabled {
            opacity: 0.5;
        }

        .model-card.disabled .model-response {
            color: #999;
        }

        .model-info {
            flex: 1;
            min-width: 0;
        }

        .model-status {
            font-size: 0.85rem;
            margin: 0.5rem 0 0;
            color: #666;
        }

        .model-status.loading {
            color: var(--accent);
        }

        .model-status.success {
            color: #16a34a;
        }

        .model-status.error {
            color: #b91c1c;
        }

        .model-response {
            padding: 1.5rem;
            min-height: 200px;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 0.9rem;
            flex: 1;
            overflow-y: auto;
            max-height: 600px;
        }

        .model-response.loading {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--accent);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        footer {
            text-align: center;
            padding: 2rem;
            font-size: 0.85rem;
            color: #666;
        }

        @media (max-width: 768px) {
            body {
                padding: 1rem;
            }

            .responses-grid {
                grid-template-columns: 1fr;
            }

            .prompt-header {
                flex-direction: column;
                align-items: flex-start;
            }

            .history-container {
                width: 100%;
            }

            select {
                width: 100%;
                min-width: unset;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Multi-Model Comparison</h1>
            <p>Send the same prompt to LLM models simultaneously and compare responses side by side.</p>
        </header>

        <div class="input-section">
            <div class="prompt-header">
                <label for="prompt">Prompt</label>
                <div class="history-container">
                    <span class="history-label">Previous:</span>
                    <select id="history">
                        <option value="">-- Select --</option>
                    </select>
                </div>
            </div>
            <textarea id="prompt" placeholder="Ask a question to LLM models..."></textarea>
            <button id="sendBtn">Send to LLM Models</button>
        </div>

        <div class="responses-grid">
            <div class="model-card" id="card-ollama">
                <div class="model-header">
                    <input type="checkbox" class="model-checkbox" id="checkbox-ollama" checked>
                    <div class="model-info">
                        <h3 class="model-name">DeepSeek R1 (Ollama)</h3>
                        <p class="model-status" id="status-ollama">Ready</p>
                    </div>
                </div>
                <div class="model-response" id="response-ollama">.........</div>
            </div>

            <div class="model-card" id="card-anthropic">
                <div class="model-header">
                    <input type="checkbox" class="model-checkbox" id="checkbox-anthropic">
                    <div class="model-info">
                        <h3 class="model-name">Claude Sonnet 4.5</h3>
                        <p class="model-status" id="status-anthropic">Ready</p>
                    </div>
                </div>
                <div class="model-response" id="response-anthropic">.........</div>
            </div>

            <div class="model-card" id="card-openai">
                <div class="model-header">
                    <input type="checkbox" class="model-checkbox" id="checkbox-openai">
                    <div class="model-info">
                        <h3 class="model-name">GPT-5</h3>
                        <p class="model-status" id="status-openai">Ready</p>
                    </div>
                </div>
                <div class="model-response" id="response-openai">.........</div>
            </div>

            <div class="model-card" id="card-google">
                <div class="model-header">
                    <input type="checkbox" class="model-checkbox" id="checkbox-google" checked>
                    <div class="model-info">
                        <h3 class="model-name">Gemini 2.0 Flash Exp</h3>
                        <p class="model-status" id="status-google">Ready</p>
                    </div>
                </div>
                <div class="model-response" id="response-google">.........</div>
            </div>
        </div>

        <footer>
            Standalone Python server - No external dependencies required. Ollama must run on localhost:11434.
        </footer>
    </div>

    <script>
        const promptInput = document.getElementById('prompt');
        const sendButton = document.getElementById('sendBtn');
        const historySelect = document.getElementById('history');

        const models = [
            { id: 'ollama', name: 'deepseek-r1:latest', type: 'ollama' },
            { id: 'anthropic', name: 'claude-sonnet-4-5-20250929', type: 'anthropic' },
            { id: 'openai', name: 'gpt-5', type: 'openai' },
            { id: 'google', name: 'gemini-2.0-flash-exp', type: 'google' }
        ];

        // Handle checkbox changes
        models.forEach(model => {
            const checkbox = document.getElementById(`checkbox-${model.id}`);
            const card = document.getElementById(`card-${model.id}`);

            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    card.classList.remove('disabled');
                } else {
                    card.classList.add('disabled');
                }
            });
        });

        // Load prompt history on page load
        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                if (response.ok) {
                    const history = await response.json();
                    updateHistoryDropdown(history);
                }
            } catch (error) {
                console.error('Failed to load history:', error);
            }
        }

        function updateHistoryDropdown(history) {
            // Clear existing options except the first one
            historySelect.innerHTML = '<option value="">-- Select --</option>';

            // Add history items in reverse order (newest first)
            history.slice().reverse().forEach((prompt, index) => {
                const option = document.createElement('option');
                const preview = prompt.length > 60
                    ? prompt.substring(0, 60) + '...'
                    : prompt;
                option.value = prompt;
                option.textContent = preview;
                historySelect.appendChild(option);
            });
        }

        // Handle history selection
        historySelect.addEventListener('change', (e) => {
            if (e.target.value) {
                promptInput.value = e.target.value;
                promptInput.focus();
            }
        });

        // Save prompt to history when sending
        async function savePrompt(prompt) {
            try {
                const response = await fetch('/api/save-prompt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                if (response.ok) {
                    const history = await response.json();
                    updateHistoryDropdown(history);
                }
            } catch (error) {
                console.error('Failed to save prompt:', error);
            }
        }

        async function sendToOllama(modelName, prompt) {
            const response = await fetch('http://localhost:11434/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelName, prompt, stream: false })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();
            if (!data || typeof data.response !== 'string') {
                throw new Error('Unexpected response payload from Ollama.');
            }

            return data.response.trim();
        }

        async function sendToAnthropic(modelName, prompt) {
            const response = await fetch('/api/anthropic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: modelName,
                    max_tokens: 4096,
                    messages: [{ role: 'user', content: prompt }]
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Anthropic API error ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();
            if (!data || !data.content || !data.content[0] || !data.content[0].text) {
                throw new Error('Unexpected response from Anthropic API.');
            }

            return data.content[0].text;
        }

        async function sendToOpenAI(modelName, prompt) {
            const response = await fetch('/api/openai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: modelName,
                    messages: [{ role: 'user', content: prompt }]
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`OpenAI API error ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();
            if (!data || !data.choices || !data.choices[0] || !data.choices[0].message) {
                throw new Error('Unexpected response from OpenAI API.');
            }

            return data.choices[0].message.content;
        }

        async function sendToGoogle(modelName, prompt) {
            const response = await fetch('/api/google', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelName, prompt: prompt })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Google API error ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();
            if (!data || !data.candidates || !data.candidates[0] || !data.candidates[0].content || !data.candidates[0].content.parts || !data.candidates[0].content.parts[0]) {
                throw new Error('Unexpected response from Google API.');
            }

            return data.candidates[0].content.parts[0].text;
        }

        async function queryModel(model, prompt) {
            const statusEl = document.getElementById(`status-${model.id}`);
            const responseEl = document.getElementById(`response-${model.id}`);

            const startTime = Date.now();
            statusEl.textContent = 'Loading...';
            statusEl.className = 'model-status loading';
            responseEl.innerHTML = '<div class="spinner"></div> Waiting for response...';
            responseEl.className = 'model-response loading';

            try {
                let responseText;

                switch (model.type) {
                    case 'ollama':
                        responseText = await sendToOllama(model.name, prompt);
                        break;
                    case 'anthropic':
                        responseText = await sendToAnthropic(model.name, prompt);
                        break;
                    case 'openai':
                        responseText = await sendToOpenAI(model.name, prompt);
                        break;
                    case 'google':
                        responseText = await sendToGoogle(model.name, prompt);
                        break;
                    default:
                        throw new Error(`Unknown model type: ${model.type}`);
                }

                const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                statusEl.textContent = `✓ Completed in ${duration}s`;
                statusEl.className = 'model-status success';
                responseEl.textContent = responseText;
                responseEl.className = 'model-response';
            } catch (error) {
                const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                statusEl.textContent = `✗ Failed after ${duration}s`;
                statusEl.className = 'model-status error';
                responseEl.textContent = `Error: ${error.message}`;
                responseEl.className = 'model-response';
                console.error(`${model.id} error:`, error);
            }
        }

        async function sendPromptToAll() {
            const prompt = promptInput.value.trim();

            if (!prompt) {
                alert('Please enter a prompt first.');
                promptInput.focus();
                return;
            }

            // Check if at least one model is enabled
            const enabledModels = models.filter(model =>
                document.getElementById(`checkbox-${model.id}`).checked
            );

            if (enabledModels.length === 0) {
                alert('Please enable at least one model.');
                return;
            }

            sendButton.disabled = true;

            // Save prompt to history
            await savePrompt(prompt);

            // Send to enabled models only in parallel
            await Promise.all(enabledModels.map(model => queryModel(model, prompt)));

            sendButton.disabled = false;
        }

        sendButton.addEventListener('click', sendPromptToAll);
        promptInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                sendPromptToAll();
            }
        });

        // Load history when page loads
        loadHistory();
    </script>
</body>
</html>"""


class ChatHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the chat interface and API proxy."""

    def do_GET(self):
        """Serve the HTML interface or history API."""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        elif self.path == '/api/history':
            # Return prompt history
            history = load_prompt_history()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(history).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle API proxy requests and history save."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())

            # Handle save-prompt endpoint
            if self.path == '/api/save-prompt':
                prompt_text = data.get('prompt', '')
                if prompt_text:
                    history = add_prompt_to_history(prompt_text)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(history).encode())
                else:
                    self.send_error(400, 'Missing prompt')
                return

            # Get event loop and run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if self.path == '/api/anthropic':
                result = loop.run_until_complete(self.proxy_anthropic(data))
            elif self.path == '/api/openai':
                result = loop.run_until_complete(self.proxy_openai(data))
            elif self.path == '/api/google':
                result = loop.run_until_complete(self.proxy_google(data))
            else:
                self.send_error(404)
                return

            loop.close()

            self.send_response(result['status'])
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result['body'].encode())

        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
        except Exception as e:
            self.send_error(500, str(e))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    async def proxy_anthropic(self, data):
        """Proxy request to Anthropic API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'model': data['model'],
                'max_tokens': data.get('max_tokens', 4096),
                'messages': data['messages']
            }

            headers = {
                'Content-Type': 'application/json',
                'x-api-key': API_KEYS['anthropic'],
                'anthropic-version': '2023-06-01'
            }

            async with session.post(
                'https://api.anthropic.com/v1/messages',
                json=payload,
                headers=headers
            ) as response:
                body = await response.text()
                return {'status': response.status, 'body': body}

    async def proxy_openai(self, data):
        """Proxy request to OpenAI API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'model': data['model'],
                'messages': data['messages']
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {API_KEYS['openai']}"
            }

            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=headers
            ) as response:
                body = await response.text()
                return {'status': response.status, 'body': body}

    async def proxy_google(self, data):
        """Proxy request to Google Gemini API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'contents': [{
                    'parts': [{
                        'text': data['prompt']
                    }]
                }]
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{data['model']}:generateContent?key={API_KEYS['google']}"

            headers = {
                'Content-Type': 'application/json'
            }

            async with session.post(url, json=payload, headers=headers) as response:
                body = await response.text()
                return {'status': response.status, 'body': body}

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8080):
    """Start the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ChatHandler)

    print(f"\n{'='*60}")
    print(f"Multi-Model Chat Server Started")
    print(f"{'='*60}")
    print(f"Server running at: http://localhost:{port}")
    print(f"\nOpen your browser and navigate to: http://localhost:{port}")
    print(f"\nAPI Endpoints:")
    print(f"  POST /api/anthropic - Proxy to Anthropic API")
    print(f"  POST /api/openai - Proxy to OpenAI API")
    print(f"  POST /api/google - Proxy to Google Gemini API")
    print(f"\nRequirements:")
    print(f"  - Ollama running on http://localhost:11434")
    print(f"  - API keys configured (environment or defaults)")
    print(f"\nPress Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    # Try to open browser automatically
    try:
        threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    except:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    import sys

    # Allow custom port via command line argument
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)

    try:
        run_server(port)
    except OSError as e:
        if 'address already in use' in str(e).lower():
            print(f"\nError: Port {port} is already in use.")
            print(f"Try running with a different port: python ollama-chat.py <port>")
            sys.exit(1)
        raise
