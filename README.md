# Blogging Website (Flask)

A simple blogging site built with Flask + SQLite, featuring authentication and CRUD for posts.

## Features
- User registration, login, logout
- Create, edit, delete posts (auth required)
- List posts with author and timestamps
- SQLite database with CLI init command
- Jinja templates and basic CSS

## Requirements
- Python 3.10+
- pip

## Setup

### Option A: Virtualenv (recommended)
If your Python doesn't include venv, install it (Debian/Ubuntu):
```bash
sudo apt update && sudo apt install -y python3-venv
```
Then:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Option B: User install (no venv)
```bash
python3 -m pip install --user -r requirements.txt
```

## Initialize the database
```bash
python3 -m flask --app app init-db
```

## Run the app
```bash
python3 -m flask --app app run --debug
```
The app will be available at `http://127.0.0.1:5000/`.

## Project Structure
```
blog/
  __init__.py        # app factory
  auth.py            # auth blueprint
  blog.py            # blog blueprint (posts)
  db.py              # SQLite connection + init CLI
  templates/         # Jinja templates
  static/            # CSS
app.py                # entrypoint (create_app)
requirements.txt
README.md
```

## Notes
- Default secret key is for dev only; set `FLASK_SECRET_KEY` in production.
- Instance directory and SQLite file are created automatically in `instance/blog.sqlite`.