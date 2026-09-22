import os
import smtplib
from email.message import EmailMessage
class NotificationService:
    def __init__(self):
        self.host=os.getenv("SMTP_HOST");self.port=int(os.getenv("SMTP_PORT","587"));self.user=os.getenv("SMTP_USER");self.password=os.getenv("SMTP_PASSWORD")
    def send_email(self,to,subject,body):
        if not all((self.host,self.user,self.password)): raise RuntimeError("SMTP não configurado")
        msg=EmailMessage();msg["From"]=self.user;msg["To"]=to;msg["Subject"]=subject;msg.set_content(body)
        with smtplib.SMTP(self.host,self.port) as server: server.starttls();server.login(self.user,self.password);server.send_message(msg)
