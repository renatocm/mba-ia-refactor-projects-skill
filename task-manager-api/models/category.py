from database import db
from utils.time import utc_now
class Category(db.Model):
    __tablename__="categories"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100),nullable=False,unique=True)
    description=db.Column(db.Text)
    color=db.Column(db.String(7),default="#000000",nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=utc_now)
    tasks=db.relationship("Task",back_populates="category",passive_deletes=True)
    def to_dict(self): return {"id":self.id,"name":self.name,"description":self.description,"color":self.color,"created_at":self.created_at.isoformat() if self.created_at else None}
