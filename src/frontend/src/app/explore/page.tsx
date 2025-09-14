'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';

interface PublicScan {
  scan_id: string;
  website_url: string;
  website_title: string;
  scan_date: string;
  created_by_username: string;
  created_by_full_name: string;
  question_count: number;
  difficulties: string[];
  exercise_types: string[];
}

interface Filters {
  difficulty: string;
  exercise_type: string;
  search: string;
}

export default function ExplorePage() {
  const router = useRouter();
  const { user, isLoaded } = useUser();
  const [scans, setScans] = useState<PublicScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState<Filters>({
    difficulty: '',
    exercise_type: '',
    search: ''
  });
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    fetchScans();
  }, [filters, currentPage]);

  const fetchScans = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (filters.difficulty) params.append('difficulty', filters.difficulty);
      if (filters.exercise_type) params.append('exercise_type', filters.exercise_type);
      params.append('limit', '12');
      params.append('offset', (currentPage * 12).toString());
      
      const response = await fetch(`http://localhost:8000/public-scans?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch scans');
      }
      
      const data = await response.json();
      const newScans = data.scans || [];
      
      if (currentPage === 0) {
        setScans(newScans);
      } else {
        setScans(prev => [...prev, ...newScans]);
      }
      
      setHasMore(newScans.length === 12);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(0);
  };

  const clearFilters = () => {
    setFilters({
      difficulty: '',
      exercise_type: '',
      search: ''
    });
    setCurrentPage(0);
  };

  const loadMore = () => {
    setCurrentPage(prev => prev + 1);
  };

  const startQuiz = (scanId: string) => {
    router.push(`/quiz/${scanId}`);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
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

  const getExerciseTypeIcon = (type: string) => {
    switch (type) {
      case 'mcq':
        return '📝';
      case 'fix_config':
        return '⚙️';
      case 'sandbox':
        return '💻';
      default:
        return '❓';
    }
  };

  const filteredScans = scans.filter(scan => {
    if (filters.search) {
      return scan.website_title.toLowerCase().includes(filters.search.toLowerCase()) ||
             scan.website_url.toLowerCase().includes(filters.search.toLowerCase()) ||
             scan.created_by_username?.toLowerCase().includes(filters.search.toLowerCase());
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🔍 Explore Cybersecurity Scans
          </h1>
          <p className="text-lg text-gray-600">
            Discover and practice with real-world vulnerability assessments
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Filters</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search
              </label>
              <input
                type="text"
                placeholder="Search by website name..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Difficulty */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <select
                value={filters.difficulty}
                onChange={(e) => handleFilterChange('difficulty', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Difficulties</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            {/* Exercise Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question Type
              </label>
              <select
                value={filters.exercise_type}
                onChange={(e) => handleFilterChange('exercise_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="mcq">Multiple Choice</option>
                <option value="fix_config">Fix Configuration</option>
                <option value="sandbox">Sandbox</option>
              </select>
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8 text-center">
            <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Scans</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={() => {
                setError('');
                fetchScans();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && scans.length === 0 && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading scans...</p>
          </div>
        )}

        {/* Scans Grid */}
        {!loading && filteredScans.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {filteredScans.map((scan) => (
              <div key={scan.scan_id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
                <div className="p-6">
                  {/* Website URL */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">
                      {scan.website_url}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {new Date(scan.scan_date).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Website Title */}
                  <div className="mb-4">
                    <p className="text-sm text-gray-600">
                      Website: <span className="font-medium">{scan.website_title || 'Unknown Website'}</span>
                    </p>
                    <p className="text-xs text-gray-600">
                      Created by {scan.created_by_full_name || scan.created_by_username || 'Anonymous'}
                    </p>
                  </div>

                  {/* Stats */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">
                        {scan.question_count} questions
                      </span>
                      <span className="text-gray-600">
                        {scan.difficulties.length} difficulty levels
                      </span>
                    </div>
                  </div>

                  {/* Difficulties */}
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-2">
                      {scan.difficulties.map((difficulty) => (
                        <span
                          key={difficulty}
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(difficulty)}`}
                        >
                          {difficulty}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Exercise Types */}
                  <div className="mb-6">
                    <div className="flex flex-wrap gap-2">
                      {scan.exercise_types.map((type) => (
                        <span
                          key={type}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium"
                        >
                          {getExerciseTypeIcon(type)} {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Action Button */}
                  <button
                    onClick={() => startQuiz(scan.scan_id)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    🎮 Start Quiz
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredScans.length === 0 && !error && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No Scans Found
            </h3>
            <p className="text-gray-600 mb-4">
              {filters.difficulty || filters.exercise_type || filters.search
                ? 'Try adjusting your filters to see more results.'
                : 'No public scans are available yet. Be the first to create one!'}
            </p>
            {filters.difficulty || filters.exercise_type || filters.search ? (
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Clear Filters
              </button>
            ) : (
              <a
                href="/gemini-questions"
                className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create First Scan
              </a>
            )}
          </div>
        )}

        {/* Load More Button */}
        {!loading && hasMore && filteredScans.length > 0 && (
          <div className="text-center">
            <button
              onClick={loadMore}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
            >
              Load More Scans
            </button>
          </div>
        )}

        {/* Loading More Indicator */}
        {loading && scans.length > 0 && (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading more scans...</p>
          </div>
        )}
      </div>
    </div>
  );
}
