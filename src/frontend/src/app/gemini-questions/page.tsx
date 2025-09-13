'use client';

import { useState } from 'react';
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

interface GeminiResponse {
  questions: Question[];
}

interface GameStats {
  totalQuestions: number;
  correctAnswers: number;
  totalXp: number;
  badgesEarned: string[];
}

export default function GeminiQuestionsPage() {
  const [zapData, setZapData] = useState('');
  const [numQuestions, setNumQuestions] = useState(20);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
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

    setLoading(true);
    setError('');
    setQuestions([]);

    try {
      const response = await fetch('http://localhost:8000/generate-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          zap_data: zapData,
          num_questions: numQuestions,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate questions');
      }

      const data: GeminiResponse = await response.json();
      setQuestions(data.questions);
      setGameStats({
        totalQuestions: data.questions.length,
        correctAnswers: 0,
        totalXp: 0,
        badgesEarned: []
      });
      setCurrentQuestionIndex(0);
      setGameStarted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (isCorrect: boolean, xpEarned: number, timeTaken: number) => {
    setGameStats(prev => ({
      ...prev,
      correctAnswers: prev.correctAnswers + (isCorrect ? 1 : 0),
      totalXp: prev.totalXp + xpEarned,
      badgesEarned: isCorrect ? [...prev.badgesEarned, questions[currentQuestionIndex].badge] : prev.badgesEarned
    }));
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

  const resetGame = () => {
    setQuestions([]);
    setGameStats({
      totalQuestions: 0,
      correctAnswers: 0,
      totalXp: 0,
      badgesEarned: []
    });
    setCurrentQuestionIndex(0);
    setGameStarted(false);
  };


  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🧠 Cybersecurity Questions Generator
          </h1>
          <p className="text-lg text-gray-600">
            Generate training questions from ZAP scan data using AI
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            📝 Input ZAP Data
          </h2>
          
          <div className="space-y-4">
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
                onChange={(e) => setNumQuestions(parseInt(e.target.value) || 20)}
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
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '🔄 Generating Questions...' : '🚀 Generate Questions'}
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
              ❌ {error}
            </div>
          )}
        </div>

        {/* Game Stats */}
        {gameStarted && (
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
                  <div className="text-xs text-gray-500 mt-1">
                    💡 Use ← → arrow keys to navigate
                  </div>
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
        {gameStarted && currentQuestionIndex < questions.length && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              🎯 Ready to finish?
            </h3>
            <p className="text-gray-600 mb-4">
              You can continue answering questions or complete the game now.
            </p>
            <button
              onClick={() => setCurrentQuestionIndex(questions.length)}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              ✅ Complete Game
            </button>
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
