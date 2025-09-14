'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import QuestionCard from '@/components/QuestionCard';

interface Question {
  id: string;
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
  severity: string;
  category: string;
  description: string;
  how_it_arises: string[];
  exploitation_methods: string[];
  real_world_examples: string[];
  prevention_methods: string[];
  code_examples: Record<string, any>;
  quiz_answers: {
    keyConcepts: string[];
    preventionMethods: string[];
    securityHeaders: string[];
    attackVectors: string[];
  };
}

interface QuizData {
  questions: Question[];
  vulnerability_guide: VulnerabilityGuideEntry[];
  website_title: string;
  website_url: string;
  created_by: string;
}

interface GameStats {
  totalQuestions: number;
  correctAnswers: number;
  totalXP: number;
  badgesEarned: string[];
  timeStarted: number;
}

export default function QuizPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isLoaded } = useUser();
  const scanId = params.scanId as string;

  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [vulnerabilityGuide, setVulnerabilityGuide] = useState<VulnerabilityGuideEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [gameStats, setGameStats] = useState<GameStats>({
    totalQuestions: 0,
    correctAnswers: 0,
    totalXP: 0,
    badgesEarned: [],
    timeStarted: Date.now()
  });
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [gameCompleted, setGameCompleted] = useState(false);
  const [questionResponses, setQuestionResponses] = useState<Map<string, any>>(new Map());
  const [quizAttemptId, setQuizAttemptId] = useState<string | null>(null);

  useEffect(() => {
    if (scanId) {
      fetchQuizData();
    }
  }, [scanId]);

  const fetchQuizData = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await fetch(`http://localhost:8000/scan/${scanId}/questions`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch quiz data: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.questions && data.questions.length > 0) {
        setQuizData(data);
        setQuestions(data.questions);
        setVulnerabilityGuide(data.vulnerability_guide || []);
        setGameStats(prev => ({
          ...prev,
          totalQuestions: data.questions.length
        }));
        setShowGuide(true);
      } else {
        setError('No questions found for this quiz');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load quiz data');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = async (questionId: string, isCorrect: boolean, xpEarned: number, timeTaken: number, badge?: string) => {
    // Update game stats
    setGameStats(prev => ({
      ...prev,
      correctAnswers: prev.correctAnswers + (isCorrect ? 1 : 0),
      totalXP: prev.totalXP + xpEarned,
      badgesEarned: (isCorrect && badge) ? [...prev.badgesEarned, badge] : prev.badgesEarned
    }));

    // Store the response
    const response = {
      questionId,
      isCorrect,
      xpEarned,
      timeTaken,
      badge,
      answeredAt: new Date().toISOString()
    };
    
    setQuestionResponses(prev => new Map(prev.set(questionId, response)));

    // Save individual question response to database
    if (user && quizAttemptId) {
      try {
        await fetch('http://localhost:8000/save-question-response', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            quiz_attempt_id: quizAttemptId,
            question_id: questionId,
            user_answer: response,
            is_correct: isCorrect,
            xp_earned: xpEarned,
            time_taken: Math.floor(timeTaken),
            user_id: user.id
          })
        });
        console.log(`✅ Question response saved for question ${questionId}`);
      } catch (err) {
        console.error('Failed to save question response:', err);
      }
    }
  };

  const goToNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      // Quiz completed
      setGameCompleted(true);
      saveQuizAttempt();
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const goToQuestion = (index: number) => {
    if (index >= 0 && index < questions.length) {
      setCurrentQuestionIndex(index);
    }
  };

  const saveQuizAttempt = async () => {
    if (!user || !quizData) return;

    try {
      const attemptData = {
        user_id: user.id,
        website_scan_id: scanId,
        total_questions: gameStats.totalQuestions,
        correct_answers: gameStats.correctAnswers,
        total_xp: gameStats.totalXP,
        badges_earned: gameStats.badgesEarned,
        time_taken: Math.floor((Date.now() - gameStats.timeStarted) / 1000)
      };

      await fetch('http://localhost:8000/save-quiz-attempt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(attemptData)
      });

      console.log('Quiz attempt saved successfully');
    } catch (err) {
      console.error('Failed to save quiz attempt:', err);
    }
  };

  const resetGame = () => {
    setCurrentQuestionIndex(0);
    setGameStarted(false);
    setShowGuide(true);
    setGameCompleted(false);
    setGameStats({
      totalQuestions: questions.length,
      correctAnswers: 0,
      totalXP: 0,
      badgesEarned: [],
      timeStarted: Date.now()
    });
  };

  const startQuiz = async () => {
    setShowGuide(false);
    setGameStarted(true);
    
    // Create quiz attempt when user starts
    if (user && isLoaded) {
      try {
        // Debug: Log user data from Clerk
        console.log('Clerk user data:', {
          id: user.id,
          username: user.username,
          firstName: user.firstName,
          lastName: user.lastName,
          fullName: user.fullName,
          emailAddresses: user.emailAddresses,
          primaryEmailAddress: user.primaryEmailAddress,
          imageUrl: user.imageUrl
        });
        
        const response = await fetch('http://localhost:8000/create-quiz-attempt', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: user.id,
            user_email: user.emailAddresses?.[0]?.emailAddress || user.primaryEmailAddress?.emailAddress || null,
            user_username: user.username || user.firstName || 'User',
            user_full_name: user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'User',
            user_avatar_url: user.imageUrl || null,
            website_scan_id: scanId,
            total_questions: questions.length
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          setQuizAttemptId(data.attempt_id);
          console.log('✅ Quiz attempt created:', data.attempt_id);
        } else {
          console.error('Failed to create quiz attempt:', response.status, response.statusText);
        }
      } catch (err) {
        console.error('Failed to create quiz attempt:', err);
        // Don't prevent quiz from starting if attempt creation fails
        console.log('Continuing quiz without attempt tracking...');
      }
    } else {
      console.warn('User not authenticated, starting quiz without attempt tracking');
    }
  };

  if (loading || !isLoaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading quiz...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-blue-600 text-6xl mb-4">🔐</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h1>
          <p className="text-gray-600 mb-4">Please sign in to play this quiz.</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Quiz</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/explore')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Explore
          </button>
        </div>
      </div>
    );
  }

  if (!quizData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 text-6xl mb-4">📝</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Quiz Not Found</h1>
          <p className="text-gray-600 mb-4">The quiz you're looking for doesn't exist.</p>
          <button
            onClick={() => router.push('/explore')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Explore
          </button>
        </div>
      </div>
    );
  }

  // Show vulnerability guide first
  if (showGuide && !gameStarted) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🛡️ Security Guide: {quizData.website_title || 'Unknown Website'}
            </h1>
            <p className="text-gray-600">
              Learn about the vulnerabilities found in this website before taking the quiz
            </p>
          </div>

          {/* Vulnerability Guide */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              📚 Vulnerability Information
            </h2>
            <div className="space-y-6">
              {vulnerabilityGuide.map((entry, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {entry.name} ({entry.severity})
                  </h3>
                  <p className="text-gray-700 mb-3">{entry.description}</p>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">How it arises:</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {(entry.how_it_arises || []).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Prevention methods:</h4>
                      <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                        {(entry.prevention_methods || []).map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {entry.quiz_answers && entry.quiz_answers.keyConcepts && (
                    <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2">Key Concepts:</h4>
                      <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
                        {(entry.quiz_answers.keyConcepts || []).map((concept, i) => (
                          <li key={i}>{concept}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Start Quiz Button */}
          <div className="text-center">
            <button
              onClick={startQuiz}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg"
            >
              🎮 Start Quiz ({questions.length} questions)
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show game completion
  if (gameCompleted) {
    const accuracy = Math.round((gameStats.correctAnswers / gameStats.totalQuestions) * 100);
    const timeTaken = Math.floor((Date.now() - gameStats.timeStarted) / 1000);
    const minutes = Math.floor(timeTaken / 60);
    const seconds = timeTaken % 60;

    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Quiz Completed!</h1>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{accuracy}%</div>
                <div className="text-sm text-blue-800">Accuracy</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{gameStats.totalXP}</div>
                <div className="text-sm text-green-800">XP Earned</div>
              </div>
            </div>

            <div className="text-gray-600 mb-6">
              <p>Correct: {gameStats.correctAnswers}/{gameStats.totalQuestions}</p>
              <p>Time: {minutes}m {seconds}s</p>
            </div>

            {gameStats.badgesEarned.length > 0 && (
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-2">Badges Earned:</h3>
                <div className="flex flex-wrap justify-center gap-2">
                  {gameStats.badgesEarned.map((badge, index) => (
                    <span key={index} className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
                      🏆 {badge}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <button
                onClick={resetGame}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                🔄 Play Again
              </button>
              <button
                onClick={() => router.push('/explore')}
                className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                📚 Explore More Quizzes
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show current question
  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold text-gray-900">
              🎮 {quizData.website_title || 'Security Quiz'}
            </h1>
            <button
              onClick={() => router.push('/explore')}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              ← Back to Explore
            </button>
          </div>
          
          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
              <span>{gameStats.correctAnswers} correct • {gameStats.totalXP} XP</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between">
            <button
              onClick={goToPreviousQuestion}
              disabled={currentQuestionIndex === 0}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              ← Previous
            </button>
            
            <div className="flex space-x-2">
              {questions.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToQuestion(index)}
                  className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                    index === currentQuestionIndex
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>

            <button
              onClick={goToNextQuestion}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {currentQuestionIndex === questions.length - 1 ? 'Finish' : 'Next →'}
            </button>
          </div>
        </div>


        {/* Question */}
        <QuestionCard
          question={currentQuestion}
          questionNumber={currentQuestionIndex + 1}
          onAnswer={(isCorrect, xpEarned, timeTaken) => handleAnswer(currentQuestion.id, isCorrect, xpEarned, timeTaken, currentQuestion.badge)}
          onNext={goToNextQuestion}
        />
      </div>
    </div>
  );
}