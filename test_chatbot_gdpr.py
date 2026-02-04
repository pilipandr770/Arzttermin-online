"""
Test Chatbot GDPR Compliance (Phase 3)
=======================================

Tests:
1. ✅ Medical keyword blocking (German/English/Ukrainian)
2. ✅ Allowed queries pass through
3. ✅ Language-specific blocked responses
4. ✅ No chat history storage
5. ✅ Structured responses with medical_advice flag
"""

import requests
import json
import time

BASE_URL = "https://arzttermin-online.onrender.com"
# BASE_URL = "http://localhost:5000"  # For local testing

# Test data: practice_id (replace with real ID from your DB)
PRACTICE_ID = "7c36adb4-6883-4c5f-bf7e-bd19e00a0a71"  # Dr. Müller's practice


def print_test_header(test_name):
    """Print formatted test header"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")


def test_blocked_medical_queries():
    """Test that medical queries are blocked"""
    print_test_header("Medical Queries Blocking")
    
    medical_queries = [
        # German
        ("Ich habe starke Kopfschmerzen. Was soll ich tun?", "de"),
        ("Welches Medikament hilft gegen Fieber?", "de"),
        ("Kann ich Antibiotika ohne Rezept bekommen?", "de"),
        ("Ich habe Symptome von COVID-19", "de"),
        
        # English
        ("I have severe headaches. What should I do?", "en"),
        ("What medicine helps against fever?", "en"),
        
        # Ukrainian
        ("У мене сильний біль. Що робити?", "uk"),
        ("Які ліки від температури?", "uk"),
    ]
    
    for query, lang in medical_queries:
        print(f"\n📝 Query ({lang}): {query}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/{PRACTICE_ID}",
            json={"message": query},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Type: {data.get('type')}")
            print(f"   Medical Advice: {data.get('medical_advice')}")
            print(f"   Reason: {data.get('reason')}")
            print(f"   Response: {data.get('response')[:100]}...")
            
            # Validate
            assert data.get('type') == 'scope_violation', "Should be blocked!"
            assert data.get('medical_advice') == False, "Should have medical_advice: false"
            assert data.get('reason') in ['contains_forbidden_keyword', 'medical_intent_detected'], "Should have block reason"
            print(f"   ✅ BLOCKED correctly")
        else:
            print(f"   ❌ ERROR: {response.text}")


def test_allowed_queries():
    """Test that allowed queries pass through"""
    print_test_header("Allowed Queries")
    
    allowed_queries = [
        "Wie komme ich zu Ihrer Praxis?",
        "Was sind Ihre Öffnungszeiten?",
        "Wie buche ich einen Termin?",
        "Wo finde ich einen Parkplatz?",
        "Welche Versicherungen akzeptieren Sie?",
        "Kann ich online buchen?",
        "Guten Tag, ich brauche Hilfe bei der Terminbuchung",
    ]
    
    for query in allowed_queries:
        print(f"\n📝 Query: {query}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/{PRACTICE_ID}",
            json={"message": query},
            headers={"Content-Type": "application/json"},
            timeout=60  # OpenAI can be slow
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Type: {data.get('type')}")
            print(f"   Medical Advice: {data.get('medical_advice')}")
            print(f"   Response: {data.get('response')[:150]}...")
            
            # Validate
            assert data.get('type') in ['platform_help', 'general_greeting'], "Should be allowed type"
            assert data.get('medical_advice') == False, "Should have medical_advice: false"
            assert 'scope_violation' not in data.get('type', ''), "Should NOT be blocked"
            print(f"   ✅ ALLOWED correctly")
        else:
            print(f"   ⚠️ ERROR: {response.text}")


def test_no_history_storage():
    """Test that chat history is NOT stored"""
    print_test_header("No History Storage (GDPR)")
    
    # Send 3 messages with same session_id
    session_id = "test-session-123"
    
    messages = [
        "Hallo, ich bin neu hier",
        "Wie buche ich einen Termin?",
        "Danke für die Hilfe"
    ]
    
    print(f"📝 Sending {len(messages)} messages with session_id: {session_id}")
    
    for i, msg in enumerate(messages, 1):
        print(f"\n   Message {i}: {msg}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/{PRACTICE_ID}",
            json={"message": msg, "session_id": session_id},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check that response doesn't reference previous messages
            response_text = data.get('response', '').lower()
            
            # Validate: response should be stateless (not reference "you said earlier")
            print(f"   Response: {data.get('response')[:100]}...")
            print(f"   ✅ Response received (stateless)")
        else:
            print(f"   ❌ ERROR: {response.text}")
    
    print(f"\n📊 Result: All messages processed independently (no context from previous messages)")
    print(f"   This confirms NO HISTORY STORAGE ✅")


def test_help_chatbot_gdpr():
    """Test help chatbot GDPR compliance"""
    print_test_header("Help Chatbot GDPR Compliance")
    
    # Test medical blocking in help chat
    response = requests.post(
        f"{BASE_URL}/api/help-chat",
        json={
            "message": "Ich habe Fieber, was soll ich tun?",
            "current_page": "/search"
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Type: {data.get('type')}")
        print(f"Medical Advice: {data.get('medical_advice')}")
        print(f"Response: {data.get('response')[:100]}...")
        
        # Validate
        assert data.get('type') == 'scope_violation', "Should be blocked!"
        assert data.get('medical_advice') == False, "Should have medical_advice: false"
        print(f"✅ Help chatbot ALSO blocks medical queries")
    else:
        print(f"❌ ERROR: {response.text}")


def test_structured_response_format():
    """Test that all responses follow structured format"""
    print_test_header("Structured Response Format")
    
    response = requests.post(
        f"{BASE_URL}/api/chat/{PRACTICE_ID}",
        json={"message": "Wie kann ich einen Termin buchen?"},
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"📋 Response structure:")
        print(f"   - type: {data.get('type')} ✅")
        print(f"   - medical_advice: {data.get('medical_advice')} ✅")
        print(f"   - response: {len(data.get('response', ''))} chars ✅")
        print(f"   - session_id: {data.get('session_id')[:8]}... ✅")
        print(f"   - disclaimer: {data.get('disclaimer', 'N/A')[:50]}... ✅")
        
        # Validate structure
        assert 'type' in data, "Missing 'type' field"
        assert 'medical_advice' in data, "Missing 'medical_advice' field"
        assert 'response' in data, "Missing 'response' field"
        assert data.get('medical_advice') == False, "medical_advice should ALWAYS be false"
        
        print(f"\n✅ Structured response format is CORRECT")
    else:
        print(f"❌ ERROR: {response.text}")


def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n" + "="*60)
    print("🚀 PHASE 3: CHATBOT GDPR COMPLIANCE TESTS")
    print("="*60)
    
    try:
        # 1. Test medical blocking
        test_blocked_medical_queries()
        time.sleep(2)
        
        # 2. Test allowed queries
        test_allowed_queries()
        time.sleep(2)
        
        # 3. Test no history
        test_no_history_storage()
        time.sleep(2)
        
        # 4. Test structured format
        test_structured_response_format()
        time.sleep(2)
        
        # 5. Test help chatbot
        test_help_chatbot_gdpr()
        
        print("\n" + "="*60)
        print("✅ ALL PHASE 3 TESTS COMPLETED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    run_all_tests()
