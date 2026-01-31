#!/usr/bin/env python3
"""
Тест AI Chatbot функциональности
"""

import requests
import json

BASE_URL = 'http://localhost:5000'

print("=" * 70)
print("🤖 ТЕСТИРОВАНИЕ AI CHATBOT ФУНКЦИОНАЛЬНОСТИ")
print("=" * 70)

# Тест 1: Получить practice_id существующего врача
print("\n📋 Шаг 1: Получение practice_id...")

login_response = requests.post(f'{BASE_URL}/api/auth/doctor/login', json={
    'email': 'testdoctor@example.com',
    'password': 'Doctor123!'
})

if login_response.status_code == 200:
    token = login_response.json().get('access_token')
    print("✅ Логин успешен!")
    
    # Получить профиль практики
    headers = {'Authorization': f'Bearer {token}'}
    profile_response = requests.get(f'{BASE_URL}/api/practice/profile', headers=headers)
    
    if profile_response.status_code == 200:
        practice_data = profile_response.json()
        practice_id = practice_data['id']
        practice_name = practice_data['name']
        print(f"✅ Practice ID: {practice_id}")
        print(f"   Practice Name: {practice_name}")
        
        # Тест 2: Обновить chatbot_instructions
        print("\n📝 Шаг 2: Обновление chatbot instructions...")
        
        update_response = requests.put(
            f'{BASE_URL}/api/practice/profile/extended',
            headers=headers,
            json={
                'chatbot_instructions': '''
Wenn Patienten nach dem Weg zur Praxis fragen:
- Vom Hauptbahnhof nehmen Sie die U3 Richtung Moosach bis Universität
- Von dort sind es 3 Minuten zu Fuß
- Die Praxis befindet sich im Erdgeschoss

Für den ersten Termin:
- Bitte 15 Minuten früher kommen für Anmeldung
- Versicherungskarte mitbringen
- Der Wartebereich ist direkt beim Eingang rechts

Parken:
- Parkhaus am Hauptbahnhof (5 Minuten zu Fuß)
- Straßenparken möglich (Parkscheinautomat)
                '''
            }
        )
        
        if update_response.status_code == 200:
            print("✅ Chatbot instructions aktualisiert!")
        else:
            print(f"❌ Fehler beim Aktualisieren: {update_response.status_code}")
        
        # Тест 3: Testen des Chatbots
        print("\n" + "=" * 70)
        print("💬 Шаг 3: Testen des Chatbots")
        print("=" * 70)
        
        # Проверяем наличие OpenAI API ключа
        print("\n⚠️  WICHTIG: Stellen Sie sicher, dass OPENAI_API_KEY in .env gesetzt ist!")
        print("   Beispiel: OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx\n")
        
        test_questions = [
            "Wie komme ich zur Praxis?",
            "Wann haben Sie geöffnet?",
            "Wo kann ich parken?",
            "Was soll ich zum ersten Termin mitbringen?"
        ]
        
        conversation_id = None
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n❓ Frage {i}: {question}")
            
            chat_response = requests.post(
                f'{BASE_URL}/api/chat/{practice_id}',
                json={
                    'message': question,
                    'conversation_id': conversation_id
                }
            )
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                conversation_id = chat_data['conversation_id']
                print(f"✅ Antwort: {chat_data['reply'][:200]}...")
            elif chat_response.status_code == 503:
                print("⚠️  Service nicht verfügbar (OpenAI API Key fehlt)")
                print("   Fügen Sie OPENAI_API_KEY in die .env Datei hinzu")
                break
            else:
                error_data = chat_response.json()
                print(f"❌ Fehler {chat_response.status_code}: {error_data.get('error', 'Unknown error')}")
                break
        
        print("\n" + "=" * 70)
        print("✅ TESTS ABGESCHLOSSEN")
        print("=" * 70)
        print("\n📋 Zusammenfassung:")
        print(f"   Practice ID: {practice_id}")
        print(f"   Practice Name: {practice_name}")
        print(f"   Chatbot Instructions: {'✅ Gesetzt' if update_response.status_code == 200 else '❌ Fehler'}")
        print(f"   Conversation ID: {conversation_id if conversation_id else 'N/A'}")
        print("\n💡 Nächste Schritte:")
        print("   1. Setzen Sie OPENAI_API_KEY in der .env Datei")
        print("   2. Starten Sie den Server neu: python run.py")
        print("   3. Öffnen Sie die Patientensuche und testen Sie den Chatbot")
        
    else:
        print(f"❌ Fehler beim Laden des Profils: {profile_response.status_code}")
else:
    print(f"❌ Login fehlgeschlagen: {login_response.status_code}")
    print("   Möglicherweise existiert der Test-Doktor nicht")
    print("   Erstellen Sie einen neuen Arzt oder verwenden Sie einen vorhandenen")
