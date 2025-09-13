'use client';

import { useState } from 'react';

interface Question {
  vuln_type: string;
  title: string;
  short_explain: string;
  exercise_type: string;
  exercise_prompt: string;
  choices: Array<{ id: string; text: string }>;
  answer_key: string[];
  hints: string[];
  difficulty: string;
  xp: number;
  badge: string;
}

interface GeminiResponse {
  questions: Question[];
}

export default function GeminiQuestionsPage() {
  const [zapData, setZapData] = useState('');
  const [numQuestions, setNumQuestions] = useState(20);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getExerciseTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'mcq':
        return 'bg-blue-100 text-blue-800';
      case 'fix_config':
        return 'bg-orange-100 text-orange-800';
      case 'sandbox':
        return 'bg-pink-100 text-pink-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
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

        {/* Results */}
        {questions.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-6">
              🎯 Generated Questions ({questions.length})
            </h2>
            
            <div className="space-y-6">
              {questions.map((question, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {index + 1}. {question.title}
                    </h3>
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(question.difficulty)}`}>
                        {question.difficulty}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getExerciseTypeColor(question.exercise_type)}`}>
                        {question.exercise_type}
                      </span>
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {question.xp} XP
                      </span>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-gray-700 mb-2">
                      <strong>Vulnerability:</strong> {question.vuln_type}
                    </p>
                    <p className="text-gray-600 mb-3">
                      <strong>Explanation:</strong> {question.short_explain}
                    </p>
                    <p className="text-gray-800 font-medium">
                      <strong>Question:</strong> {question.exercise_prompt}
                    </p>
                  </div>

                  {question.choices && question.choices.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-2">Choices:</h4>
                      <div className="space-y-2">
                        {question.choices.map((choice, choiceIndex) => (
                          <div key={choiceIndex} className="flex items-center space-x-2">
                            <span className="font-medium text-blue-600">{choice.id}.</span>
                            <span className="text-gray-700">{choice.text}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Answer:</h4>
                    <p className="text-green-700 font-medium">
                      {question.exercise_type === 'sandbox' 
                        ? question.answer_key.join('\n') 
                        : question.answer_key.join(', ')}
                    </p>
                  </div>

                  {question.hints && question.hints.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-2">Hints:</h4>
                      <ul className="list-disc list-inside space-y-1">
                        {question.hints.map((hint, hintIndex) => (
                          <li key={hintIndex} className="text-gray-600">{hint}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    <span className="text-sm text-gray-500">
                      Badge: <span className="font-medium text-purple-600">{question.badge}</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
