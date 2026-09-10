import os

from app import create_app
from app.extensions import socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "4554")),
        debug=app.config.get("DEBUG", False),
    )
