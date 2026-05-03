from flask import render_template, request, flash, redirect, url_for, send_from_directory, abort, current_app
from app.main import bp
from app.services.fns_checker import FNSChecker
from app.services.report_generator import ReportGenerator
from app.services.email_sender import EmailSender
from app.models import CheckHistory
from app import db
import os

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        inn_list = request.form.get('inn_list', '')
        email = request.form.get('email', '')
        
        if not inn_list or not email:
            flash('Заполните все поля', 'danger')
            return redirect(url_for('main.index'))
        
        # Разбираем ИНН
        inns = [inn.strip() for inn in inn_list.replace('\n', ',').split(',') if inn.strip()]
        
        if len(inns) > 100:
            flash('Максимум 100 ИНН за раз', 'danger')
            return redirect(url_for('main.index'))
        
        try:
            # Проверка через ФНС
            checker = FNSChecker()
            results = checker.check_batch(inns)
            
            # Генерация отчета
            generator = ReportGenerator()
            report_path = generator.generate_excel(results, email)
            
            # Отправка на почту
            sender = EmailSender()
            sender.send_report(email, report_path)
            
            # Сохранение в историю
            history = CheckHistory(
                user_email=email,
                inn_list=','.join(inns),
                report_file=report_path,
                email_sent=True
            )
            db.session.add(history)
            db.session.commit()
            
            flash('Проверка завершена. Отчет отправлен на почту', 'success')
            
        except Exception as e:
            flash(f'Ошибка при проверке: {str(e)}', 'danger')
    
    return render_template('index.html')

@bp.route('/history')
def history():
    checks = CheckHistory.query.order_by(CheckHistory.check_date.desc()).limit(50).all()
    return render_template('history.html', checks=checks)

@bp.route('/download-report/<filename>')
def download_report(filename):
    """
    Маршрут для безопасного скачивания отчётов.
    Файлы физически лежат в папке REPORTS_FOLDER, но доступ к ним
    контролируется через этот маршрут.
    """
    try:
        # Используем абсолютный путь из конфига
        reports_dir = current_app.config['REPORTS_FOLDER']
        return send_from_directory(reports_dir, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)
