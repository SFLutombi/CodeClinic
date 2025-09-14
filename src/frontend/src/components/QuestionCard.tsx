'use client';

import { useState, useEffect } from 'react';

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

interface QuestionCardProps {
  question: Question;
  questionNumber: number;
  onAnswer: (isCorrect: boolean, xpEarned: number, timeTaken: number) => void;
  onNext?: () => void;
  onPrevious?: () => void;
}

export default function QuestionCard({ question, questionNumber, onAnswer, onNext, onPrevious }: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [customAnswer, setCustomAnswer] = useState<string>('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [xpEarned, setXpEarned] = useState(0);
  const [showHints, setShowHints] = useState(false);
  const [hintsRevealed, setHintsRevealed] = useState(0);
  const [startTime] = useState(Date.now());
  const [timeTaken, setTimeTaken] = useState(0);
  // Reset state when question changes (questionNumber is the key)
  useEffect(() => {
    setSelectedAnswer('');
    setCustomAnswer('');
    setIsSubmitted(false);
    setIsCorrect(null);
    setXpEarned(0);
    setShowHints(false);
    setHintsRevealed(0);
    setTimeTaken(0);
  }, [questionNumber]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'ArrowLeft' && onPrevious) {
        onPrevious();
      } else if (event.key === 'ArrowRight' && onNext) {
        onNext();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [onNext, onPrevious]);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'advanced':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getExerciseTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'mcq':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'fix_config':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'sandbox':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleSubmit = () => {
    if (isSubmitted) return;

    const endTime = Date.now();
    const timeElapsed = (endTime - startTime) / 1000;
    setTimeTaken(timeElapsed);

    let correct = false;
    let answerToCheck = '';

    if (question.exercise_type === 'sandbox') {
      answerToCheck = customAnswer.trim();
    } else {
      answerToCheck = selectedAnswer;
    }

    // Check if answer matches (case-insensitive for sandbox)
    // If no answer provided, it's automatically incorrect
    if (answerToCheck.length === 0) {
      correct = false;
    } else if (question.exercise_type === 'sandbox') {
      correct = question.answer_key.some(key => 
        key.toLowerCase().trim() === answerToCheck.toLowerCase()
      );
    } else {
      correct = question.answer_key.includes(answerToCheck);
    }

    setIsCorrect(correct);
    setIsSubmitted(true);

    // Calculate XP - only give XP for correct answers
    let baseXp = correct ? question.xp : 0;
    let speedBonus = 0;
    
    if (correct && timeElapsed <= 30) {
      speedBonus = Math.floor(baseXp * 0.2); // 20% bonus for quick correct answers
    }
    
    const totalXp = baseXp + speedBonus;
    setXpEarned(totalXp);

    onAnswer(correct, totalXp, timeElapsed);
  };

  const toggleHints = () => {
    if (!showHints) {
      setShowHints(true);
      setHintsRevealed(1);
    } else if (hintsRevealed < question.hints.length) {
      setHintsRevealed(hintsRevealed + 1);
    }
  };

  const canSubmit = () => {
    // Simple logic: can submit as long as not already submitted
    return !isSubmitted;
  };

  const getCardBorderColor = () => {
    if (!isSubmitted) return 'border-gray-200';
    if (isCorrect) return 'border-green-500';
    return 'border-red-500';
  };

  const getCardBgColor = () => {
    if (!isSubmitted) return 'bg-white';
    if (isCorrect) return 'bg-green-50';
    return 'bg-red-50';
  };

  return (
    <div className={`border-2 rounded-lg p-6 transition-all duration-300 ${getCardBorderColor()} ${getCardBgColor()}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className="text-2xl font-bold text-gray-600">#{questionNumber}</span>
          <div className="flex space-x-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getDifficultyColor(question.difficulty)}`}>
              {question.difficulty}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getExerciseTypeColor(question.exercise_type)}`}>
              {question.exercise_type.toUpperCase()}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-blue-600">{question.xp} XP</div>
          {isSubmitted && (
            <div className="text-sm text-green-600 font-medium">
              +{xpEarned} XP earned
            </div>
          )}
        </div>
      </div>

      {/* Question Title and Explanation */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {question.title}
        </h3>
        <p className="text-gray-600 mb-3">
          <strong>Vulnerability:</strong> {question.vuln_type}
        </p>
        <p className="text-gray-700">
          {question.short_explain}
        </p>
      </div>

      {/* Question Prompt */}
      <div className="mb-6">
        <div className="bg-gray-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
          <p className="text-gray-800 font-medium">
            {question.exercise_prompt}
          </p>
        </div>
      </div>

      {/* Answer Section */}
      <div className="mb-6">
        {question.exercise_type === 'sandbox' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter your answer:
            </label>
            <textarea
              value={customAnswer}
              onChange={(e) => setCustomAnswer(e.target.value)}
              disabled={isSubmitted}
              placeholder="Enter your payload, command, or configuration..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
              rows={4}
            />
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Select your answer:
            </label>
            <div className="space-y-2">
              {question.choices.map((choice) => (
                <button
                  key={choice.id}
                  onClick={() => setSelectedAnswer(choice.id)}
                  disabled={isSubmitted}
                  className={`w-full text-left p-3 rounded-lg border-2 transition-all duration-200 ${
                    selectedAnswer === choice.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${
                    isSubmitted && question.answer_key.includes(choice.id)
                      ? 'border-green-500 bg-green-50'
                      : ''
                  } ${
                    isSubmitted && selectedAnswer === choice.id && !question.answer_key.includes(choice.id)
                      ? 'border-red-500 bg-red-50'
                      : ''
                  } disabled:cursor-not-allowed`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="font-bold text-blue-600">{choice.id}.</span>
                    <span className={`${question.exercise_type === 'fix_config' ? 'font-mono text-sm' : ''}`}>
                      {choice.text}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Hints Section */}
      {question.hints.length > 0 && (
        <div className="mb-6">
          <button
            onClick={toggleHints}
            disabled={isSubmitted}
            className="text-blue-600 hover:text-blue-800 font-medium text-sm disabled:cursor-not-allowed"
          >
            💡 {showHints ? 'Show more hints' : 'Show hints'} ({hintsRevealed}/{question.hints.length})
          </button>
          
          {showHints && (
            <div className="mt-2 space-y-2">
              {question.hints.slice(0, hintsRevealed).map((hint, index) => (
                <div key={index} className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded-r-lg">
                  <p className="text-yellow-800 text-sm">{hint}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Submit Button */}
      <div className="mb-4">
        <button
          onClick={handleSubmit}
          disabled={isSubmitted}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            !isSubmitted
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {isSubmitted ? 'Submitted' : 'Submit Answer'}
        </button>
      </div>

      {/* Feedback Section */}
      {isSubmitted && (
        <div className={`p-4 rounded-lg border-2 ${
          isCorrect 
            ? 'bg-green-100 border-green-300' 
            : 'bg-red-100 border-red-300'
        }`}>
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl">
              {isCorrect ? '✅' : '❌'}
            </span>
            <span className={`font-bold text-lg ${
              isCorrect ? 'text-green-800' : 'text-red-800'
            }`}>
              {isCorrect ? 'Correct!' : 'Incorrect'}
            </span>
          </div>
          
          <div className="space-y-2">
            <p className={`text-sm ${
              isCorrect ? 'text-green-700' : 'text-red-700'
            }`}>
              {isCorrect 
                ? `Great job! You earned ${xpEarned} XP${timeTaken <= 30 ? ' (including speed bonus!)' : ''}.`
                : `The correct answer is: ${question.answer_key.join(', ')}`
              }
            </p>
            
            {isCorrect && question.badge && (
              <div className="bg-purple-100 border border-purple-300 rounded-lg p-2">
                <p className="text-purple-800 text-sm font-medium">
                  🏆 Badge Unlocked: {question.badge}
                </p>
              </div>
            )}
            
            <p className="text-xs text-gray-600">
              Time taken: {timeTaken.toFixed(1)}s
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
