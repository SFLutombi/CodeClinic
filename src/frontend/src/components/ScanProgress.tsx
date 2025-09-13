"use client";

import { useState, useEffect } from 'react';

interface ScanProgressProps {
  scanId: string | null;
}

export default function ScanProgress({ scanId }: ScanProgressProps) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Initializing scan...');
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { name: 'Validating URL', description: 'Checking if the website is accessible' },
    { name: 'Discovering Pages', description: 'Crawling the website to find all pages' },
    { name: 'Running Security Tests', description: 'Scanning for vulnerabilities and security issues' },
    { name: 'Analyzing Results', description: 'Processing scan data and generating report' },
    { name: 'Generating Report', description: 'Creating your personalized security health report' }
  ];

  useEffect(() => {
    if (!scanId) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/scan/${scanId}/status`);
        const data = await response.json();
        
        setProgress(data.progress || 0);
        setStatus(data.status || 'Scanning...');
        
        // Update current step based on progress
        const stepIndex = Math.floor((data.progress || 0) / 20);
        setCurrentStep(Math.min(stepIndex, steps.length - 1));
        
      } catch (error) {
        console.error('Error polling scan status:', error);
      }
    };

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000);
    
    // Initial poll
    pollStatus();

    return () => clearInterval(interval);
  }, [scanId]);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-blue-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Security Checkup in Progress
          </h2>
          <p className="text-gray-600">
            We're examining your website for security vulnerabilities
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Current Step */}
        <div className="mb-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">{currentStep + 1}</span>
                </div>
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-blue-900">
                  {steps[currentStep]?.name || 'Processing...'}
                </h3>
                <p className="text-blue-700">
                  {steps[currentStep]?.description || 'Please wait while we process your request...'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Steps List */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Process</h3>
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center p-4 rounded-lg border transition-all ${
                index <= currentStep
                  ? 'bg-green-50 border-green-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex-shrink-0">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    index < currentStep
                      ? 'bg-green-600 text-white'
                      : index === currentStep
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {index < currentStep ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : index === currentStep ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
              </div>
              <div className="ml-4">
                <h4 className={`text-sm font-medium ${
                  index <= currentStep ? 'text-green-900' : 'text-gray-500'
                }`}>
                  {step.name}
                </h4>
                <p className={`text-sm ${
                  index <= currentStep ? 'text-green-700' : 'text-gray-400'
                }`}>
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Status Message */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            This may take a few minutes depending on the size of your website
          </p>
        </div>
      </div>
    </div>
  );
}
