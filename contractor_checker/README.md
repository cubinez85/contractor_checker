# Сервис проверки контрагентов через ФНС

Веб-приложение для автоматической проверки благонадежности контрагентов по ИНН с использованием данных ФНС.

## 🚀 Функциональность

- ✅ Проверка юридических лиц (ИНН, 10 цифр)
- ✅ Проверка индивидуальных предпринимателей (ИНН, 12 цифр)
- ✅ Гибридная система проверки:
  - Быстрая проверка через API `egrul.itsoft.ru`
  - При ошибке - проверка через официальный сайт ФНС (`egrul.nalog.ru`)
- ✅ Автоматическое определение статуса:
  - Действующее / Действующий ИП
  - В стадии ликвидации
  - Недействующее / Недействующий ИП
- ✅ Генерация Excel-отчетов с результатами
- ✅ Автоматическая отправка отчетов на email
- ✅ История всех проверок
- ✅ Административная панель для управления данными
- ✅ Защита базовой аутентификацией через Nginx

## 🛠 Технологический стек

- **Backend:** Python 3.10, Flask 2.3
- **База данных:** PostgreSQL
- **ORM:** SQLAlchemy, Flask-Migrate
- **Админка:** Flask-Admin
- **Веб-сервер:** Nginx, Gunicorn
- **Процесс-менеджер:** systemd
- **Парсинг:** Requests, BeautifulSoup4
- **Отчеты:** Pandas, OpenPyXL
- **Почта:** SMTP (smtplib)
- **Aутентификация** использование встроенной аутентификации Nginx

## 📁 Структура проекта
/var/www/contractor_checker/
├── app/
│ ├── init.py # Инициализация Flask приложения
│ ├── models.py # Модели базы данных
│ ├── admin/
│ │ ├── init.py # Blueprint админки
│ │ └── views.py # Представления админки
│ ├── main/
│ │ ├── init.py # Blueprint главной страницы
│ │ └── routes.py # Маршруты приложения
│ ├── services/
│ │ ├── fns_checker.py # Гибридный парсер ФНС
│ │ ├── report_generator.py # Генерация Excel-отчетов
│ │ └── email_sender.py # Отправка email
│ └── templates/ # HTML шаблоны
│ ├── base.html
│ ├── index.html
│ ├── history.html
│ └── admin/
│ └── dashboard.html
├── logs/ # Логи приложения
├── reports/ # Сгенерированные отчеты
├── venv/ # Виртуальное окружение
├── .env # Переменные окружения
├── config.py # Конфигурация приложения
├── run.py # Точка входа
└── requirements.txt # Зависимости

## 🔍 Алгоритм проверки контрагента

### Гибридный подход (fns_checker.py)

1. **Проверка через egrul.itsoft.ru** (быстрый уровень)
   - Бесплатный API, не требует авторизации
   - Определяет тип по длине ИНН (10 - ЮЛ, 12 - ИП)
   - Возвращает статус и наименование

2. **Fallback на официальный сайт ФНС** (надежный уровень)
   - Активируется при ошибке или статусе "inactive" для ЮЛ
   - Эмулирует поведение браузера на `egrul.nalog.ru`
   - POST-запрос с параметрами поиска
   - Получение ID запроса
   - GET-запрос результата через 2 секунды
   - Парсинг JSON-ответа

3. **Определение статуса**
   - **active**: Действующее (есть запись в ЕГРЮЛ/ЕГРИП)
   - **liquidating**: В стадии ликвидации (по ключевым словам)
   - **inactive**: Недействующее (404 от API или отсутствие записи)

## 📧 Формирование отчетов

Генерируется Excel-файл со следующими колонками:
- **ИНН** (с указанием типа: ЮЛ/ИП)
- **Наименование** (полное наименование организации/ФИО ИП)
- **Тип** (Юридическое лицо / Индивидуальный предприниматель)
- **Статус** (Действующее / Действующий ИП / В стадии ликвидации / Недействующее)
- **Дата регистрации**
- **Дата проверки**
- **Рекомендация** (к сотрудничеству / исключить / ручная проверка)

## 🖥 Административная панель

Flask-Admin предоставляет:
- 📊 Дашборд со статистикой проверок
- 👥 Управление контрагентами (CRUD)
- 📜 История проверок с фильтрацией
- 🔍 Поиск по ИНН и наименованию
- 📤 Экспорт данных в CSV/Excel

## 🔐 Безопасность

- Базовая аутентификация на уровне Nginx (htpasswd)
- Защита директории с отчетами (internal)
- Все пароли и ключи в .env файле
- PostgreSQL с изолированным пользователем
- Логирование всех ошибок и действий

## ⚙️ Установка и развертывание

### Требования
- Ubuntu 22.04 LTS
- Python 3.10+
- PostgreSQL 14+
- Nginx
- Git

### Быстрая установка

```bash
# Клонирование проекта
cd ~
git clone https://github.com/your-repo/contractor-checker.git 

# Настройка окружения
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка базы данных
sudo -u postgres psql
CREATE DATABASE contractor_db;
CREATE USER contractor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE contractor_db TO contractor_user;
\q

# Настройка переменных окружения
cp .env.example .env
nano .env  # Отредактируйте под свои параметры

# Инициализация базы данных
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Настройка Nginx и systemd
sudo cp config/nginx.conf /etc/nginx/sites-available/contractor_checker
sudo ln -s /etc/nginx/sites-available/contractor_checker /etc/nginx/sites-enabled/
sudo cp config/contractor_checker.service /etc/systemd/system/
sudo systemctl start contractor_checker
sudo systemctl enable contractor_checker
