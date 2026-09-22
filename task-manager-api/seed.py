from app import app
from database import db
from models.user import User
from models.category import Category
from models.task import Task
from utils.time import utc_now

def seed_data(reset=False):
    with app.app_context():
        if reset:
            Task.query.delete();User.query.delete();Category.query.delete();db.session.commit()
        if not User.query.filter_by(email="admin@example.com").first():
            u=User(name="Admin",email="admin@example.com",role="admin");u.set_password(__import__("os").getenv("SEED_ADMIN_PASSWORD", "change-me-123"));db.session.add(u);db.session.commit()

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--reset",action="store_true");seed_data(parser.parse_args().reset)
