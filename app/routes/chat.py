"""
Chat Route - AI Chatbot Assistant для практик
"""
from flask import Blueprint, request, jsonify, session
from app.models.practice import Practice
from app.models.doctor import Doctor
import os
import uuid
import json

bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def get_system_prompt(practice: Practice, doctor: Doctor = None) -> str:
    """
    Создает system prompt для AI ассистента практики
    
    Комбинирует:
    - Общую инструкцию для всех ассистентов
    - Данные о практике (адрес, часы работы, контакты)
    - Кастомные инструкции от врача
    """
    
    # Общая инструкция
    base_instruction = """Du bist der AI-Assistent der Arztpraxis. Deine Aufgabe ist es, Patienten freundlich und professionell zu helfen.

Du kannst:
- Informationen über die Praxis geben (Adresse, Öffnungszeiten, Kontaktdaten)
- Häufig gestellte Fragen beantworten
- Wegbeschreibungen und Parkplatzmöglichkeiten erklären
- Über Leistungen und Ausstattung informieren
- Über akzeptierte Versicherungen informieren

Du kannst NICHT:
- Medizinische Diagnosen stellen
- Termine direkt buchen (verweise auf die Terminbuchung)
- Rezepte ausstellen
- Notfälle behandeln (verweise auf Notruf 112)

Antworte immer höflich, kurz und präzise. Bei medizinischen Fragen verweise auf einen Arzttermin."""

    # Информация о практике
    practice_info = f"\n\n=== INFORMATIONEN ÜBER DIE PRAXIS ===\n"
    practice_info += f"Name: {practice.name}\n"
    
    if practice.phone:
        practice_info += f"Telefon: {practice.phone}\n"
    
    if practice.owner_email:
        practice_info += f"Email: {practice.owner_email}\n"
    
    # Адрес
    if practice.address:
        try:
            address = json.loads(practice.address)
            practice_info += f"Adresse: {address.get('street', '')}, {address.get('plz', '')} {address.get('city', '')}\n"
        except:
            practice_info += f"Adresse: {practice.address}\n"
    
    # Часы работы
    if practice.opening_hours:
        try:
            hours = json.loads(practice.opening_hours)
            practice_info += "\nÖffnungszeiten:\n"
            days_de = {
                'monday': 'Montag',
                'tuesday': 'Dienstag',
                'wednesday': 'Mittwoch',
                'thursday': 'Donnerstag',
                'friday': 'Freitag',
                'saturday': 'Samstag',
                'sunday': 'Sonntag'
            }
            for day, times in hours.items():
                day_name = days_de.get(day, day)
                if isinstance(times, list) and times:
                    time_str = ', '.join([f"{t[0]}-{t[1]}" for t in times if isinstance(t, list) and len(t) >= 2])
                    practice_info += f"  {day_name}: {time_str}\n"
                elif isinstance(times, dict):
                    practice_info += f"  {day_name}: {times.get('open', '')}-{times.get('close', '')}\n"
        except:
            pass
    
    # Website
    if practice.website:
        practice_info += f"\nWebsite: {practice.website}\n"
    
    # Парковка
    if practice.parking_info:
        practice_info += f"\nParkmöglichkeiten: {practice.parking_info}\n"
    
    # Общественный транспорт
    if practice.public_transport:
        try:
            transport = json.loads(practice.public_transport)
            if transport:
                practice_info += "\nÖffentliche Verkehrsmittel:\n"
                for t in transport:
                    practice_info += f"  {t.get('type', '').capitalize()} {t.get('line', '')}: Haltestelle {t.get('stop', '')} ({t.get('distance', '')})\n"
        except:
            pass
    
    # Экстренные контакты
    if practice.emergency_phone:
        practice_info += f"\nNotfallkontakt: {practice.emergency_phone}\n"
    
    if practice.whatsapp_number:
        practice_info += f"WhatsApp: {practice.whatsapp_number}\n"
    
    # Особенности
    if practice.features:
        try:
            features = json.loads(practice.features)
            if features:
                practice_info += "\nBesonderheiten:\n"
                feature_names = {
                    'wheelchair_accessible': 'Rollstuhlgerecht',
                    'parking': 'Parkplatz vorhanden',
                    'wifi': 'WLAN für Patienten',
                    'elevator': 'Aufzug vorhanden',
                    'air_conditioning': 'Klimaanlage'
                }
                for f in features:
                    practice_info += f"  - {feature_names.get(f, f)}\n"
        except:
            pass
    
    # Кастомные инструкции от врача
    custom_instructions = ""
    if practice.chatbot_instructions:
        custom_instructions = f"\n\n=== ZUSÄTZLICHE ANWEISUNGEN DES ARZTES ===\n{practice.chatbot_instructions}\n"
    
    return base_instruction + practice_info + custom_instructions


@bp.route('/<practice_id>', methods=['POST'])
def chat_with_practice(practice_id):
    """
    Чат с AI ассистентом практики
    
    Request JSON:
    {
        "message": "Как до вас добраться?",
        "conversation_id": "optional-uuid"  // для продолжения беседы
    }
    
    Response JSON:
    {
        "reply": "Ответ от ассистента",
        "conversation_id": "uuid"
    }
    """
    try:
        # Проверяем OpenAI API ключ
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'error': 'Der Chatbot-Service ist derzeit nicht verfügbar. Bitte kontaktieren Sie die Praxis direkt.',
                'code': 'service_unavailable'
            }), 503
        
        # Получаем практику
        practice = Practice.query.get(uuid.UUID(practice_id))
        if not practice:
            return jsonify({'error': 'Praxis nicht gefunden'}), 404
        
        # Получаем сообщение пользователя
        data = request.get_json()
        if not data or not data.get('message'):
            return jsonify({'error': 'Nachricht ist erforderlich'}), 400
        
        user_message = data.get('message', '').strip()
        if len(user_message) > 1000:
            return jsonify({'error': 'Nachricht ist zu lang (max 1000 Zeichen)'}), 400
        
        # Conversation ID для истории
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Получаем или создаем историю разговора в сессии
        session_key = f'chat_history_{practice_id}_{conversation_id}'
        chat_history = session.get(session_key, [])
        
        # Ограничиваем историю последними 10 сообщениями
        if len(chat_history) > 20:  # 10 пар (user + assistant)
            chat_history = chat_history[-20:]
        
        # Добавляем новое сообщение пользователя
        chat_history.append({
            'role': 'user',
            'content': user_message
        })
        
        # Создаем system prompt
        system_prompt = get_system_prompt(practice)
        
        # Отправляем запрос к OpenAI
        try:
            # Сохраняем и удаляем прокси-переменные ДО импорта
            # Render.com автоматически добавляет HTTP_PROXY, что конфликтует с OpenAI/httpx
            proxy_vars = {}
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                if key in os.environ:
                    proxy_vars[key] = os.environ[key]
                    del os.environ[key]
            
            try:
                # Импортируем OpenAI ПОСЛЕ очистки переменных окружения
                from openai import OpenAI
                import httpx
                
                # Создаем httpx клиент без прокси явно
                http_client = httpx.Client(
                    timeout=30.0,
                    follow_redirects=True
                )
                
                # Создаем OpenAI client с нашим httpx клиентом
                client = OpenAI(
                    api_key=openai_api_key,
                    http_client=http_client
                )
            finally:
                # Восстанавливаем прокси-переменные
                for key, value in proxy_vars.items():
                    os.environ[key] = value
            
            messages = [
                {'role': 'system', 'content': system_prompt}
            ] + chat_history
            
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            assistant_reply = response.choices[0].message.content
            
            # Добавляем ответ в историю
            chat_history.append({
                'role': 'assistant',
                'content': assistant_reply
            })
            
            # Сохраняем историю в сессии
            session[session_key] = chat_history
            session.modified = True
            
            return jsonify({
                'reply': assistant_reply,
                'conversation_id': conversation_id
            })
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return jsonify({
                'error': 'Entschuldigung, ich konnte Ihre Anfrage nicht bearbeiten. Bitte versuchen Sie es später erneut.',
                'code': 'api_error'
            }), 500
    
    except ValueError:
        return jsonify({'error': 'Ungültige Praxis-ID'}), 400
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'error': 'Ein unerwarteter Fehler ist aufgetreten',
            'code': 'server_error'
        }), 500


@bp.route('/<practice_id>/reset', methods=['POST'])
def reset_conversation(practice_id):
    """
    Сброс истории разговора
    
    Request JSON:
    {
        "conversation_id": "uuid"
    }
    """
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if conversation_id:
        session_key = f'chat_history_{practice_id}_{conversation_id}'
        if session_key in session:
            del session[session_key]
            session.modified = True
    
    return jsonify({'message': 'Konversation zurückgesetzt'})
