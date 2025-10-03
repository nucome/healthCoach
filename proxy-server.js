const http = require('http');
const https = require('https');
const url = require('url');

const API_KEYS = {
    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'openai': os.getenv('OPENAI_API_KEY'),
    'google': os.getenv('GOOGLE_API_KEY')
};

const server = http.createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    if (req.method !== 'POST') {
        res.writeHead(405, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Method not allowed' }));
        return;
    }

    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    let body = '';
    req.on('data', chunk => {
        body += chunk.toString();
    });

    req.on('end', () => {
        try {
            const data = JSON.parse(body);

            if (pathname === '/anthropic') {
                proxyToAnthropic(data, res);
            } else if (pathname === '/openai') {
                proxyToOpenAI(data, res);
            } else if (pathname === '/google') {
                proxyToGoogle(data, res);
            } else {
                res.writeHead(404, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: 'Not found' }));
            }
        } catch (error) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Invalid JSON' }));
        }
    });
});

function proxyToAnthropic(data, res) {
    const postData = JSON.stringify({
        model: data.model,
        max_tokens: data.max_tokens || 4096,
        messages: data.messages
    });

    const options = {
        hostname: 'api.anthropic.com',
        port: 443,
        path: '/v1/messages',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': API_KEYS.anthropic,
            'anthropic-version': '2023-06-01',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const proxyReq = https.request(options, (proxyRes) => {
        let responseBody = '';

        proxyRes.on('data', (chunk) => {
            responseBody += chunk;
        });

        proxyRes.on('end', () => {
            res.writeHead(proxyRes.statusCode, { 'Content-Type': 'application/json' });
            res.end(responseBody);
        });
    });

    proxyReq.on('error', (error) => {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
    });

    proxyReq.write(postData);
    proxyReq.end();
}

function proxyToOpenAI(data, res) {
    const postData = JSON.stringify({
        model: data.model,
        messages: data.messages
    });

    const options = {
        hostname: 'api.openai.com',
        port: 443,
        path: '/v1/chat/completions',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${API_KEYS.openai}`,
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const proxyReq = https.request(options, (proxyRes) => {
        let responseBody = '';

        proxyRes.on('data', (chunk) => {
            responseBody += chunk;
        });

        proxyRes.on('end', () => {
            res.writeHead(proxyRes.statusCode, { 'Content-Type': 'application/json' });
            res.end(responseBody);
        });
    });

    proxyReq.on('error', (error) => {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
    });

    proxyReq.write(postData);
    proxyReq.end();
}

function proxyToGoogle(data, res) {
    const postData = JSON.stringify({
        contents: [{
            parts: [{
                text: data.prompt
            }]
        }]
    });

    const options = {
        hostname: 'generativelanguage.googleapis.com',
        port: 443,
        path: `/v1beta/models/${data.model}:generateContent?key=${API_KEYS.google}`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const proxyReq = https.request(options, (proxyRes) => {
        let responseBody = '';

        proxyRes.on('data', (chunk) => {
            responseBody += chunk;
        });

        proxyRes.on('end', () => {
            res.writeHead(proxyRes.statusCode, { 'Content-Type': 'application/json' });
            res.end(responseBody);
        });
    });

    proxyReq.on('error', (error) => {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
    });

    proxyReq.write(postData);
    proxyReq.end();
}

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`Proxy server running on http://localhost:${PORT}`);
    console.log('Endpoints:');
    console.log('  POST /anthropic - Proxy to Anthropic API');
    console.log('  POST /openai - Proxy to OpenAI API');
    console.log('  POST /google - Proxy to Google Gemini API');
});
