from flask import Blueprint

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Этот файл нужен только для blueprint, 
# регистрация ModelView будет происходить в app/__init__.py после создания admin
