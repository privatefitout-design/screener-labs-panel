from flask import Flask, render_template_string, request, jsonify, session
import requests
import base64
import json
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'screener-labs-2026')

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'privatefitout-design/crypto-scanner')
RAILWAY_TOKEN = os.environ.get('RAILWAY_TOKEN', '')

@app.route('/')
def index():
    with open(os.path.join(os.path.dirname(__file__), 'index.html')) as f:
        return f.read()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    messages = data.get('messages', [])
    
    system_prompt = """You are an autonomous agent for ScreenerLabs crypto scanner project.
You have tools to manage GitHub and Railway. The owner is Said Hodjaev — Dubai entrepreneur.

Project: crypto scanner on Railway (EU region), GitHub repo: privatefitout-design/crypto-scanner
Scanner 1 (LONG) is live. Scanner 2 (SHORT) waiting for Coinglass API.

When Said gives you a task:
1. Analyze what needs to be done
2. Use the appropriate tool (github_get_file, github_update_file, github_create_file, railway_status)
3. Report back concisely what you did

Always respond in Russian. Be concise. Code must be immediately working.

Available tools:
- github_get_file: get file content from repo
- github_update_file: update/create file in repo  
- railway_status: check Railway deployment status
- github_list_files: list repo files

When updating scanner code, always preserve existing logic unless explicitly told to change it."""

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 2000,
            'system': system_prompt,
            'tools': [
                {
                    'name': 'github_get_file',
                    'description': 'Get file content from GitHub repository',
                    'input_schema': {
                        'type': 'object',
                        'properties': {
                            'repo': {'type': 'string', 'description': 'repo owner/name'},
                            'path': {'type': 'string', 'description': 'file path'}
                        },
                        'required': ['repo', 'path']
                    }
                },
                {
                    'name': 'github_update_file',
                    'description': 'Create or update a file in GitHub repository',
                    'input_schema': {
                        'type': 'object',
                        'properties': {
                            'repo': {'type': 'string'},
                            'path': {'type': 'string'},
                            'content': {'type': 'string', 'description': 'file content'},
                            'message': {'type': 'string', 'description': 'commit message'}
                        },
                        'required': ['repo', 'path', 'content', 'message']
                    }
                },
                {
                    'name': 'github_list_files',
                    'description': 'List files in GitHub repository',
                    'input_schema': {
                        'type': 'object',
                        'properties': {
                            'repo': {'type': 'string'},
                            'path': {'type': 'string', 'description': 'directory path, default root'}
                        },
                        'required': ['repo']
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
            tool_result = execute_tool(block['name'], block['input'])
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': block['id'],
                'content': json.dumps(tool_result)
            })
    
    # If there were tool calls, continue the conversation
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
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 2000,
                'system': system_prompt,
                'tools': result.get('content', []),
                'messages': messages_with_tools
            }
        )
        if follow_up.status_code == 200:
            result = follow_up.json()
    
    text_response = ''
    for block in result.get('content', []):
        if block.get('type') == 'text':
            text_response += block['text']
    
    return jsonify({
        'response': text_response,
        'tool_calls': [b for b in result.get('content', []) if b.get('type') == 'tool_use'],
        'stop_reason': result.get('stop_reason')
    })


def execute_tool(name, input_data):
    token = GITHUB_TOKEN
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    if name == 'github_get_file':
        repo = input_data.get('repo', GITHUB_REPO)
        path = input_data['path']
        r = requests.get(f'https://api.github.com/repos/{repo}/contents/{path}', headers=headers)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return {'success': True, 'content': content, 'sha': data['sha']}
        return {'success': False, 'error': r.text}
    
    elif name == 'github_update_file':
        repo = input_data.get('repo', GITHUB_REPO)
        path = input_data['path']
        content = input_data['content']
        message = input_data.get('message', 'Update via ScreenerLabs agent')
        
        # Check if file exists to get sha
        r = requests.get(f'https://api.github.com/repos/{repo}/contents/{path}', headers=headers)
        sha = r.json().get('sha') if r.status_code == 200 else None
        
        payload = {
            'message': message,
            'content': base64.b64encode(content.encode()).decode()
        }
        if sha:
            payload['sha'] = sha
        
        r = requests.put(
            f'https://api.github.com/repos/{repo}/contents/{path}',
            headers=headers,
            json=payload
        )
        if r.status_code in [200, 201]:
            return {'success': True, 'message': f'File {path} updated. Railway will auto-deploy.'}
        return {'success': False, 'error': r.text}
    
    elif name == 'github_list_files':
        repo = input_data.get('repo', GITHUB_REPO)
        path = input_data.get('path', '')
        url = f'https://api.github.com/repos/{repo}/contents/{path}'
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            files = [{'name': f['name'], 'type': f['type'], 'path': f['path']} for f in r.json()]
            return {'success': True, 'files': files}
        return {'success': False, 'error': r.text}
    
    return {'success': False, 'error': f'Unknown tool: {name}'}


@app.route('/api/github/files', methods=['GET'])
def get_files():
    repo = request.args.get('repo', GITHUB_REPO)
    token = GITHUB_TOKEN
    r = requests.get(
        f'https://api.github.com/repos/{repo}/contents/',
        headers={'Authorization': f'token {token}'}
    )
    if r.status_code == 200:
        return jsonify(r.json())
    return jsonify({'error': r.text}), 400


@app.route('/api/railway/status', methods=['GET'])
def railway_status():
    # Railway GraphQL API
    r = requests.post(
        'https://backboard.railway.app/graphql/v2',
        headers={
            'Authorization': f'Bearer {RAILWAY_TOKEN}',
            'Content-Type': 'application/json'
        },
        json={'query': '{ me { projects { edges { node { name deployments { edges { node { status createdAt } } } } } } } }'}
    )
    if r.status_code == 200:
        return jsonify(r.json())
    return jsonify({'error': 'Railway API unavailable'}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
