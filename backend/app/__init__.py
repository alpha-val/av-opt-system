from flask import Flask, send_from_directory
from flask_mail import Mail
from .extensions import mongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

mail = Mail()

def create_app():

    react_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "./build"))
    app = Flask(__name__, static_folder=react_build_dir, static_url_path="")
    print("Serving static site from: ", react_build_dir)
    
    # # ── Mail settings ─────────────────────────────────────────────────────
    # app.config.update(
    #     MAIL_SERVER      = "smtp.gmail.com",
    #     MAIL_PORT        = 587,
    #     MAIL_USE_TLS     = True,
    #     MAIL_USE_SSL     = False,
    #     MAIL_USERNAME    = os.getenv("GMAIL_USERNAME"),    # e.g. from env var
    #     MAIL_PASSWORD    = os.getenv("GMAIL_PASSWORD"),    # e.g. from env var
    #     MAIL_DEFAULT_SENDER = ("Sport Squad", "noreply@sport-squad.render.com")
    # )
    # mail.init_app(app)

    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["DB_NAME"] = os.getenv("DB_NAME", "Sport-Squad")

    app.secret_key = os.getenv("SECRET_KEY")

    # Setup MongoDB connection
    # mongo.init_app(app)

    # from .athlete.routes import athlete_bp
    # from .auth.routes import auth_bp
    # from .coach.routes import coach_bp
    # from .goal.routes import goals_bp
    # from .events.routes import event_bp
    # from .message.invites import invite_bp
    # from .media.routes import media_bp
    # from .message.routes import message_bp
    # from .message.invites import invite_bp
    # from .organization.routes import org_bp
    # from .parent.routes import parent_bp

    # app.register_blueprint(athlete_bp, url_prefix="/api/v1/athlete")
    # app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    # app.register_blueprint(coach_bp, url_prefix="/api/v1/coach")
    # app.register_blueprint(goals_bp, url_prefix="/api/v1/docs")
    # app.register_blueprint(event_bp, url_prefix="/api/v1/event")
    # app.register_blueprint(media_bp, url_prefix="/api/v1/media")
    # app.register_blueprint(message_bp, url_prefix="/api/v1/message")
    # app.register_blueprint(invite_bp, url_prefix="/api/v1/invite")
    # app.register_blueprint(org_bp, url_prefix="/api/v1/org")
    # app.register_blueprint(parent_bp, url_prefix="/api/v1/parent")


    @app.errorhandler(404)
    def not_found(e):
        static_dir = app.static_folder
        return send_from_directory(static_dir, "index.html") 

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_react(path):

        if path.startswith("api"):
            return "Page not Found!", 404

        static_dir = app.static_folder
        target_path = os.path.join(static_dir, path)


        print(f"* * * * * * * * file_path: {target_path}, exists: {os.path.isfile(target_path)}")
        if os.path.isfile(target_path):
            return send_from_directory(static_dir, path)
        else:
            # Always fall back to index.html for client-side routes like /parent
            return send_from_directory(static_dir, "index.html")        

    return app
