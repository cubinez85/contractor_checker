import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.server = current_app.config['MAIL_SERVER']
        self.port = current_app.config['MAIL_PORT']
        self.sender = current_app.config['MAIL_DEFAULT_SENDER']
        
    def send_report(self, recipient, report_path):
        """
        Отправка отчета на email
        """
        try:
            # Создание сообщения
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient
            msg['Subject'] = 'Отчет проверки контрагентов'
            
            # Текст письма
            body = """
            Здравствуйте!
            
            Во вложении находится отчет по проверке контрагентов через ФНС.
            
            С уважением,
            Сервис проверки контрагентов
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Вложение - файл отчета
            with open(report_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), Name=os.path.basename(report_path))
                attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_path)}"'
                msg.attach(attachment)
            
            # Отправка
            with smtplib.SMTP(self.server, self.port) as server:
                server.send_message(msg)
            
            logger.info(f"Отчет отправлен на {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки email: {str(e)}")
            raise
