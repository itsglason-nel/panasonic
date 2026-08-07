"""
PMPC Data Logger — WSGI Entry Point
Usage: gunicorn --worker-class eventlet -b 0.0.0.0:8080 wsgi:app
"""
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(
        app,
        host=app.config.get('SERVER_HOST', '0.0.0.0'),
        port=app.config.get('SERVER_PORT', 8080),
        debug=app.config.get('DEBUG', False),
    )
