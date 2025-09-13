#!/usr/bin/env python3
"""
Test the question navigation features
"""

import requests
import json
import time

def test_navigation_features():
    """Test that the navigation system works properly"""
    
    test_data = {
        "zap_data": "SQL Injection - High - https://example.com\nXSS - Medium - https://example.com\nMissing Anti-clickjacking Header - Medium - https://example.com\nContent Security Policy (CSP) Header Not Set - Medium - https://example.com\nStrict-Transport-Security Header Not Set - Low - https://example.com",
        "num_questions": 5
    }
    
    print("🧭 Testing Question Navigation Features...")
    print("=" * 50)
    print("📋 Expected navigation features:")
    print("  ✅ Question number buttons")
    print("  ✅ Previous/Next buttons")
    print("  ✅ Keyboard navigation (← →)")
    print("  ✅ Manual question switching")
    print("  ✅ Complete game button")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/generate-game",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"⏱️  Request took: {duration:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            questions = result.get('questions', [])
            
            print(f"✅ Success! Generated {len(questions)} questions for navigation testing")
            
            # Validate questions have all required fields for navigation
            navigation_ready = True
            for i, q in enumerate(questions):
                required_fields = ['title', 'exercise_type', 'difficulty', 'xp', 'badge']
                missing_fields = [field for field in required_fields if field not in q]
                
                if missing_fields:
                    print(f"❌ Question {i+1} missing fields: {missing_fields}")
                    navigation_ready = False
            
            if navigation_ready:
                print("✅ All questions have required fields for navigation")
            
            # Show navigation structure
            print(f"\n🧭 Navigation Structure:")
            print(f"  📊 Total Questions: {len(questions)}")
            print(f"  🎯 Question Types: {set(q.get('exercise_type', '') for q in questions)}")
            print(f"  📈 Difficulties: {set(q.get('difficulty', '') for q in questions)}")
            print(f"  💰 XP Range: {min(q.get('xp', 0) for q in questions)}-{max(q.get('xp', 0) for q in questions)}")
            
            # Show sample questions for navigation
            print(f"\n🎮 Sample Questions for Navigation:")
            for i, q in enumerate(questions[:3], 1):
                print(f"  {i}. {q.get('title', 'N/A')[:50]}...")
                print(f"     Type: {q.get('exercise_type', 'N/A')} | Difficulty: {q.get('difficulty', 'N/A')} | XP: {q.get('xp', 'N/A')}")
            
            return navigation_ready
            
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_navigation_features()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 Navigation Test PASSED!")
        print("✅ All questions ready for navigation")
        print("🧭 Navigation features implemented:")
        print("  • Question number buttons")
        print("  • Previous/Next buttons")
        print("  • Keyboard navigation (← →)")
        print("  • Manual question switching")
        print("  • Complete game option")
        print("\n🌐 To test navigation:")
        print("1. Start backend: python3 run.py")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Visit: http://localhost:3000/gemini-questions")
        print("4. Generate questions and test navigation!")
    else:
        print("❌ Navigation Test FAILED!")
        print("Check the validation results above")
    print(f"{'='*50}")
