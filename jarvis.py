#!/usr/bin/env python3
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('.jarvis')
NOTES_FILE = DATA_DIR / 'notes.json'
TODO_FILE = DATA_DIR / 'todo.json'

COMMANDS = [
    'help',
    'hello',
    'time',
    'date',
    'todo add <task>',
    'todo list',
    'todo remove <id>',
    'note add <text>',
    'note list',
    'search <query>',
    'run <shell command>',
    'open <url>',
    'exit',
]


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


def add_todo(task):
    todos = load_json(TODO_FILE)
    todos.append({'id': len(todos) + 1, 'task': task, 'created_at': datetime.now().isoformat()})
    save_json(TODO_FILE, todos)
    print(f'✅ Added todo #{len(todos)}: {task}')


def list_todos():
    todos = load_json(TODO_FILE)
    if not todos:
        print('No todos yet.')
        return
    print('Your todos:')
    for item in todos:
        print(f"{item['id']}. {item['task']}")


def remove_todo(item_id):
    todos = load_json(TODO_FILE)
    remaining = [item for item in todos if item['id'] != item_id]
    if len(remaining) == len(todos):
        print(f'⚠️ Todo #{item_id} not found.')
        return
    for index, item in enumerate(remaining, start=1):
        item['id'] = index
    save_json(TODO_FILE, remaining)
    print(f'✅ Removed todo #{item_id}.')


def add_note(text):
    notes = load_json(NOTES_FILE)
    notes.append({'id': len(notes) + 1, 'text': text, 'created_at': datetime.now().isoformat()})
    save_json(NOTES_FILE, notes)
    print(f'📝 Saved note #{len(notes)}.')


def list_notes():
    notes = load_json(NOTES_FILE)
    if not notes:
        print('No notes yet.')
        return
    print('Your notes:')
    for note in notes:
        print(f"{note['id']}. {note['text']}")


def search_files(query):
    print(f'🔎 Searching for "{query}" in workspace...')
    matches = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for root, _, files in os.walk('.'):
        if root.startswith('./.jarvis') or root.startswith('./.git'):
            continue
        for filename in files:
            path = os.path.join(root, filename)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for num, line in enumerate(f, start=1):
                        if pattern.search(line):
                            matches.append((path, num, line.strip()))
                            if len(matches) >= 20:
                                break
            except OSError:
                continue
        if len(matches) >= 20:
            break
    if not matches:
        print('No matches found.')
        return
    for path, num, line in matches:
        print(f'{path}:{num}: {line}')


def run_shell(command):
    try:
        print(f'▶️ Running: {command}')
        args = shlex.split(command)
        result = subprocess.run(args, capture_output=True, text=True)
        print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
    except FileNotFoundError:
        print('⚠️ Command not found.')
    except Exception as exc:
        print(f'⚠️ Error running command: {exc}')


def open_url(url):
    if not re.match(r'^(https?|ftp)://', url):
        url = 'https://' + url
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', url])
        elif sys.platform.startswith('win'):
            subprocess.run(['start', url], shell=True)
        else:
            subprocess.run(['xdg-open', url])
        print(f'🌐 Opened {url}')
    except Exception as exc:
        print(f'⚠️ Unable to open URL: {exc}')


def show_help():
    print('Jarvis Assistant Commands:')
    for command in COMMANDS:
        print(f'  - {command}')
    print('Type a command or ask for help to get started.')


def greet():
    print('Welcome to Jarvis.')
    print('Type "help" to see what I can do.')
    print('')


def parse_command(line):
    line = line.strip()
    if not line:
        return
    if line.lower() in ('exit', 'quit', 'bye'):
        print('Goodbye. Jarvis is standing by.')
        sys.exit(0)
    if line.lower() == 'help':
        show_help()
        return
    if line.lower() in ('hello', 'hi', 'hey'):
        print('Hello. How can I help you today?')
        return
    if line.lower() == 'time':
        print(datetime.now().strftime('%H:%M:%S'))
        return
    if line.lower() == 'date':
        print(datetime.now().strftime('%Y-%m-%d'))
        return
    if line.lower().startswith('todo add '):
        add_todo(line[9:].strip())
        return
    if line.lower() == 'todo list':
        list_todos()
        return
    if line.lower().startswith('todo remove '):
        try:
            item_id = int(line[12:].strip())
            remove_todo(item_id)
        except ValueError:
            print('⚠️ Use a valid todo id.')
        return
    if line.lower().startswith('note add '):
        add_note(line[9:].strip())
        return
    if line.lower() == 'note list':
        list_notes()
        return
    if line.lower().startswith('search '):
        search_files(line[7:].strip())
        return
    if line.lower().startswith('run '):
        run_shell(line[4:].strip())
        return
    if line.lower().startswith('open '):
        open_url(line[5:].strip())
        return
    print('⚠️ Command not recognized. Type "help" for available actions.')


def main():
    ensure_data_dir()
    greet()
    try:
        while True:
            line = input('Jarvis> ')
            parse_command(line)
    except (EOFError, KeyboardInterrupt):
        print('\nGoodbye. Jarvis is standing by.')


if __name__ == '__main__':
    main()
