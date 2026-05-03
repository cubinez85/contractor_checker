from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from dotenv import load_dotenv
import os
import pkg_resources

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
admin = None

def create_admin_instance(app):
    """
    Создает экземпляр Admin с учетом версии Flask-Admin
    """
    from flask_admin import Admin as FlaskAdmin
    from app.admin.views import MyAdminIndexView
    
    try:
        # Пробуем создать админку с template_mode (для новых версий)
        from flask_admin import Admin as FlaskAdmin
        admin = FlaskAdmin(
            app=app,
            name='Contractor Checker Admin',
            index_view=MyAdminIndexView()
        )
        
        # Пытаемся установить template_mode если возможно
        try:
            # Для новых версий Flask-Admin
            admin.template_mode = 'bootstrap4'
        except:
            pass  # Игнорируем, если не поддерживается
            
        return admin
        
    except Exception as e:
        print(f"Error creating Admin: {e}")
        # Fallback на простую админку без template_mode
        return FlaskAdmin(
            app=app,
            name='Contractor Checker Admin',
            index_view=MyAdminIndexView()
        )

def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        app.config.from_object('config.Config')
    else:
        app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    
    global admin
    admin = create_admin_instance(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Регистрируем ModelView в админке
    from app.models import Contractor, CheckHistory
    from app.admin.views import ContractorView, CheckHistoryView
    
    admin.add_view(ContractorView(Contractor, db.session, name="Контрагенты", category="Управление"))
    admin.add_view(CheckHistoryView(CheckHistory, db.session, name="История проверок", category="Управление"))

    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)

    return app
