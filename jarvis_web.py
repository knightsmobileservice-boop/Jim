#!/usr/bin/env python3
import json
import os
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA_DIR = Path('.jarvis')
NOTES_FILE = DATA_DIR / 'notes.json'
TODO_FILE = DATA_DIR / 'todo.json'

PORT = int(os.environ.get('JARVIS_PORT', '8080'))


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)
    for path in (NOTES_FILE, TODO_FILE):
        if not path.exists():
            path.write_text('[]', encoding='utf-8')


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def search_workspace(query):
    results = []
    for root, _, files in os.walk('.'):
        if root.startswith('./.jarvis') or root.startswith('./.git'):
            continue
        for filename in files:
            path = os.path.join(root, filename)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for num, line in enumerate(f, start=1):
                        if query.lower() in line.lower():
                            results.append({'file': path, 'line': num, 'text': line.strip()})
                            if len(results) >= 50:
                                break
            except OSError:
                continue
        if len(results) >= 50:
            break
    return results


def handle_command(command):
    text = command.strip()
    lower = text.lower()
    if not text:
        return {'message': 'I did not hear anything. Try saying a command.'}
    if lower in ('hello', 'hi', 'hey'):
        return {'message': 'Hello. I am Jarvis. Tell me what you want me to do.'}
    if lower == 'time':
        return {'message': datetime.now().strftime('%H:%M:%S')}
    if lower == 'date':
        return {'message': datetime.now().strftime('%Y-%m-%d')}
    if lower.startswith('todo add '):
        task = text[9:].strip()
        if not task:
            return {'message': 'Please tell me the todo task to add.'}
        todos = load_json(TODO_FILE)
        new_item = {'id': len(todos) + 1, 'task': task}
        todos.append(new_item)
        save_json(TODO_FILE, todos)
        return {'message': f'Todo added: {task}', 'todos': todos}
    if lower == 'todo list':
        todos = load_json(TODO_FILE)
        if not todos:
            return {'message': 'Your todo list is empty.', 'todos': []}
        return {'message': f'You have {len(todos)} todos.', 'todos': todos}
    if lower.startswith('todo remove '):
        try:
            item_id = int(lower[12:].strip())
        except ValueError:
            return {'message': 'Please say a valid todo number to remove.'}
        todos = load_json(TODO_FILE)
        remaining = [item for item in todos if item['id'] != item_id]
        if len(remaining) == len(todos):
            return {'message': f'Todo {item_id} was not found.'}
        for index, item in enumerate(remaining, start=1):
            item['id'] = index
        save_json(TODO_FILE, remaining)
        return {'message': f'Todo {item_id} removed.', 'todos': remaining}
    if lower.startswith('note add '):
        note_text = text[9:].strip()
        if not note_text:
            return {'message': 'Please say the note text to save.'}
        notes = load_json(NOTES_FILE)
        new_note = {'id': len(notes) + 1, 'text': note_text}
        notes.append(new_note)
        save_json(NOTES_FILE, notes)
        return {'message': 'Note saved.', 'notes': notes}
    if lower == 'note list':
        notes = load_json(NOTES_FILE)
        if not notes:
            return {'message': 'Your note list is empty.', 'notes': []}
        return {'message': f'You have {len(notes)} notes.', 'notes': notes}
    if lower.startswith('search '):
        query = text[7:].strip()
        if not query:
            return {'message': 'Please say what you want me to search for.'}
        results = search_workspace(query)
        return {'message': f'Found {len(results)} matches for "{query}".', 'results': results}
    return {'message': 'I did not understand that command. Try: todo add, note add, search, time, date.'}


def json_response(handler, data, status=HTTPStatus.OK):
    payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def read_request_body(handler):
    length = int(handler.headers.get('Content-Length', 0))
    body = handler.rfile.read(length).decode('utf-8') if length else ''
    if body:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return None


def apply_cors(handler):
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type')


class JarvisHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        apply_cors(self)
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.path = '/static/index.html'
            return super().do_GET()
        if parsed.path == '/api/status':
            json_response(self, {'status': 'ok', 'message': 'Jarvis web app is running'})
            return
        if parsed.path == '/api/todos':
            json_response(self, load_json(TODO_FILE))
            return
        if parsed.path == '/api/notes':
            json_response(self, load_json(NOTES_FILE))
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        payload = read_request_body(self)
        if parsed.path == '/api/todos':
            if not payload or 'task' not in payload:
                json_response(self, {'error': 'Missing task field'}, HTTPStatus.BAD_REQUEST)
                return
            todos = load_json(TODO_FILE)
            new_item = {'id': len(todos) + 1, 'task': payload['task']}
            todos.append(new_item)
            save_json(TODO_FILE, todos)
            json_response(self, new_item, HTTPStatus.CREATED)
            return
        if parsed.path == '/api/notes':
            if not payload or 'text' not in payload:
                json_response(self, {'error': 'Missing text field'}, HTTPStatus.BAD_REQUEST)
                return
            notes = load_json(NOTES_FILE)
            new_note = {'id': len(notes) + 1, 'text': payload['text']}
            notes.append(new_note)
            save_json(NOTES_FILE, notes)
            json_response(self, new_note, HTTPStatus.CREATED)
            return
        if parsed.path == '/api/search':
            query = payload.get('query') if payload else ''
            if not query:
                json_response(self, {'error': 'Missing query field'}, HTTPStatus.BAD_REQUEST)
                return
            results = search_workspace(query)
            json_response(self, {'query': query, 'results': results})
            return
        if parsed.path == '/api/command':
            command = payload.get('command') if payload else ''
            if not command:
                json_response(self, {'error': 'Missing command field'}, HTTPStatus.BAD_REQUEST)
                return
            result = handle_command(command)
            json_response(self, result)
            return
        json_response(self, {'error': 'Not found'}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/todos/'):
            try:
                todo_id = int(parsed.path.split('/')[-1])
            except ValueError:
                json_response(self, {'error': 'Invalid todo id'}, HTTPStatus.BAD_REQUEST)
                return
            todos = load_json(TODO_FILE)
            remaining = [item for item in todos if item['id'] != todo_id]
            if len(remaining) == len(todos):
                json_response(self, {'error': 'Todo not found'}, HTTPStatus.NOT_FOUND)
                return
            for index, item in enumerate(remaining, start=1):
                item['id'] = index
            save_json(TODO_FILE, remaining)
            json_response(self, {'deleted': todo_id})
            return
        json_response(self, {'error': 'Not found'}, HTTPStatus.NOT_FOUND)


def run_server():
    ensure_data_dir()
    server_address = ('0.0.0.0', PORT)
    with ThreadingHTTPServer(server_address, JarvisHandler) as httpd:
        print(f'Jarvis web app running on http://0.0.0.0:{PORT}')
        print('Open this address from another device on the same network.')
        httpd.serve_forever()


if __name__ == '__main__':
    run_server()
