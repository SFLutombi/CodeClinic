"use client";

import { useState } from 'react';
import { Vulnerability, SeverityLevel } from '@/types/scan';

interface LabResultsProps {
  vulnerabilities?: Vulnerability[];
}

export default function LabResults({ vulnerabilities }: LabResultsProps) {
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<SeverityLevel | 'all'>('all');

  // Ensure vulnerabilities is an array
  const vulns = vulnerabilities || [];

  // Filter vulnerabilities by severity
  const filteredVulns = filterSeverity === 'all' 
    ? vulns 
    : vulns.filter(v => v.severity === filterSeverity);

  // Get severity styling
  const getSeverityStyles = (severity: SeverityLevel) => {
    switch (severity) {
      case 'high':
        return {
          badge: 'bg-red-100 text-red-800 border-red-200',
          icon: '🔴',
          color: 'text-red-600'
        };
      case 'medium':
        return {
          badge: 'bg-orange-100 text-orange-800 border-orange-200',
          icon: '🟠',
          color: 'text-orange-600'
        };
      case 'low':
        return {
          badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          icon: '🟡',
          color: 'text-yellow-600'
        };
      case 'informational':
        return {
          badge: 'bg-blue-100 text-blue-800 border-blue-200',
          icon: 'ℹ️',
          color: 'text-blue-600'
        };
      default:
        return {
          badge: 'bg-gray-100 text-gray-800 border-gray-200',
          icon: '⚪',
          color: 'text-gray-600'
        };
    }
  };

  // Get vulnerability type icon
  const getVulnTypeIcon = (type: string) => {
    switch (type) {
      case 'xss': return '🕷️';
      case 'sql_injection': return '💉';
      case 'csrf': return '🔄';
      case 'insecure_headers': return '📋';
      case 'ssl_tls': return '🔒';
      case 'authentication': return '🔑';
      case 'authorization': return '👤';
      case 'data_exposure': return '📊';
      default: return '⚠️';
    }
  };

  const severityCounts = {
    all: vulnerabilities.length,
    high: vulnerabilities.filter(v => v.severity === 'high').length,
    medium: vulnerabilities.filter(v => v.severity === 'medium').length,
    low: vulnerabilities.filter(v => v.severity === 'low').length,
    informational: vulnerabilities.filter(v => v.severity === 'informational').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Lab Results</h2>
          <p className="text-gray-600">Detailed vulnerability analysis and recommendations</p>
        </div>
        <div className="text-sm text-gray-600">
          {filteredVulns.length} of {vulnerabilities.length} issues
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-1">
        <div className="flex space-x-1">
          {(['all', 'high', 'medium', 'low', 'informational'] as const).map((severity) => (
            <button
              key={severity}
              onClick={() => setFilterSeverity(severity)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                filterSeverity === severity
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-black hover:bg-gray-50'
              }`}
            >
              {severity === 'all' ? 'All' : severity.charAt(0).toUpperCase() + severity.slice(1)}
              <span className="ml-2 text-xs">
                ({severityCounts[severity]})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Vulnerability Cards */}
      <div className="space-y-4">
        {filteredVulns.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {filterSeverity === 'all' ? 'No Issues Found!' : `No ${filterSeverity} issues found`}
            </h3>
            <p className="text-gray-600">
              {filterSeverity === 'all' 
                ? 'Congratulations! Your website appears to be secure.'
                : `Great! No ${filterSeverity} severity issues were detected.`
              }
            </p>
          </div>
        ) : (
          filteredVulns.map((vuln) => {
            const severityStyles = getSeverityStyles(vuln.severity);
            const isExpanded = expandedVuln === vuln.id;
            
            return (
              <div
                key={vuln.id}
                className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Card Header */}
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedVuln(isExpanded ? null : vuln.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4">
                      <div className="text-2xl">
                        {getVulnTypeIcon(vuln.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {vuln.title}
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${severityStyles.badge}`}>
                            {severityStyles.icon} {vuln.severity.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm mb-2">
                          {vuln.description}
                        </p>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>URL: {vuln.url}</span>
                          {vuln.parameter && (
                            <span>Parameter: {vuln.parameter}</span>
                          )}
                          {vuln.cwe_id && (
                            <span>CWE: {vuln.cwe_id}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      <svg
                        className={`w-5 h-5 text-gray-500 transform transition-transform ${
                          isExpanded ? 'rotate-180' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-gray-200 bg-gray-50 p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Evidence */}
                      {vuln.evidence && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900 mb-2">Evidence</h4>
                          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <code className="text-sm text-red-800 break-all">
                              {vuln.evidence}
                            </code>
                          </div>
                        </div>
                      )}

                      {/* Solution */}
                      {vuln.solution && (
                        <div>
                          <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommended Solution</h4>
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <p className="text-sm text-green-800">
                              {vuln.solution}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-6 flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                          Mark as Fixed
                        </button>
                        <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
                          Learn More
                        </button>
                      </div>
                      <div className="text-xs text-gray-600">
                        Confidence: {vuln.confidence || 'Unknown'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Summary Footer */}
      {filteredVulns.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-800">Next Steps</h4>
              <p className="text-sm text-blue-700 mt-1">
                Review each vulnerability above and implement the recommended solutions. 
                Start with high-severity issues and work your way down. Consider running 
                another scan after making changes to verify improvements.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
