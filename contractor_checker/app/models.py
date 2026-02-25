from app import db
from datetime import datetime

# Модель User больше не нужна - удаляем

class Contractor(db.Model):
    __tablename__ = 'contractors'
    
    id = db.Column(db.Integer, primary_key=True)
    inn = db.Column(db.String(12), unique=True, nullable=False)
    name = db.Column(db.String(200))
    status = db.Column(db.String(50))  # active, liquidating, inactive
    registration_date = db.Column(db.Date)
    liquidation_date = db.Column(db.Date)
    last_check_date = db.Column(db.DateTime, default=datetime.utcnow)
    check_result = db.Column(db.JSON)  # полные результаты проверки
    
    def __repr__(self):
        return f'<Contractor {self.inn}>'

class CheckHistory(db.Model):
    __tablename__ = 'check_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))
    inn_list = db.Column(db.Text)  # список ИНН через запятую
    check_date = db.Column(db.DateTime, default=datetime.utcnow)
    report_file = db.Column(db.String(200))  # путь к файлу отчета
    email_sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<CheckHistory {self.id} - {self.check_date}>'
