"""
Основные маршруты приложения
"""
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Главная страница - лендинг"""
    return render_template('index.html')