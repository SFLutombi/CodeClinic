"use client";

import { useState } from 'react';
import URLInputForm from '@/components/URLInputForm';
import PageSelection from '@/components/PageSelection';
import ScanProgress from '@/components/ScanProgress';
import VitalsDashboard from '@/components/VitalsDashboard';
import LabResults from '@/components/LabResults';

interface Page {
  url: string;
  title: string;
  status_code: number;
}

export default function Home() {
  const [workflowStep, setWorkflowStep] = useState<'input' | 'crawling' | 'page-selection' | 'scanning' | 'completed' | 'error'>('input');
  const [scanData, setScanData] = useState<any>(null);
  const [crawlId, setCrawlId] = useState<string | null>(null);
  const [scanId, setScanId] = useState<string | null>(null);
  const [discoveredPages, setDiscoveredPages] = useState<Page[]>([]);

  const handleCrawlStart = async (url: string) => {
    try {
      setWorkflowStep('crawling');
      
      // Call backend API to start crawl
      const response = await fetch('http://localhost:8000/crawl/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to start crawl: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      setCrawlId(data.scan_id);
      
      // Poll for crawl completion
      pollCrawlStatus(data.scan_id);
      
    } catch (error) {
      console.error('Error starting crawl:', error);
      setWorkflowStep('error');
    }
  };

  const pollCrawlStatus = async (crawlId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/scan/${crawlId}/status`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          // Get discovered pages
          const pagesResponse = await fetch(`http://localhost:8000/crawl/${crawlId}/pages`);
          const pagesData = await pagesResponse.json();
          setDiscoveredPages(pagesData.pages || []);
          setWorkflowStep('page-selection');
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setWorkflowStep('error');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling crawl status:', error);
        setWorkflowStep('error');
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const handleScanAll = async () => {
    if (!crawlId) return;
    
    try {
      setWorkflowStep('scanning');
      
      // Start scan for all discovered pages
      const response = await fetch('http://localhost:8000/scan/start-selected', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scan_id: crawlId,
          selected_pages: discoveredPages.map(page => page.url)
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to start scan: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      setScanId(data.scan_id);
      
      // Poll for scan completion
      pollScanStatus(data.scan_id);
      
    } catch (error) {
      console.error('Error starting scan:', error);
      setWorkflowStep('error');
    }
  };

  const handleScanSelected = async (selectedPages: string[]) => {
    if (!crawlId) return;
    
    try {
      setWorkflowStep('scanning');
      
      // Start scan for selected pages
      const response = await fetch('http://localhost:8000/scan/start-selected', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scan_id: crawlId,
          selected_pages: selectedPages
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to start selected scan: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      setScanId(data.scan_id);
      
      // Poll for scan completion
      pollScanStatus(data.scan_id);
      
    } catch (error) {
      console.error('Error starting selected scan:', error);
      setWorkflowStep('error');
    }
  };

  const pollScanStatus = async (scanId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/scan/${scanId}/status`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          setScanData(data);
          setWorkflowStep('completed');
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setWorkflowStep('error');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling scan status:', error);
        setWorkflowStep('error');
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-blue-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">CodeClinic</h1>
                <p className="text-sm text-gray-600">Security Health Assessment</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="/gemini-questions"
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                🧠 AI Questions
              </a>
              <a
                href="/explore"
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                🔍 Explore
              </a>
              <a
                href="/leaderboard"
                className="text-blue-600 hover:text-blue-800 font-medium transition-colors"
              >
                🏆 Leaderboard
              </a>
              <div className="text-sm text-gray-500">
                Powered by OWASP ZAP
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {workflowStep === 'input' && (
          <div className="text-center">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Welcome to CodeClinic
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Assess the security health of your web applications with our gamified, 
                clinic-inspired security scanner. Get detailed diagnostics and actionable recommendations.
              </p>
            </div>
            
            <URLInputForm onCrawlStart={handleCrawlStart} />
          </div>
        )}

        {workflowStep === 'crawling' && (
          <ScanProgress scanId={crawlId} />
        )}

        {workflowStep === 'page-selection' && (
          <PageSelection 
            pages={discoveredPages}
            onScanAll={handleScanAll}
            onScanSelected={handleScanSelected}
          />
        )}

        {workflowStep === 'scanning' && (
          <ScanProgress scanId={scanId} />
        )}

        {workflowStep === 'completed' && scanData && (
          <div className="space-y-8">
            <VitalsDashboard vulnerabilities={scanData.vulnerabilities || []} />
            <LabResults vulnerabilities={scanData.vulnerabilities || []} />
          </div>
        )}

        {workflowStep === 'error' && (
          <div className="text-center">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">Process Failed</h3>
              <p className="text-red-700 mb-4">
                There was an error during the security assessment process. This could be due to:
              </p>
              <ul className="text-sm text-red-600 text-left mb-4">
                <li>• The target website is not accessible</li>
                <li>• Network connectivity issues</li>
                <li>• The website is blocking security scanners</li>
                <li>• Temporary server issues</li>
              </ul>
              <div className="space-y-2">
                <button
                  onClick={() => setWorkflowStep('input')}
                  className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={() => setWorkflowStep('input')}
                  className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Start Over
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}