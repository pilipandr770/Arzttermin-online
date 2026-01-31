# AI Chatbot Feature - Documentation

## Обзор

AI Chatbot - это интеллектуальный ассистент для каждой медицинской практики, который автоматически отвечает на вопросы пациентов.

## Функциональность

### Что может чатбот:
- ✅ Отвечать на вопросы о расположении практики и как до нее добраться
- ✅ Информировать об часах работы
- ✅ Объяснять, где припарковаться
- ✅ Рассказывать о доступных услугах и оборудовании
- ✅ Информировать о принимаемых страховых компаниях
- ✅ Отвечать на FAQ
- ✅ Давать индивидуальные инструкции (заполняются врачом)

### Что НЕ может чатбот:
- ❌ Ставить медицинские диагнозы
- ❌ Бронировать термины (перенаправляет на систему бронирования)
- ❌ Выписывать рецепты
- ❌ Обрабатывать экстренные случаи (перенаправляет на 112)

## Архитектура

### Backend Components

1. **Model: Practice** (`app/models/practice.py`)
   - Поле `chatbot_instructions` (TEXT) для хранения кастомных инструкций

2. **Route: Chat API** (`app/routes/chat.py`)
   - `POST /api/chat/<practice_id>` - отправить сообщение
   - `POST /api/chat/<practice_id>/reset` - сбросить беседу
   - Интеграция с OpenAI GPT-4

3. **System Prompt Builder** (`app/routes/chat.py::get_system_prompt()`)
   - Комбинирует:
     * Базовую инструкцию (роль ассистента)
     * Данные практики (адрес, часы, контакты)
     * Кастомные инструкции врача

### Frontend Components

1. **Doctor Profile** (`app/templates/doctor/practice_profile_extended.html`)
   - Вкладка "Chatbot" (8-я вкладка)
   - Поле для ввода `chatbot_instructions`

2. **Patient Search** (`app/templates/patient/search.html`)
   - Кнопка "Chatbot - Praxis Assistent" в карточке доктора
   - Модальное окно с интерфейсом чата
   - JavaScript функции для отправки/получения сообщений

## Настройка

### 1. Получить OpenAI API Key

Зарегистрируйтесь на https://platform.openai.com/ и создайте API ключ.

### 2. Добавить в .env

```bash
# AI Chatbot
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview  # или gpt-3.5-turbo для экономии
```

### 3. Применить миграцию

```bash
python apply_migration.py 07_add_chatbot_instructions
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

## Использование для врачей

### Настройка инструкций

1. Войти в кабинет врача
2. Перейти в "Praxis Profil erweitert"
3. Открыть вкладку "Chatbot"
4. Ввести специфичные инструкции для практики

**Примеры инструкций:**

```
Wenn Patienten nach dem Weg zur Praxis fragen:
- Vom Hauptbahnhof nehmen Sie die U3 oder U6 Richtung Garching bis Münchner Freiheit
- Von dort sind es 5 Minuten zu Fuß
- Die Praxis befindet sich im 2. Stock, es gibt einen Aufzug

Für den ersten Termin:
- Bitte 10 Minuten früher kommen für Anmeldung
- Versicherungskarte und ggf. Überweisungsschein mitbringen
- Der Wartebereich ist im 2. Stock direkt links

Umkleiden und Vorbereitung:
- Umkleidekabinen befinden sich im Behandlungszimmer
- Bitte Wertsachen nicht unbeaufsichtigt lassen
```

5. Сохранить изменения

## Использование для пациентов

### Открытие чатбота

1. На странице поиска врачей найти нужного специалиста
2. В карточке доктора нажать кнопку "Chatbot - Praxis Assistent"
3. В модальном окне ввести вопрос
4. Получить ответ от AI ассистента

### Примеры вопросов

- "Wie komme ich zur Praxis?"
- "Wann haben Sie geöffnet?"
- "Wo kann ich parken?"
- "Welche Versicherungen akzeptieren Sie?"
- "Was soll ich zum ersten Termin mitbringen?"
- "Gibt es einen Aufzug?"

## Технические детали

### API Request Format

```json
POST /api/chat/<practice_id>
Content-Type: application/json

{
  "message": "Wie komme ich zur Praxis?",
  "conversation_id": "optional-uuid"
}
```

### API Response Format

```json
{
  "reply": "Von der U-Bahn Station...",
  "conversation_id": "uuid-for-continuation"
}
```

### Session Management

- История чата хранится в Flask session
- Ограничение: последние 20 сообщений (10 пар вопрос-ответ)
- Session key: `chat_history_{practice_id}_{conversation_id}`

### OpenAI Settings

- Model: `gpt-4-turbo-preview` (по умолчанию)
- Max tokens: 500
- Temperature: 0.7
- Система: Role-based prompt с контекстом практики

## Security & Privacy

- ✅ Сообщения не сохраняются в базе данных
- ✅ История хранится только в сессии пользователя
- ✅ API endpoint не требует авторизации (публичный доступ для пациентов)
- ✅ Rate limiting нужно добавить в production
- ✅ Валидация длины сообщения (max 1000 символов)

## Стоимость

### OpenAI Pricing (приблизительно)

- **GPT-4-turbo-preview**: ~$0.01 за 1K tokens input, ~$0.03 за 1K tokens output
- **GPT-3.5-turbo**: ~$0.0005 за 1K tokens input, ~$0.0015 за 1K tokens output

**Пример расчета:**
- Среднее сообщение: ~200 tokens (input + output)
- GPT-4: ~$0.008 за сообщение
- GPT-3.5: ~$0.0004 за сообщение
- 1000 сообщений/месяц:
  - GPT-4: ~$8/месяц
  - GPT-3.5: ~$0.40/месяц

## Рекомендации

### Production Setup

1. **Rate Limiting**: Добавить ограничение запросов (например, 10 сообщений/минуту на IP)
2. **Caching**: Кэшировать частые вопросы
3. **Monitoring**: Логировать использование для анализа затрат
4. **Fallback**: Graceful degradation если OpenAI API недоступен
5. **Content Moderation**: Фильтровать неподходящий контент

### UX Improvements

1. Добавить предустановленные вопросы (quick replies)
2. Typing indicator с анимацией
3. История чата persists между сессиями (опционально)
4. Экспорт беседы в email
5. Feedback система (thumbs up/down)

## Troubleshooting

### Chatbot не отвечает

1. Проверить `OPENAI_API_KEY` в .env
2. Проверить баланс OpenAI аккаунта
3. Проверить логи Flask на ошибки API

### Ответы неточные

1. Проверить что все поля профиля практики заполнены
2. Обновить `chatbot_instructions` с более подробной информацией
3. Уточнить формулировку вопроса

### Ошибка 503

- OpenAI API ключ не настроен
- Добавить в .env: `OPENAI_API_KEY=your-key-here`

## Roadmap

### Планируемые улучшения

- [ ] Multilingual support (английский, турецкий, русский)
- [ ] Voice input/output
- [ ] Интеграция с календарем (предложение свободных слотов)
- [ ] Analytics dashboard для врачей
- [ ] A/B testing разных промптов
- [ ] Fine-tuned модель специально для медицинских практик

## Support

При возникновении вопросов или проблем:
- Проверить документацию API: `/api/chat/<practice_id>`
- Проверить логи: `tail -f logs/app.log`
- Контакт разработчика: dev@terminfinder.de
