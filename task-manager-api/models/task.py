from database import db
from utils.time import utc_now,is_overdue
class Task(db.Model):
    __tablename__="tasks"
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(200),nullable=False)
    description=db.Column(db.Text)
    status=db.Column(db.String(20),default="pending",nullable=False)
    priority=db.Column(db.Integer,default=3,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id",ondelete="SET NULL"),nullable=True)
    category_id=db.Column(db.Integer,db.ForeignKey("categories.id",ondelete="SET NULL"),nullable=True)
    created_at=db.Column(db.DateTime(timezone=True),default=utc_now)
    updated_at=db.Column(db.DateTime(timezone=True),default=utc_now,onupdate=utc_now)
    due_date=db.Column(db.DateTime(timezone=True))
    tags=db.Column(db.String(500))
    user=db.relationship("User",backref=db.backref("tasks",passive_deletes=True))
    category=db.relationship("Category",back_populates="tasks")
    def to_dict(self): return {"id":self.id,"title":self.title,"description":self.description,"status":self.status,"priority":self.priority,"user_id":self.user_id,"category_id":self.category_id,"created_at":self.created_at.isoformat() if self.created_at else None,"updated_at":self.updated_at.isoformat() if self.updated_at else None,"due_date":self.due_date.isoformat() if self.due_date else None,"tags":self.tags.split(",") if self.tags else [],"overdue":is_overdue(self.due_date,self.status)}
