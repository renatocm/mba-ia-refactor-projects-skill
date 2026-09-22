from database import db
from models.user import User
from utils.validation import validate_user
def get(user_id): return db.session.get(User,user_id)
def create(data):
    validate_user(data)
    if User.query.filter_by(email=data["email"]).first(): raise KeyError("Email já cadastrado")
    user=User(name=data["name"].strip(),email=data["email"].lower(),role=data.get("role","user")); user.set_password(data["password"]); db.session.add(user); db.session.commit(); return user
def update(user,data):
    validate_user(data,True)
    for key in ("name","email","role","active"):
        if key in data: setattr(user,key,data[key])
    if "password" in data: user.set_password(data["password"])
    db.session.commit(); return user
