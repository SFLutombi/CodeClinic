"use client";

import { Vulnerability, SeverityLevel } from '@/types/scan';

interface VitalsDashboardProps {
  vulnerabilities?: Vulnerability[];
}

export default function VitalsDashboard({ vulnerabilities }: VitalsDashboardProps) {
  // Ensure vulnerabilities is an array
  const vulns = vulnerabilities || [];
  
  // Calculate health metrics
  const totalVulns = vulns.length;
  const highSeverity = vulns.filter(v => v.severity === 'high').length;
  const mediumSeverity = vulns.filter(v => v.severity === 'medium').length;
  const lowSeverity = vulns.filter(v => v.severity === 'low').length;
  const infoSeverity = vulns.filter(v => v.severity === 'informational').length;

  // Calculate overall health score (0-100)
  const healthScore = Math.max(0, 100 - (highSeverity * 20) - (mediumSeverity * 10) - (lowSeverity * 5) - (infoSeverity * 1));
  
  // Determine health status
  const getHealthStatus = (score: number) => {
    if (score >= 80) return { status: 'Excellent', color: 'green', icon: '🟢' };
    if (score >= 60) return { status: 'Good', color: 'blue', icon: '🔵' };
    if (score >= 40) return { status: 'Fair', color: 'yellow', icon: '🟡' };
    if (score >= 20) return { status: 'Poor', color: 'orange', icon: '🟠' };
    return { status: 'Critical', color: 'red', icon: '🔴' };
  };

  const healthStatus = getHealthStatus(healthScore);

  // Get severity color
  const getSeverityColor = (severity: SeverityLevel) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-orange-600 bg-orange-100';
      case 'low': return 'text-yellow-600 bg-yellow-100';
      case 'informational': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Security Health Report
        </h2>
        <p className="text-gray-600">
          Your website's security assessment results
        </p>
      </div>

      {/* Main Health Score */}
      <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
        <div className="text-center">
          <div className="mb-6">
            <div className="text-6xl mb-4">{healthStatus.icon}</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Overall Health Score
            </h3>
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {healthScore}
            </div>
            <div className={`text-xl font-semibold text-${healthStatus.color}-600`}>
              {healthStatus.status}
            </div>
          </div>

          {/* Circular Progress Bar */}
          <div className="relative w-32 h-32 mx-auto mb-6">
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-gray-300"
              />
              {/* Progress circle */}
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - healthScore / 100)}`}
                className={`text-${healthStatus.color}-600 transition-all duration-1000 ease-out`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold text-gray-900">{healthScore}</span>
            </div>
          </div>

          <p className="text-gray-600 max-w-md mx-auto">
            {healthScore >= 80 
              ? "Your website shows excellent security practices with minimal vulnerabilities."
              : healthScore >= 60
              ? "Your website has good security with some areas for improvement."
              : healthScore >= 40
              ? "Your website has moderate security issues that should be addressed."
              : healthScore >= 20
              ? "Your website has significant security vulnerabilities that need immediate attention."
              : "Your website has critical security issues that require urgent remediation."
            }
          </p>
        </div>
      </div>

      {/* Vulnerability Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* High Severity */}
        <div className="bg-white rounded-lg shadow p-6 border border-red-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Severity</p>
              <p className="text-2xl font-bold text-red-600">{highSeverity}</p>
            </div>
          </div>
        </div>

        {/* Medium Severity */}
        <div className="bg-white rounded-lg shadow p-6 border border-orange-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Medium Severity</p>
              <p className="text-2xl font-bold text-orange-600">{mediumSeverity}</p>
            </div>
          </div>
        </div>

        {/* Low Severity */}
        <div className="bg-white rounded-lg shadow p-6 border border-yellow-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Low Severity</p>
              <p className="text-2xl font-bold text-yellow-600">{lowSeverity}</p>
            </div>
          </div>
        </div>

        {/* Informational */}
        <div className="bg-white rounded-lg shadow p-6 border border-blue-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Informational</p>
              <p className="text-2xl font-bold text-blue-600">{infoSeverity}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">{totalVulns}</div>
            <div className="text-sm text-gray-600">Total Issues Found</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {vulns.filter(v => v.type === 'xss').length}
            </div>
            <div className="text-sm text-gray-600">XSS Vulnerabilities</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900">
              {vulns.filter(v => v.type === 'insecure_headers').length}
            </div>
            <div className="text-sm text-gray-600">Header Issues</div>
          </div>
        </div>
      </div>
    </div>
  );
}
