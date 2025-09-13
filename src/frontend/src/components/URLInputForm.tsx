"use client";

import { useState } from 'react';
import { ScanType } from '@/types/scan';

interface URLInputFormProps {
  onScanStart: (url: string, scanType: ScanType) => void;
}

export default function URLInputForm({ onScanStart }: URLInputFormProps) {
  const [url, setUrl] = useState('');
  const [scanType, setScanType] = useState<ScanType>('full_site');
  const [isValidating, setIsValidating] = useState(false);

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url);
      return url.startsWith('http://') || url.startsWith('https://');
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      alert('Please enter a URL');
      return;
    }

    if (!validateUrl(url)) {
      alert('Please enter a valid URL (must start with http:// or https://)');
      return;
    }

    setIsValidating(true);
    
    try {
      // Basic URL accessibility check
      const response = await fetch(url, { 
        method: 'HEAD',
        mode: 'no-cors' // This will work for same-origin or CORS-enabled sites
      });
      
      onScanStart(url, scanType);
    } catch (error) {
      // Even if CORS fails, we can still try the scan
      onScanStart(url, scanType);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Start Your Security Checkup
          </h3>
          <p className="text-gray-600">
            Enter your website URL to begin a comprehensive security assessment
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL Input */}
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
              Website URL
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <input
                type="url"
                id="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg"
                required
              />
            </div>
          </div>

          {/* Scan Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Scan Type
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                className={`relative cursor-pointer rounded-lg p-4 border-2 transition-all ${
                  scanType === 'full_site'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setScanType('full_site')}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <input
                      type="radio"
                      name="scanType"
                      value="full_site"
                      checked={scanType === 'full_site'}
                      onChange={() => setScanType('full_site')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Full Site Scan</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      Comprehensive scan of all discovered pages (slower, more thorough)
                    </p>
                  </div>
                </div>
              </div>

              <div
                className={`relative cursor-pointer rounded-lg p-4 border-2 transition-all ${
                  scanType === 'selective_pages'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setScanType('selective_pages')}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <input
                      type="radio"
                      name="scanType"
                      value="selective_pages"
                      checked={scanType === 'selective_pages'}
                      onChange={() => setScanType('selective_pages')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                  </div>
                  <div className="ml-3">
                    <h4 className="text-sm font-medium text-gray-900">Selective Pages</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      Choose specific pages to scan (faster, more targeted)
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isValidating}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isValidating ? (
              <div className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Validating URL...
              </div>
            ) : (
              'Start Security Checkup'
            )}
          </button>
        </form>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800">What happens next?</h4>
              <p className="text-sm text-blue-700 mt-1">
                We'll crawl your website, run security tests, and provide you with a detailed 
                health report including vulnerabilities and recommendations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
