"use client";

import { useState } from 'react';

interface Page {
  url: string;
  title: string;
  status_code: number;
}

interface PageSelectionProps {
  pages: Page[];
  onScanSelected: (selectedPages: string[]) => void;
  onScanAll: () => void;
}

export default function PageSelection({ pages, onScanSelected, onScanAll }: PageSelectionProps) {
  const [selectedPages, setSelectedPages] = useState<string[]>([]);

  const handlePageToggle = (pageUrl: string) => {
    setSelectedPages(prev => 
      prev.includes(pageUrl) 
        ? prev.filter(url => url !== pageUrl)
        : [...prev, pageUrl]
    );
  };

  const handleSelectAll = () => {
    setSelectedPages(pages.map(page => page.url));
  };

  const handleDeselectAll = () => {
    setSelectedPages([]);
  };

  const handleScanSelected = () => {
    if (selectedPages.length > 0) {
      onScanSelected(selectedPages);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Website Crawling Complete
          </h3>
          <p className="text-gray-600">
            We discovered {pages.length} pages on your website. Choose which pages to scan for security vulnerabilities.
          </p>
        </div>

        {/* Selection Controls */}
        <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-4">
            <button
              onClick={handleSelectAll}
              className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              Select All
            </button>
            <button
              onClick={handleDeselectAll}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Deselect All
            </button>
            <span className="text-sm text-gray-600">
              {selectedPages.length} of {pages.length} pages selected
            </span>
          </div>
          <button
            onClick={onScanAll}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Scan All Pages
          </button>
        </div>

        {/* Page List */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {pages.map((page, index) => (
            <div
              key={index}
              className={`flex items-center p-4 rounded-lg border-2 transition-all cursor-pointer ${
                selectedPages.includes(page.url)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handlePageToggle(page.url)}
            >
              <div className="flex-shrink-0 mr-4">
                <input
                  type="checkbox"
                  checked={selectedPages.includes(page.url)}
                  onChange={() => handlePageToggle(page.url)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {page.title || 'Untitled Page'}
                  </h4>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {page.status_code}
                  </span>
                </div>
                <p className="text-xs text-gray-600 truncate mt-1">
                  {page.url}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {selectedPages.length > 0 
              ? `Ready to scan ${selectedPages.length} selected pages`
              : 'Select pages to scan or choose "Scan All Pages"'
            }
          </div>
          <button
            onClick={handleScanSelected}
            disabled={selectedPages.length === 0}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Scan Selected ({selectedPages.length})
          </button>
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800">Scanning Options</h4>
              <p className="text-sm text-blue-700 mt-1">
                <strong>Scan All:</strong> Comprehensive security scan of all discovered pages (slower, more thorough)
                <br />
                <strong>Scan Selected:</strong> Targeted scan of only the pages you choose (faster, more focused)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
