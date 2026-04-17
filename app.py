from flask import Flask, render_template_string, request, jsonify
import requests
import base64
import json
import os

app = Flask(**name**)
app.secret_key = os.environ.get(‘SECRET_KEY’, ‘screener-labs-2026’)

ANTHROPIC_API_KEY = os.environ.get(‘ANTHROPIC_API_KEY’, ‘’)
GITHUB_TOKEN = os.environ.get(‘GITHUB_TOKEN’, ‘’)
GITHUB_REPO = os.environ.get(‘GITHUB_REPO’, ‘privatefitout-design/crypto-scanner’)

@app.route(’/’)
def index():
with open(os.path.join(os.path.dirname(**file**), ‘index.html’)) as f:
return f.read()

@app.route(’/api/debug’, methods=[‘POST’])
def debug_symbol():
“”“Debug a symbol using Managed Agents API with full internet access”””
data = request.json
symbol = data.get(‘symbol’, ‘BTCUSDT’).upper()

```
# Read scanner code
scanner_code = ""
try:
    with open(os.path.join(os.path.dirname(__file__), 'scanner1_accumulation.py')) as f:
        scanner_code = f.read()
except:
    pass

# Use Anthropic API with tools to access Binance directly
response = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    },
    json={
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 2000,
        'tools': [
            {
                'type': 'web_fetch_20260209',
                'name': 'web_fetch'
            }
        ],
        'system': f"""You are a crypto scanner debug agent. 
```

Use web_fetch to get real data from Binance Futures API and analyze the symbol.
Scanner logic reference:
{scanner_code[:4000]}

For DEBUG analysis:

1. Fetch daily klines: https://fapi.binance.com/fapi/v1/klines?symbol=SYMBOL&interval=1d&limit=200
1. Fetch 1h klines: https://fapi.binance.com/fapi/v1/klines?symbol=SYMBOL&interval=1h&limit=30
1. Fetch OI history: https://fapi.binance.com/fapi/v1/openInterestHist?symbol=SYMBOL&period=1h&limit=24
   Then analyze using the scanner logic and report each filter result.”””,
   ‘messages’: [
   {‘role’: ‘user’, ‘content’: f’DEBUG {symbol} - fetch real Binance data and run full scanner analysis. Report each filter: EMA compression, slope, amplitude, NATR, OI angle, OI growth, antispike. Show final score and tier.’}
   ]
   },
   timeout=60
   )
   
   if response.status_code != 200:
   return jsonify({‘error’: response.text}), 500
   
   result = response.json()
   text = ‘’
   for block in result.get(‘content’, []):
   if block.get(‘type’) == ‘text’:
   text += block[‘text’]
   
   return jsonify({‘response’: text, ‘symbol’: symbol})

@app.route(’/api/chat’, methods=[‘POST’])
def chat():
data = request.json
messages = data.get(‘messages’, [])

```
system_prompt = """You are ScreenerLabs agent for Said Hodjaev.
```

You manage crypto-scanner on Railway/GitHub.
Tools: github_get_file, github_update_file, github_list_files.
Respond in Russian. Be concise.”””

```
response = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    },
    json={
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 2000,
        'system': system_prompt,
        'tools': [
            {
                'name': 'github_get_file',
                'description': 'Get file from GitHub',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string'}
                    },
                    'required': ['path']
                }
            },
            {
                'name': 'github_update_file',
                'description': 'Update file in GitHub',
                'input_schema': {
                    'type': 'object',
                    'properties': {
                        'path': {'type': 'string'},
                        'content': {'type': 'string'},
                        'message': {'type': 'string'}
                    },
                    'required': ['path', 'content', 'message']
                }
            },
            {
                'name': 'github_list_files',
                'description': 'List files in GitHub repo',
                'input_schema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
        ],
        'messages': messages
    }
)

if response.status_code != 200:
    return jsonify({'error': response.text}), 500

result = response.json()

# Process tool calls
tool_results = []
for block in result.get('content', []):
    if block.get('type') == 'tool_use':
        tool_result = execute_tool(block['name'], block.get('input', {}))
        tool_results.append({
            'type': 'tool_result',
            'tool_use_id': block['id'],
            'content': json.dumps(tool_result)
        })

if tool_results:
    messages_with_tools = messages + [
        {'role': 'assistant', 'content': result['content']},
        {'role': 'user', 'content': tool_results}
    ]
    follow_up = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 2000,
            'system': system_prompt,
            'messages': messages_with_tools
        }
    )
    if follow_up.status_code == 200:
        result = follow_up.json()

text = ''
for block in result.get('content', []):
    if block.get('type') == 'text':
        text += block['text']

return jsonify({
    'response': text,
    'tool_calls': [b for b in result.get('content', []) if b.get('type') == 'tool_use']
})
```

def execute_tool(name, input_data):
headers = {
‘Authorization’: f’token {GITHUB_TOKEN}’,
‘Accept’: ‘application/vnd.github.v3+json’
}

```
if name == 'github_get_file':
    path = input_data.get('path', '')
    r = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}', headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return {'success': True, 'content': content, 'sha': r.json()['sha']}
    return {'success': False, 'error': r.text}

elif name == 'github_update_file':
    path = input_data.get('path', '')
    content = input_data.get('content', '')
    message = input_data.get('message', 'Update via ScreenerLabs')
    r = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}', headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    payload = {'message': message, 'content': base64.b64encode(content.encode()).decode()}
    if sha:
        payload['sha'] = sha
    r = requests.put(f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}', headers=headers, json=payload)
    if r.status_code in [200, 201]:
        return {'success': True, 'message': f'{path} updated. Railway auto-deploys.'}
    return {'success': False, 'error': r.text}

elif name == 'github_list_files':
    r = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/contents/', headers=headers)
    if r.status_code == 200:
        return {'success': True, 'files': [f['name'] for f in r.json()]}
    return {'success': False, 'error': r.text}

return {'success': False, 'error': 'Unknown tool'}
```

if **name** == ‘**main**’:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port)
