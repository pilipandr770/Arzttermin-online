"""
Test script for Help Chatbot Widget
Тестирует все три типа пользователей
"""
import requests
import json

BASE_URL = "http://localhost:5000"
# BASE_URL = "https://arzttermin-online.onrender.com"  # Для production

def test_help_chat_as_guest():
    """Test help chat без JWT токена (guest user)"""
    print("\n=== TEST 1: Guest User ===")
    
    response = requests.post(
        f"{BASE_URL}/api/help-chat",
        json={
            "message": "Was ist TerminFinder und wie funktioniert es?",
            "current_page": "/"
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"User Type: {data.get('user_type')}")
    print(f"Reply: {data.get('reply')[:200]}...")  # Erste 200 Zeichen
    
    return response.status_code == 200


def test_help_chat_with_token(token, user_type_name):
    """Test help chat с JWT токеном"""
    print(f"\n=== TEST: {user_type_name} ===")
    
    response = requests.post(
        f"{BASE_URL}/api/help-chat",
        json={
            "message": "Wie kann ich mein Profil aktualisieren?",
            "current_page": f"/{user_type_name.lower()}/dashboard"
        },
        cookies={"access_token_cookie": token}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"User Type: {data.get('user_type')}")
    print(f"Reply: {data.get('reply')[:200]}...")
    
    return response.status_code == 200


def test_reset():
    """Test chat reset"""
    print("\n=== TEST: Reset Chat ===")
    
    response = requests.post(f"{BASE_URL}/api/help-chat/reset")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200


def test_context_awareness():
    """Test context-specific responses"""
    print("\n=== TEST: Context Awareness ===")
    
    pages = [
        ("/", "Startseite"),
        ("/patient/search", "Arztsuche"),
        ("/patient/bookings", "Meine Termine"),
        ("/doctor/calendar", "Arzt Kalender"),
        ("/practice/profile", "Praxisprofil")
    ]
    
    for page, description in pages:
        print(f"\n  Testing page: {description} ({page})")
        response = requests.post(
            f"{BASE_URL}/api/help-chat",
            json={
                "message": "Wo bin ich und was kann ich hier machen?",
                "current_page": page
            }
        )
        
        if response.status_code == 200:
            reply = response.json().get('reply', '')
            print(f"  ✓ Response length: {len(reply)} chars")
        else:
            print(f"  ✗ Failed: {response.status_code}")


def test_conversation_history():
    """Test chat history (multiple messages)"""
    print("\n=== TEST: Conversation History ===")
    
    messages = [
        "Hallo, ich bin neu hier",
        "Ich bin Patient und suche einen Arzt",
        "Wie funktioniert die Terminbuchung?",
        "Gibt es auch Online-Termine?",
        "Danke für die Hilfe!"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n  Message {i}: {msg}")
        response = requests.post(
            f"{BASE_URL}/api/help-chat",
            json={
                "message": msg,
                "current_page": "/patient/search"
            }
        )
        
        if response.status_code == 200:
            reply = response.json().get('reply', '')
            print(f"  ✓ Got reply ({len(reply)} chars)")
        else:
            print(f"  ✗ Failed: {response.status_code}")


def main():
    print("=" * 60)
    print("Help Chatbot Widget Test Suite")
    print("=" * 60)
    
    # Test 1: Guest user
    try:
        success = test_help_chat_as_guest()
        print(f"\n✓ Guest test: {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"\n✗ Guest test FAILED: {e}")
    
    # Test 2: Context awareness
    try:
        test_context_awareness()
        print(f"\n✓ Context test: PASSED")
    except Exception as e:
        print(f"\n✗ Context test FAILED: {e}")
    
    # Test 3: Conversation history
    try:
        test_conversation_history()
        print(f"\n✓ History test: PASSED")
    except Exception as e:
        print(f"\n✗ History test FAILED: {e}")
    
    # Test 4: Reset
    try:
        success = test_reset()
        print(f"\n✓ Reset test: {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"\n✗ Reset test FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
    
    print("\n📝 Manual Testing Steps:")
    print("1. Open http://localhost:5000 in browser")
    print("2. Look for purple button in bottom-right corner")
    print("3. Click button to open chat widget")
    print("4. Test as guest: Ask 'Was ist TerminFinder?'")
    print("5. Login as patient and test from /patient/search")
    print("6. Login as doctor and test from /practice/profile")
    print("7. Try different pages and see context-specific responses")


if __name__ == "__main__":
    main()
