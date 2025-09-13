#!/usr/bin/env python3
"""
Test the updated prompt with deterministic answers
"""

import requests
import json
import time

def test_updated_prompt():
    """Test the updated prompt that focuses on deterministic answers"""
    
    test_data = {
        "zap_data": "SQL Injection - High - https://example.com\nXSS - Medium - https://example.com\nMissing Anti-clickjacking Header - Medium - https://example.com",
        "num_questions": 5
    }
    
    print("🧪 Testing Updated Prompt (Deterministic Answers)...")
    print("=" * 60)
    print("📋 Expected improvements:")
    print("  ✅ Only mcq, fix_config, and sandbox question types")
    print("  ✅ Deterministic answers (no subjective questions)")
    print("  ✅ Single correct answer for mcq/fix_config")
    print("  ✅ Exact expected outputs for sandbox")
    print("-" * 60)
    
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
            
            print(f"✅ Success! Generated {len(questions)} questions")
            
            # Validate question types
            valid_types = ['mcq', 'fix_config', 'sandbox']
            invalid_types = []
            single_answers = 0
            multiple_answers = 0
            
            for i, q in enumerate(questions):
                exercise_type = q.get('exercise_type', '')
                answer_key = q.get('answer_key', [])
                
                if exercise_type not in valid_types:
                    invalid_types.append(f"Question {i+1}: {exercise_type}")
                
                if exercise_type in ['mcq', 'fix_config']:
                    if len(answer_key) == 1:
                        single_answers += 1
                    else:
                        multiple_answers += 1
            
            print(f"\n📊 Validation Results:")
            print(f"  ✅ Valid question types: {len(questions) - len(invalid_types)}/{len(questions)}")
            print(f"  ✅ Single answers (mcq/fix_config): {single_answers}")
            print(f"  ❌ Multiple answers (should be 0): {multiple_answers}")
            
            if invalid_types:
                print(f"  ❌ Invalid types found: {invalid_types}")
            
            # Show sample questions
            print(f"\n🎯 Sample Questions:")
            for i, q in enumerate(questions[:3], 1):
                print(f"\n{i}. {q.get('title', 'N/A')}")
                print(f"   Type: {q.get('exercise_type', 'N/A')}")
                print(f"   Difficulty: {q.get('difficulty', 'N/A')}")
                print(f"   Answers: {len(q.get('answer_key', []))} answer(s)")
                if q.get('exercise_type') in ['mcq', 'fix_config']:
                    print(f"   Answer: {q.get('answer_key', [])[0] if q.get('answer_key') else 'None'}")
            
            # Show full JSON for first question
            if questions:
                print(f"\n📋 Full JSON for Question 1:")
                print(json.dumps(questions[0], indent=2, ensure_ascii=False))
            
            return len(invalid_types) == 0 and multiple_answers == 0
            
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_updated_prompt()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 Test PASSED! Updated prompt is working correctly.")
        print("✅ All questions have deterministic answers")
        print("✅ No subjective or open-ended questions")
    else:
        print("❌ Test FAILED! Check the validation results above.")
    print(f"{'='*60}")
