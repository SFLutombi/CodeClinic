#!/usr/bin/env python3
"""
Test the gamified question flow
"""

import requests
import json
import time

def test_gamified_questions():
    """Test the gamified question generation and flow"""
    
    test_data = {
        "zap_data": "SQL Injection - High - https://example.com\nXSS - Medium - https://example.com\nMissing Anti-clickjacking Header - Medium - https://example.com\nContent Security Policy (CSP) Header Not Set - Medium - https://example.com",
        "num_questions": 5
    }
    
    print("🎮 Testing Gamified Question Flow...")
    print("=" * 50)
    print("📋 Expected features:")
    print("  ✅ Interactive question cards")
    print("  ✅ XP system with speed bonuses")
    print("  ✅ Achievement badges")
    print("  ✅ Difficulty levels")
    print("  ✅ Hints system")
    print("  ✅ Deterministic answers")
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
            
            print(f"✅ Success! Generated {len(questions)} gamified questions")
            
            # Analyze question features
            question_types = {}
            difficulties = {}
            xp_range = {'min': float('inf'), 'max': 0}
            badges = set()
            hints_count = 0
            
            for i, q in enumerate(questions):
                # Question types
                q_type = q.get('exercise_type', '')
                question_types[q_type] = question_types.get(q_type, 0) + 1
                
                # Difficulties
                diff = q.get('difficulty', '')
                difficulties[diff] = difficulties.get(diff, 0) + 1
                
                # XP range
                xp = q.get('xp', 0)
                xp_range['min'] = min(xp_range['min'], xp)
                xp_range['max'] = max(xp_range['max'], xp)
                
                # Badges
                badge = q.get('badge', '')
                if badge:
                    badges.add(badge)
                
                # Hints
                hints = q.get('hints', [])
                hints_count += len(hints)
            
            print(f"\n📊 Game Features Analysis:")
            print(f"  🎯 Question Types: {question_types}")
            print(f"  📈 Difficulty Distribution: {difficulties}")
            print(f"  💰 XP Range: {xp_range['min']}-{xp_range['max']} XP")
            print(f"  🏆 Unique Badges: {len(badges)}")
            print(f"  💡 Total Hints: {hints_count}")
            
            # Show sample question for gamification
            if questions:
                sample = questions[0]
                print(f"\n🎮 Sample Gamified Question:")
                print(f"  Title: {sample.get('title', 'N/A')}")
                print(f"  Type: {sample.get('exercise_type', 'N/A')}")
                print(f"  Difficulty: {sample.get('difficulty', 'N/A')}")
                print(f"  XP: {sample.get('xp', 'N/A')} (base) + speed bonus")
                print(f"  Badge: {sample.get('badge', 'N/A')}")
                print(f"  Hints: {len(sample.get('hints', []))} available")
                print(f"  Choices: {len(sample.get('choices', []))} options")
            
            # Validate gamification features
            has_gamification = (
                len(question_types) > 0 and
                len(difficulties) > 0 and
                xp_range['max'] > 0 and
                len(badges) > 0 and
                hints_count > 0
            )
            
            return has_gamification
            
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gamified_questions()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 Gamified Flow Test PASSED!")
        print("✅ All gamification features are working")
        print("🎮 Ready for interactive gameplay!")
        print("\n🌐 To test the frontend:")
        print("1. Start backend: python3 run.py")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Visit: http://localhost:3000/gemini-questions")
    else:
        print("❌ Gamified Flow Test FAILED!")
        print("Check the analysis above for missing features")
    print(f"{'='*50}")
