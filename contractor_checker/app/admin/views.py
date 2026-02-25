from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView, expose
from flask import redirect, url_for
from datetime import datetime, timedelta

# Убираем импорт admin и db из app
# Они будут переданы позже

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # Импортируем модели внутри метода, чтобы избежать циклического импорта
        from app.models import Contractor, CheckHistory
        
        # Статистика для дашборда
        total_checks = CheckHistory.query.count()
        total_contractors = Contractor.query.count()
        
        # Проверки за последние 24 часа
        last_24h = CheckHistory.query.filter(
            CheckHistory.check_date >= datetime.now() - timedelta(hours=24)
        ).count()
        
        # Статусы контрагентов
        active = Contractor.query.filter_by(status='active').count()
        inactive = Contractor.query.filter_by(status='inactive').count()
        liquidating = Contractor.query.filter_by(status='liquidating').count()
        
        return self.render('admin/dashboard.html',
            total_checks=total_checks,
            total_contractors=total_contractors,
            last_24h=last_24h,
            active=active,
            inactive=inactive,
            liquidating=liquidating
        )

class SecureModelView(ModelView):
    def is_accessible(self):
        return True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.index'))

class ContractorView(SecureModelView):
    column_list = ['id', 'inn', 'name', 'status', 'registration_date', 'last_check_date']
    column_searchable_list = ['inn', 'name']
    column_filters = ['status', 'registration_date']
    column_labels = {
        'id': 'ID',
        'inn': 'ИНН',
        'name': 'Наименование',
        'status': 'Статус',
        'registration_date': 'Дата регистрации',
        'last_check_date': 'Последняя проверка'
    }
    column_formatters = {
        'status': lambda v, c, m, p: {
            'active': '✅ Действующее',
            'inactive': '❌ Недействующее',
            'liquidating': '⚠️ В стадии ликвидации'
        }.get(m.status, m.status)
    }
    can_create = True
    can_edit = True
    can_delete = True
    page_size = 50
    can_export = True
    export_types = ['csv', 'xlsx']

class CheckHistoryView(SecureModelView):
    column_list = ['id', 'user_email', 'check_date', 'inn_count', 'email_sent']
    column_searchable_list = ['user_email']
    column_filters = ['check_date', 'email_sent']
    column_labels = {
        'id': 'ID',
        'user_email': 'Email пользователя',
        'check_date': 'Дата проверки',
        'inn_count': 'Количество ИНН',
        'email_sent': 'Отправлено на email'
    }
    column_formatters = {
        'inn_count': lambda v, c, m, p: len(m.inn_list.split(',')) if m.inn_list else 0,
        'email_sent': lambda v, c, m, p: '✅ Да' if m.email_sent else '❌ Нет',
        'check_date': lambda v, c, m, p: m.check_date.strftime('%d.%m.%Y %H:%M') if m.check_date else ''
    }
    can_create = False
    can_edit = True
    can_delete = True
    page_size = 50

