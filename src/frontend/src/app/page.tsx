"use client";

import { useState } from 'react';
import { ScanType } from '@/types/scan';
import URLInputForm from '@/components/URLInputForm';
import ScanProgress from '@/components/ScanProgress';
import VitalsDashboard from '@/components/VitalsDashboard';
import LabResults from '@/components/LabResults';

export default function Home() {
  const [scanStatus, setScanStatus] = useState<'idle' | 'scanning' | 'completed' | 'error'>('idle');
  const [scanData, setScanData] = useState<any>(null);
  const [scanId, setScanId] = useState<string | null>(null);

  const handleScanStart = async (url: string, scanType: ScanType) => {
    try {
      setScanStatus('scanning');
      
      // Call backend API to start scan
      const response = await fetch('http://localhost:8000/scan/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          scan_type: scanType
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
      setScanStatus('error');
    }
  };

  const pollScanStatus = async (scanId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/scan/${scanId}/status`);
        const data = await response.json();
        
        if (data.status === 'completed') {
          setScanData(data);
          setScanStatus('completed');
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setScanStatus('error');
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error('Error polling scan status:', error);
        setScanStatus('error');
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
            <div className="text-sm text-gray-500">
              Powered by OWASP ZAP
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {scanStatus === 'idle' && (
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
            
            <URLInputForm onScanStart={handleScanStart} />
          </div>
        )}

        {scanStatus === 'scanning' && (
          <ScanProgress scanId={scanId} />
        )}

        {scanStatus === 'completed' && scanData && (
          <div className="space-y-8">
            <VitalsDashboard vulnerabilities={scanData.vulnerabilities || []} />
            <LabResults vulnerabilities={scanData.vulnerabilities || []} />
          </div>
        )}

        {scanStatus === 'error' && (
          <div className="text-center">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">Scan Failed</h3>
              <p className="text-red-700">There was an error starting the scan. Please try again.</p>
              <button
                onClick={() => setScanStatus('idle')}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}