# Jim

## Jarvis Assistant

A lightweight local Jarvis-style CLI assistant is available in `jarvis.py`.

## Jarvis Web App

A browser-accessible Jarvis app is available in `jarvis_web.py`. Use it from other devices on the same network.

### Run the web app

```bash
python3 jarvis_web.py
```

Then open `http://<your-computer-ip>:8080/` from another device.

### Features

- Add and delete todos
- Add notes
- Search your workspace files
- Voice commands and spoken responses
- Mobile-friendly browser interface

### Voice support

On supported browsers, tap "Start Listening" and speak commands such as:

- "todo add buy milk"
- "todo list"
- "note add call Alice"
- "note list"
- "search login"
- "time"
- "date"

### Notes

- Data is stored in `.jarvis/` and is ignored by git.
- The web app listens on `0.0.0.0:8080` so other devices on your local network can connect.

## Jarvis Assistant

A lightweight Jarvis-style CLI assistant that runs in the workspace.

### Usage

1. Run the assistant:
   ```bash
   python3 jarvis.py
   ```
2. Use commands such as:
   - `help`
   - `hello`
   - `time`
   - `date`
   - `todo add <task>`
   - `todo list`
   - `todo remove <id>`
   - `note add <text>`
   - `note list`
   - `search <query>`
   - `run <shell command>`
   - `open <url>`
   - `exit`

### Notes

- Data is stored in `.jarvis/` and is ignored by git.
- This assistant is designed for local command and note management.
