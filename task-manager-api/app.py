from flask import Flask
from flask_cors import CORS
from config import Config
from database import db
from errors import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from datetime import timezone

def create_app(config_class=Config):
    app=Flask(__name__);app.config.from_object(config_class);CORS(app);db.init_app(app)
    app.register_blueprint(task_bp);app.register_blueprint(user_bp);app.register_blueprint(report_bp);register_error_handlers(app)
    @app.get("/health")
    def health(): return {"status":"ok"}
    @app.get("/")
    def index(): return {"message":"Task Manager API","version":"1.0"}
    return app
app=create_app()
if __name__=="__main__":
    with app.app_context(): db.create_all()
    app.run(debug=app.config.get("DEBUG",False),host="0.0.0.0",port=5000)
