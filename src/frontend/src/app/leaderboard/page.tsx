'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';

interface LeaderboardEntry {
  user_id: string;
  username: string;
  full_name: string;
  total_xp: number;
  total_questions: number;
  correct_answers: number;
  accuracy: number;
  badges_earned: string[];
}

export default function LeaderboardPage() {
  const { user } = useUser();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/leaderboard?limit=20');
      
      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }
      
      const data = await response.json();
      setLeaderboard(data.leaderboard || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (index: number) => {
    switch (index) {
      case 0:
        return '🥇';
      case 1:
        return '🥈';
      case 2:
        return '🥉';
      default:
        return `#${index + 1}`;
    }
  };

  const getRankColor = (index: number) => {
    switch (index) {
      case 0:
        return 'bg-yellow-50 border-yellow-200';
      case 1:
        return 'bg-gray-50 border-gray-200';
      case 2:
        return 'bg-orange-50 border-orange-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading leaderboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Leaderboard</h2>
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchLeaderboard}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🏆 Cybersecurity Leaderboard
          </h1>
          <p className="text-lg text-gray-600">
            Top performers in cybersecurity knowledge and skills
          </p>
        </div>

        {/* Current User Stats */}
        {user && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-blue-900 mb-4">Your Progress</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {leaderboard.find(entry => entry.user_id === user.id)?.total_xp || 0}
                </div>
                <div className="text-sm text-blue-800">Total XP</div>
              </div>
              <div className="bg-white rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-600">
                  {leaderboard.find(entry => entry.user_id === user.id)?.correct_answers || 0}
                </div>
                <div className="text-sm text-green-800">Correct Answers</div>
              </div>
              <div className="bg-white rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {leaderboard.find(entry => entry.user_id === user.id)?.badges_count || 0}
                </div>
                <div className="text-sm text-purple-800">Badges Earned</div>
              </div>
            </div>
          </div>
        )}

        {/* Leaderboard */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Top Performers</h2>
          </div>
          
          {leaderboard.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Data Yet
              </h3>
              <p className="text-gray-600">
                Be the first to take a quiz and appear on the leaderboard!
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {leaderboard.map((entry, index) => (
                <div
                  key={entry.user_id}
                  className={`p-6 ${getRankColor(index)} ${
                    user?.id === entry.user_id ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-bold text-gray-700 min-w-[60px]">
                        {getRankIcon(index)}
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {entry.username?.charAt(0).toUpperCase() || 
                             entry.full_name?.charAt(0).toUpperCase() || 
                             '?'}
                          </span>
                        </div>
                        
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {entry.full_name || entry.username || 'Anonymous'}
                          </h3>
                          {entry.username && entry.username !== entry.full_name && (
                            <p className="text-sm text-gray-500">@{entry.username}</p>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <div className="text-xl font-bold text-blue-600">
                          {entry.total_xp.toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-500">XP</div>
                      </div>
                      
                      <div className="text-center">
                        <div className="text-lg font-semibold text-purple-600">
                          {entry.badges_earned.length}
                        </div>
                        <div className="text-xs text-gray-500">Badges</div>
                      </div>
                    </div>
                  </div>
                  
                  
                  {/* Badges display for top 3 */}
                  {index < 3 && entry.badges_earned.length > 0 && (
                    <div className="mt-3">
                      <div className="text-sm text-gray-600 mb-2">Badges Earned:</div>
                      <div className="flex flex-wrap gap-1">
                        {entry.badges_earned.map((badge, badgeIndex) => (
                          <span
                            key={badgeIndex}
                            className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full"
                          >
                            {badge}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Call to Action */}
        <div className="mt-8 text-center">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ready to climb the leaderboard?
            </h3>
            <p className="text-gray-600 mb-4">
              Take cybersecurity quizzes to earn XP, badges, and improve your ranking!
            </p>
            <div className="flex justify-center space-x-4">
              <a
                href="/gemini-questions"
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                🧠 Take Quiz
              </a>
              <a
                href="/explore"
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                🔍 Explore Scans
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
