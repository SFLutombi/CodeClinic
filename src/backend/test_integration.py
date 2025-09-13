#!/usr/bin/env python3
"""
Integration test for the complete flow
"""

import requests
import json
import time

def test_backend_response_format():
    """Test that backend returns the correct JSON format"""
    
    test_data = {
        "zap_data": "SQL Injection - High - https://example.com\nXSS - Medium - https://example.com",
        "num_questions": 3
    }
    
    print("🧪 Testing Backend Response Format...")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-game",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check response structure
            if "questions" in result:
                questions = result["questions"]
                print(f"✅ Correct response format: {len(questions)} questions")
                
                # Validate question structure
                if questions and len(questions) > 0:
                    first_q = questions[0]
                    required_fields = [
                        'vuln_type', 'title', 'short_explain', 'exercise_type',
                        'exercise_prompt', 'choices', 'answer_key', 'hints',
                        'difficulty', 'xp', 'badge'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in first_q]
                    if missing_fields:
                        print(f"❌ Missing fields in question: {missing_fields}")
                        return False
                    else:
                        print("✅ All required fields present in questions")
                        return True
                else:
                    print("❌ No questions in response")
                    return False
            else:
                print("❌ Missing 'questions' key in response")
                print(f"Response keys: {list(result.keys())}")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def test_frontend_compatibility():
    """Test that the response format is compatible with frontend"""
    
    print("\n🧪 Testing Frontend Compatibility...")
    print("=" * 50)
    
    # Simulate the exact request the frontend would make
    test_data = {
        "zap_data": "Missing Anti-clickjacking Header - Medium - https://webwriter.io/dashboard/\nContent Security Policy (CSP) Header Not Set - Medium - https://webwriter.io/api/",
        "num_questions": 5
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-game",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if response matches frontend expectations
            if "questions" in result and isinstance(result["questions"], list):
                print(f"✅ Frontend-compatible response: {len(result['questions'])} questions")
                
                # Show sample question structure
                if result["questions"]:
                    sample = result["questions"][0]
                    print("\n📋 Sample Question Structure:")
                    for key, value in sample.items():
                        if isinstance(value, list):
                            print(f"  {key}: [{len(value)} items]")
                        else:
                            print(f"  {key}: {type(value).__name__}")
                
                return True
            else:
                print("❌ Response not compatible with frontend")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 CodeClinic Integration Test")
    print("=" * 60)
    
    # Test 1: Backend response format
    backend_ok = test_backend_response_format()
    
    # Test 2: Frontend compatibility
    frontend_ok = test_frontend_compatibility()
    
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"Backend Format: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Compatible: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 All tests passed! Integration is ready.")
        print("\n🌐 To test the frontend:")
        print("1. Start backend: python3 run.py")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Visit: http://localhost:3000/gemini-questions")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
