# Security Audit - TerminFinder MVP

**Дата аудита:** 04.02.2026  
**Статус:** Development (Pre-Production)  
**Приоритет:** 🔴 КРИТИЧНО - закрыть перед production

---

## 🎯 Общая оценка: 4/10 (НЕ ГОТОВО к production)

---

## ❌ КРИТИЧЕСКИЕ УЯЗВИМОСТИ (Закрыть СЕЙЧАС)

### 1. ⚠️ CSRF Protection ОТКЛЮЧЕНА
**Файл:** `config.py:95`
```python
WTF_CSRF_ENABLED = False  # ❌ КРИТИЧНО
```

**Риск:** Атаки Cross-Site Request Forgery  
**Exploit:** Злоумышленник может подделать запросы от имени пользователя  
**Атакуемые эндпоинты:**
- POST `/api/booking/book` - создание букингов
- POST `/api/patient/alerts` - создание alerts
- DELETE `/api/booking/cancel` - отмена букингов
- POST `/api/chat/*` - отправка сообщений чатбота

**Решение (ПРИОРИТЕТ 1):**
```python
# config.py
WTF_CSRF_ENABLED = True  # ✅ Включить

# Добавить Flask-WTF
# pip install Flask-WTF
```

**Исправление:**
- Использовать Flask-WTF для CSRF токенов
- Добавить CSRF токен в каждую форму/AJAX запрос
- Или использовать SameSite cookies для JWT

---

### 2. ⚠️ CORS Полностью Открыт
**Файл:** `app/__init__.py:32`
```python
CORS(app)  # ❌ Разрешает ВСЕ домены
```

**Риск:** Cross-Origin атаки с любого домена  
**Exploit:** Любой сайт может отправлять API запросы  

**Решение (ПРИОРИТЕТ 1):**
```python
# app/__init__.py
CORS(app, 
    origins=[
        'https://terminfinder.de',
        'https://www.terminfinder.de',
        'https://arzttermin-online.onrender.com'
    ],
    supports_credentials=True,
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
)
```

---

### 3. ⚠️ Rate Limiting ОТСУТСТВУЕТ
**Статус:** НЕТ защиты от brute-force  

**Риск:** 
- Brute-force атаки на `/login`
- DDoS на API эндпоинты
- Spam через chatbot (OpenAI API abuse)

**Атакуемые эндпоинты:**
- POST `/login` - перебор паролей
- POST `/register` - спам регистрации
- POST `/api/help-chat` - OpenAI API abuse ($$$)
- POST `/api/chat/*` - OpenAI API abuse ($$$)
- POST `/api/booking/book` - спам букингов

**Решение (ПРИОРИТЕТ 1):**
```bash
pip install Flask-Limiter
```

```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",  # или Redis
    default_limits=["200 per day", "50 per hour"]
)

# app/routes/auth.py
@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Макс 5 попыток логина в минуту
def login():
    pass

# app/routes/help_chat.py
@bp.route('/api/help-chat', methods=['POST'])
@limiter.limit("10 per minute")  # Макс 10 сообщений чатбота в минуту
def help_chat():
    pass
```

---

### 4. ⚠️ SQL Injection - Частичная Защита
**Статус:** SQLAlchemy ORM защищает, но есть риски  

**Защищено (✅):**
```python
# Использование ORM (безопасно)
Doctor.query.filter_by(email=email).first()
Practice.query.get(practice_id)
```

**Потенциальные риски (⚠️):**
- Если где-то используется `db.session.execute(f"SELECT * FROM...")`
- Если используется raw SQL с f-strings
- Search запросы с LIKE (нужна валидация)

**Проверка:**
```bash
# Найти опасные паттерны
grep -r "db.session.execute" app/
grep -r "text(f\"" app/
grep -r "%.format(" app/ | grep "SELECT\|INSERT\|UPDATE\|DELETE"
```

**Решение:**
- ✅ Продолжать использовать ORM
- ⚠️ Если нужен raw SQL - использовать параметризованные запросы:
```python
# ❌ ОПАСНО
db.session.execute(f"SELECT * FROM users WHERE email = '{email}'")

# ✅ БЕЗОПАСНО
db.session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)
```

---

### 5. ⚠️ XSS (Cross-Site Scripting)
**Статус:** Частичная защита через Jinja2 auto-escape  

**Защищено (✅):**
- Jinja2 templates auto-escape по умолчанию
- `{{ variable }}` экранируется автоматически

**НЕ защищено (❌):**
- Frontend JavaScript вставка HTML без санитизации
- API responses вставляемые через `innerHTML`

**Найдено в коде:**
```javascript
// app/templates/patient/search.html
contentDiv.innerHTML = `<i class="bi bi-robot me-2"></i>${text}`;  // ⚠️ Потенциальный XSS
```

**Решение:**
```javascript
// ❌ ОПАСНО
contentDiv.innerHTML = userInput;

// ✅ БЕЗОПАСНО
contentDiv.textContent = userInput;

// Или использовать DOMPurify
import DOMPurify from 'dompurify';
contentDiv.innerHTML = DOMPurify.sanitize(userInput);
```

---

## ⚠️ ВЫСОКИЙ РИСК (Закрыть до production)

### 6. Session Security - Weak SECRET_KEY
**Файл:** `config.py:15`
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
```

**Риск:** Если SECRET_KEY утекает - все сессии скомпрометированы  

**Решение:**
```bash
# Генерация сильного ключа
python -c "import secrets; print(secrets.token_hex(32))"

# В .env
SECRET_KEY=<64-символьный случайный ключ>
JWT_SECRET_KEY=<другой 64-символьный ключ>
```

**Проверка на Render:**
```bash
# ❌ КРИТИЧНО если используется дефолтный ключ
echo $SECRET_KEY
```

---

### 7. JWT Token Security
**Текущая реализация:**
```python
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # ✅ OK
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # ⚠️ Долго
JWT_TOKEN_LOCATION = ['headers']  # ✅ OK
```

**Проблемы:**
- ❌ Нет JWT blacklist (невозможно "разлогинить" пользователя)
- ❌ Нет проверки device/IP при обновлении токена
- ⚠️ Refresh token на 30 дней - слишком долго

**Решение:**
```python
# Добавить JWT blacklist (требует Redis или DB)
from flask_jwt_extended import get_jti
from datetime import datetime

# При logout
@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jti(get_jwt())
    # Добавить jti в blacklist (Redis или DB)
    revoked_tokens.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200

# Проверка при каждом запросе
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in revoked_tokens
```

---

### 8. Password Security
**Текущая реализация:**
```python
# Используется bcrypt ✅
from bcrypt import hashpw, checkpw, gensalt
```

**Проблемы:**
- ❌ Нет требований к сложности пароля
- ❌ Нет проверки на утекшие пароли (haveibeenpwned API)
- ❌ Нет ограничения длины пароля (DoS через bcrypt)

**Решение:**
```python
# app/utils/password_validator.py
import re
import requests

def validate_password_strength(password):
    """Проверка сложности пароля"""
    if len(password) < 8:
        return False, "Пароль должен быть минимум 8 символов"
    
    if len(password) > 72:  # bcrypt limit
        return False, "Пароль слишком длинный (макс 72 символа)"
    
    if not re.search(r"[a-z]", password):
        return False, "Пароль должен содержать строчные буквы"
    
    if not re.search(r"[A-Z]", password):
        return False, "Пароль должен содержать заглавные буквы"
    
    if not re.search(r"\d", password):
        return False, "Пароль должен содержать цифры"
    
    return True, "OK"

def check_password_breach(password):
    """Проверка через haveibeenpwned API"""
    import hashlib
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    response = requests.get(url)
    
    if suffix in response.text:
        return True  # Пароль скомпрометирован
    return False
```

---

### 9. Input Validation ОТСУТСТВУЕТ
**Статус:** Нет централизованной валидации  

**Проблемы:**
- Email без валидации формата
- Phone без валидации формата
- Free-text поля без ограничения длины
- Нет санитизации HTML тегов

**Решение:**
```bash
pip install marshmallow
```

```python
# app/schemas/user_schema.py
from marshmallow import Schema, fields, validates, ValidationError
import re

class RegistrationSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda p: len(p) >= 8)
    phone = fields.Str()
    
    @validates('phone')
    def validate_phone(self, value):
        if value and not re.match(r'^\+?[\d\s\-\(\)]+$', value):
            raise ValidationError('Неверный формат телефона')

# В routes
from app.schemas.user_schema import RegistrationSchema

@bp.route('/register', methods=['POST'])
def register():
    schema = RegistrationSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    # ... продолжить
```

---

### 10. Logging & Monitoring
**Статус:** Базовый logging (print statements)  

**Проблемы:**
- ❌ Нет security event logging
- ❌ Нет мониторинга подозрительной активности
- ❌ Нет alerting для атак

**Решение:**
```python
# app/security/audit_log.py
import logging
from datetime import datetime

security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

def log_security_event(event_type, user_id=None, ip=None, details=None):
    """Логирование security событий"""
    security_logger.info({
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_type,
        'user_id': user_id,
        'ip': ip,
        'details': details
    })

# Использование
log_security_event('LOGIN_FAILED', ip=request.remote_addr, details={'email': email})
log_security_event('PASSWORD_RESET_REQUESTED', user_id=user.id)
log_security_event('SUSPICIOUS_ACTIVITY', ip=request.remote_addr, details={'reason': 'Too many requests'})
```

---

## ⚡ СРЕДНИЙ РИСК (Исправить до launch)

### 11. HTTPS/TLS
**Статус:** Render.com предоставляет TLS ✅  
**Проблема:** Нет принудительного redirect HTTP → HTTPS  

**Решение:**
```python
# app/__init__.py
from flask_talisman import Talisman

Talisman(app, 
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
    }
)
```

### 12. API Response Information Disclosure
**Проблема:** Детальные error messages  

```python
# ❌ ПЛОХО
return jsonify({'error': str(e)}), 500  # Раскрывает внутренние детали

# ✅ ХОРОШО
logger.error(f"Error details: {str(e)}")  # Логируем детали
return jsonify({'error': 'Internal server error'}), 500  # Показываем generic message
```

### 13. OpenAI API Key Protection
**Текущая реализация:**
```python
openai_api_key = os.getenv('OPENAI_API_KEY')  # ✅ Из environment
```

**Проблемы:**
- ⚠️ Нет rate limiting для OpenAI вызовов = $$$
- ⚠️ Нет максимального budget limit

**Решение:**
- Установить usage limits в OpenAI dashboard
- Добавить rate limiting (см. выше)
- Мониторить usage через OpenAI API

---

## 📋 ЧЕКЛИСТ: Что закрыть и КОГДА

### 🔴 СЕЙЧАС (Перед любым тестированием)
- [ ] Rate Limiting для login/register/chat (КРИТИЧНО)
- [ ] CORS настройка (только доверенные домены)
- [ ] Strong SECRET_KEY generation и проверка на Render
- [ ] Input validation для всех форм

### 🟠 ДО PRODUCTION (Перед запуском)
- [ ] CSRF Protection включить
- [ ] XSS санитизация на фронтенде
- [ ] Password strength requirements
- [ ] JWT blacklist mechanism
- [ ] Security audit logging
- [ ] HTTPS enforcement (Talisman)
- [ ] Error message sanitization

### 🟡 ПОСЛЕ LAUNCH (Continuous improvement)
- [ ] Penetration testing (нанять профи)
- [ ] Security monitoring (Sentry, CloudFlare WAF)
- [ ] Regular dependency updates (`pip-audit`)
- [ ] Bug bounty program
- [ ] SOC2 compliance (если нужен для enterprise)

---

## 🛡️ Рекомендации по Stripe Integration

Когда будете добавлять Stripe:

### КРИТИЧНО:
1. **Webhook Signature Verification**
```python
@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Обработка события
```

2. **Idempotency Keys**
```python
stripe.PaymentIntent.create(
    amount=1000,
    currency='eur',
    idempotency_key=f"booking-{booking_id}"  # Защита от дублей
)
```

3. **PCI Compliance:**
- ✅ Использовать Stripe.js (НЕ отправлять card data на сервер)
- ✅ HTTPS обязательно
- ✅ Не логировать payment info

---

## 🎯 Итоговая Рекомендация

**ОТВЕТ на вопрос "Когда закрывать дырки?":**

### ❌ НЕ В КОНЦЕ! 

**Почему:**
1. Исправлять security bugs дорого и долго
2. Может потребовать полный редизайн архитектуры
3. Репутационный риск при утечке данных

### ✅ СЕЙЧАС (Development Phase):

**Золотое правило:** **"Security by Design"**

1. **НЕМЕДЛЕННО (эта неделя):**
   - Rate Limiting (защита API и budget)
   - CORS configuration
   - Strong secrets
   - Input validation

2. **ДО первого external теста (следующие 2 недели):**
   - CSRF protection
   - XSS sanitization
   - Password security
   - JWT improvements

3. **ДО Production:**
   - Professional penetration test
   - Security headers (Talisman)
   - Audit logging
   - Monitoring

**Прогноз времени:**
- Базовая защита: 2-3 дня работы
- Полная защита: 1-2 недели
- Professional audit: $2000-5000

**Текущий статус:** 4/10 - НЕ готово к production, но можно быстро исправить! 🚀

---

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [JWT Best Practices](https://auth0.com/blog/jwt-security-best-practices/)
- [Stripe Security Guide](https://stripe.com/docs/security)
