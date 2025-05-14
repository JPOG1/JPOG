from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_migrate import Migrate  # ✅ Add this

from myapp.config import Config
from myapp.database import db

socket = SocketIO()
cors = CORS()
migrate = Migrate()  # ✅ Create migrate instance


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socket.init_app(app, cors_allowed_origins="*")
    cors.init_app(app)
    migrate.init_app(app, db)  # ✅ Register Flask-Migrate

    with app.app_context():
        db.create_all()

        from .views import views
        app.register_blueprint(views)

    return app
