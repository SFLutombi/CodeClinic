'use client';

import { useState } from 'react';
import { useUser, useSession } from '@clerk/nextjs';
import QuestionCard from '@/components/QuestionCard';

interface Question {
  vuln_type: string;
  title: string;
  short_explain: string;
  exercise_type: 'mcq' | 'fix_config' | 'sandbox';
  exercise_prompt: string;
  choices: Array<{ id: string; text: string }>;
  answer_key: string[];
  hints: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  xp: number;
  badge: string;
}

interface VulnerabilityGuideEntry {
  name: string;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  category: string;
  description: string;
  howItArises: string[];
  exploitationMethods: string[];
  realWorldExamples: string[];
  preventionMethods: string[];
  codeExamples: {
    vulnerable: string;
    secure: string;
  };
  relatedQuestions: string[];
  quizAnswers: {
    keyConcepts: string[];
    preventionMethods: string[];
    codeExamples: {
      vulnerable: string;
      secure: string;
    };
    securityHeaders: string[];
    attackVectors: string[];
  };
}

interface GeminiResponse {
  questions: Question[];
  vulnerability_guide: VulnerabilityGuideEntry[];
  scan_id?: string;
  saved_to_database?: boolean;
  database_error?: string;
}

interface GameStats {
  totalQuestions: number;
  correctAnswers: number;
  totalXp: number;
  badgesEarned: string[];
}

export default function GeminiQuestionsPage() {
  const { user, isLoaded } = useUser();
  const { session } = useSession();
  const [zapData, setZapData] = useState('');
  const [numQuestions, setNumQuestions] = useState<number | string>(20);
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [vulnerabilityGuide, setVulnerabilityGuide] = useState<VulnerabilityGuideEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showGuide, setShowGuide] = useState(false);
  const [gameStats, setGameStats] = useState<GameStats>({
    totalQuestions: 0,
    correctAnswers: 0,
    totalXp: 0,
    badgesEarned: []
  });
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);

  const handleGenerateQuestions = async () => {
    if (!zapData.trim()) {
      setError('Please enter ZAP data');
      return;
    }

    // Check if user is loaded and authenticated
    if (!isLoaded) {
      setError('Loading user information...');
      return;
    }

    if (!user) {
      setError('Please sign in to generate questions');
      return;
    }

    setLoading(true);
    setError('');
    setQuestions([]);

    try {
      // Get session token for authentication
      const token = await session?.getToken();
      
      // Prepare user data with better error handling
      const userData = {
        user_id: user.id,
        user_email: user.emailAddresses?.[0]?.emailAddress || user.primaryEmailAddress?.emailAddress || null,
        user_username: user.username || user.firstName || 'User',
        user_full_name: user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'User',
        user_avatar_url: user.imageUrl || null,
      };

      // Debug: Log detailed Clerk user data
      console.log('Detailed Clerk user data:', {
        id: user.id,
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        fullName: user.fullName,
        emailAddresses: user.emailAddresses,
        primaryEmailAddress: user.primaryEmailAddress,
        imageUrl: user.imageUrl
      });
      console.log('Sending user data:', userData); // Debug log

      const response = await fetch('http://localhost:8000/generate-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          zap_data: zapData,
          num_questions: numQuestions,
          website_url: websiteUrl || 'Unknown',
          ...userData,
          save_to_db: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate questions');
      }

      const data: GeminiResponse = await response.json();
      setQuestions(data.questions);
      setVulnerabilityGuide(data.vulnerability_guide);
      setGameStats({
        totalQuestions: data.questions.length,
        correctAnswers: 0,
        totalXp: 0,
        badgesEarned: []
      });
      setCurrentQuestionIndex(0);
      setGameStarted(true);
      setShowGuide(true); // Show guide first
      
      // Show database save status
      if (data.saved_to_database) {
        console.log(`✅ Questions saved to database with scan ID: ${data.scan_id}`);
      } else {
        console.log('⚠️ Questions not saved to database');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (isCorrect: boolean, xpEarned: number, timeTaken: number) => {
    setGameStats(prev => ({
      ...prev,
      correctAnswers: prev.correctAnswers + (isCorrect ? 1 : 0),
      totalXp: prev.totalXp + xpEarned,
      badgesEarned: isCorrect ? [...prev.badgesEarned, questions[currentQuestionIndex].badge] : prev.badgesEarned
    }));

    // Save individual question response to database if user is authenticated
    if (user && session) {
      try {
        const token = await session.getToken();
        const response = await fetch('http://localhost:8000/save-question-response', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({
            question_id: questions[currentQuestionIndex].id || `q_${currentQuestionIndex}`,
            user_answer: isCorrect ? 'correct' : 'incorrect',
            is_correct: isCorrect,
            xp_earned: xpEarned,
            time_taken: Math.floor(timeTaken),
            user_id: user.id
          })
        });
        
        if (response.ok) {
          console.log(`✅ Question response saved for question ${currentQuestionIndex + 1}`);
        }
      } catch (err) {
        console.error('Failed to save question response:', err);
      }
    }
  };

  const goToQuestion = (index: number) => {
    if (index >= 0 && index < questions.length) {
      setCurrentQuestionIndex(index);
    }
  };

  const goToNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const completeGame = async () => {
    console.log('completeGame function called!', {
      currentQuestionIndex,
      questionsLength: questions.length,
      gameStats
    });
    
    // Save final game results to database if user is authenticated
    if (user && session && gameStats.totalXp > 0) {
      try {
        const token = await session.getToken();
        const response = await fetch('http://localhost:8000/save-question-response', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
          },
          body: JSON.stringify({
            question_id: 'game_complete',
            user_answer: 'completed',
            is_correct: true,
            xp_earned: 0, // No additional XP for completion
            time_taken: 0
          })
        });
        
        if (response.ok) {
          console.log('✅ Game completion saved to database');
        }
      } catch (err) {
        console.error('Failed to save game completion:', err);
      }
    }
    
    console.log('Setting currentQuestionIndex to:', questions.length);
    setCurrentQuestionIndex(questions.length);
  };

  const resetGame = () => {
    setQuestions([]);
    setVulnerabilityGuide([]);
    setGameStats({
      totalQuestions: 0,
      correctAnswers: 0,
      totalXp: 0,
      badgesEarned: []
    });
    setCurrentQuestionIndex(0);
    setGameStarted(false);
    setShowGuide(false);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'High':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };


  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🧠 Cybersecurity Questions Generator
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            Generate training questions from ZAP scan data using AI
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-2xl mx-auto mb-4">
            <p className="text-blue-800">
              💡 <strong>Ready to learn?</strong> Generate questions from your ZAP scan data below!
            </p>
          </div>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            📝 Input ZAP Data
          </h2>
          
          
          <div className="space-y-4">
            <div>
              <label htmlFor="websiteUrl" className="block text-sm font-medium text-gray-700 mb-2">
                Website URL (Optional)
              </label>
              <input
                type="url"
                id="websiteUrl"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="numQuestions" className="block text-sm font-medium text-gray-700 mb-2">
                Number of Questions (1-50)
              </label>
              <input
                type="number"
                id="numQuestions"
                min="1"
                max="50"
                value={numQuestions}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '') {
                    setNumQuestions('');
                  } else {
                    const num = parseInt(value);
                    if (!isNaN(num) && num >= 1 && num <= 50) {
                      setNumQuestions(num);
                    }
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="zapData" className="block text-sm font-medium text-gray-700 mb-2">
                ZAP Scan Data
              </label>
              <textarea
                id="zapData"
                rows={10}
                value={zapData}
                onChange={(e) => setZapData(e.target.value)}
                placeholder="Paste your ZAP scan results here..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={handleGenerateQuestions}
              disabled={loading || !user || !isLoaded}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '🔄 Generating Questions...' : 
               !user ? '🔒 Please Sign In First' : 
               '🚀 Generate Questions'}
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
              ❌ {error}
            </div>
          )}
        </div>

        {/* Dynamic Vulnerability Guide */}
        {showGuide && vulnerabilityGuide.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">
                📚 Vulnerability Guide for Your Scan
              </h2>
              <button
                onClick={() => setShowGuide(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                🎮 Start Quiz
              </button>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800">
                💡 <strong>Study these vulnerabilities found in your scan before starting the quiz!</strong><br/>
                This guide contains detailed explanations that will help you answer the quiz questions correctly.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {vulnerabilityGuide.map((vuln, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900">{vuln.name}</h3>
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(vuln.severity)}`}>
                        {vuln.severity}
                      </span>
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {vuln.category}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">📝 Description</h4>
                      <p className="text-gray-700 text-sm">{vuln.description}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">🔍 How It Arises</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                        {vuln.howItArises.slice(0, 3).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">🛡️ Prevention Methods</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                        {vuln.preventionMethods.slice(0, 3).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {vuln.realWorldExamples.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">🌍 Example Attack</h4>
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <code className="text-sm text-red-800 font-mono">
                            {vuln.realWorldExamples[0]}
                          </code>
                        </div>
                      </div>
                    )}

                    {vuln.codeExamples && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">💻 Secure Code Example</h4>
                        <pre className="bg-green-50 border border-green-200 rounded p-2 text-xs text-green-800 overflow-x-auto">
                          <code>{vuln.codeExamples.secure}</code>
                        </pre>
                      </div>
                    )}

                    {vuln.quizAnswers && (
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">🎯 Study Guide for Quiz</h4>
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                          {vuln.quizAnswers.keyConcepts && vuln.quizAnswers.keyConcepts.length > 0 && (
                            <div className="mb-3">
                              <h5 className="font-medium text-yellow-800 mb-1">🔑 Key Concepts:</h5>
                              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                                {vuln.quizAnswers.keyConcepts.map((concept, i) => (
                                  <li key={i}>{concept}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {vuln.quizAnswers.securityHeaders && vuln.quizAnswers.securityHeaders.length > 0 && (
                            <div className="mb-3">
                              <h5 className="font-medium text-yellow-800 mb-1">🛡️ Security Headers:</h5>
                              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                                {vuln.quizAnswers.securityHeaders.map((header, i) => (
                                  <li key={i}>{header}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {vuln.quizAnswers.attackVectors && vuln.quizAnswers.attackVectors.length > 0 && (
                            <div className="mb-3">
                              <h5 className="font-medium text-yellow-800 mb-1">⚔️ Attack Vectors:</h5>
                              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                                {vuln.quizAnswers.attackVectors.slice(0, 3).map((vector, i) => (
                                  <li key={i}>{vector}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {vuln.quizAnswers.preventionMethods && vuln.quizAnswers.preventionMethods.length > 0 && (
                            <div>
                              <h5 className="font-medium text-yellow-800 mb-1">🔒 Prevention Methods:</h5>
                              <ul className="list-disc list-inside space-y-1 text-sm text-yellow-700">
                                {vuln.quizAnswers.preventionMethods.slice(0, 3).map((method, i) => (
                                  <li key={i}>{method}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Game Stats */}
        {gameStarted && !showGuide && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold text-gray-900">
                🎮 Game Progress
              </h2>
              <button
                onClick={resetGame}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                🔄 New Game
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{gameStats.totalXp}</div>
                <div className="text-sm text-blue-800">Total XP</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{gameStats.correctAnswers}</div>
                <div className="text-sm text-green-800">Correct</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{gameStats.badgesEarned.length}</div>
                <div className="text-sm text-purple-800">Badges</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {currentQuestionIndex + 1}/{gameStats.totalQuestions}
                </div>
                <div className="text-sm text-orange-800">Progress</div>
              </div>
            </div>

            {/* Question Navigation */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">📋 Question Navigation:</h3>
              <div className="flex flex-wrap gap-2 mb-4">
                {questions.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => goToQuestion(index)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      index === currentQuestionIndex
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
              
              <div className="flex justify-between items-center">
                <button
                  onClick={goToPreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  ← Previous
                </button>
                
                <div className="text-center">
                  <span className="text-sm text-gray-600">
                    Question {currentQuestionIndex + 1} of {questions.length}
                  </span>
                  <div className="text-xs text-gray-600 mt-1">
                    💡 Use ← → arrow keys to navigate
                  </div>
                  <button
                    onClick={() => setShowGuide(true)}
                    className="mt-2 px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-colors"
                  >
                    📚 Show Guide
                  </button>
                </div>
                
                <button
                  onClick={goToNextQuestion}
                  disabled={currentQuestionIndex === questions.length - 1}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>

            {gameStats.badgesEarned.length > 0 && (
              <div className="mt-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">🏆 Badges Earned:</h3>
                <div className="flex flex-wrap gap-2">
                  {gameStats.badgesEarned.map((badge, index) => (
                    <span key={index} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                      {badge}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Current Question */}
        {gameStarted && questions.length > 0 && currentQuestionIndex < questions.length && (
          <div className="mb-8">
            <QuestionCard
              question={questions[currentQuestionIndex]}
              questionNumber={currentQuestionIndex + 1}
              onAnswer={handleAnswer}
              onNext={goToNextQuestion}
              onPrevious={goToPreviousQuestion}
            />
          </div>
        )}

        {/* Complete All Questions Button */}
        {gameStarted && questions.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8 text-center border-2 border-green-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🎯 Ready to finish?
            </h3>
            <p className="text-gray-600 mb-4">
              You can continue answering questions or complete the game now.
            </p>
            <button
              onClick={() => {
                console.log('Finish button clicked!');
                alert('Finish button clicked! Completing game...');
                completeGame();
              }}
              className="px-8 py-4 bg-green-600 text-white text-lg font-bold rounded-lg hover:bg-green-700 transition-colors cursor-pointer border-2 border-green-600 hover:border-green-700 shadow-lg hover:shadow-xl"
              style={{ 
                pointerEvents: 'auto',
                zIndex: 10,
                position: 'relative',
                minWidth: '200px'
              }}
            >
              ✅ Complete Game
            </button>
            <div className="mt-2 text-xs text-gray-600">
              Click this button to finish the quiz at any time
            </div>
          </div>
        )}

        {/* Game Complete */}
        {gameStarted && currentQuestionIndex >= questions.length && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Game Complete!
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-blue-50 p-6 rounded-lg">
                <div className="text-3xl font-bold text-blue-600 mb-2">{gameStats.totalXp}</div>
                <div className="text-blue-800 font-medium">Total XP Earned</div>
              </div>
              <div className="bg-green-50 p-6 rounded-lg">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {Math.round((gameStats.correctAnswers / gameStats.totalQuestions) * 100)}%
                </div>
                <div className="text-green-800 font-medium">Accuracy</div>
              </div>
              <div className="bg-purple-50 p-6 rounded-lg">
                <div className="text-3xl font-bold text-purple-600 mb-2">{gameStats.badgesEarned.length}</div>
                <div className="text-purple-800 font-medium">Badges Unlocked</div>
              </div>
            </div>
            
            {gameStats.badgesEarned.length > 0 && (
              <div className="mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">🏆 Your Badges:</h3>
                <div className="flex flex-wrap justify-center gap-3">
                  {gameStats.badgesEarned.map((badge, index) => (
                    <span key={index} className="px-4 py-2 bg-purple-100 text-purple-800 rounded-full font-medium">
                      {badge}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <button
              onClick={resetGame}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              🎮 Play Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
