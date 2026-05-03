import React from 'react';
import { ShieldAlert, Shield, ShieldCheck } from 'lucide-react';

const getSeverityStyles = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: ShieldAlert, iconColor: 'text-red-600', badge: 'bg-red-100 border-red-300' };
    case 'medium':
      return { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', icon: Shield, iconColor: 'text-orange-500', badge: 'bg-orange-100 border-orange-300' };
    default:
      return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', icon: ShieldCheck, iconColor: 'text-yellow-500', badge: 'bg-yellow-100 border-yellow-300' };
  }
};

const SecurityList = ({ issues }) => {
  if (!issues || issues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <div className="bg-green-50 p-4 rounded-full mb-3 text-green-500">
          <ShieldCheck size={32} />
        </div>
        <p>No security vulnerabilities found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {issues.map((issue, index) => {
        const styles = getSeverityStyles(issue.severity);
        const Icon = styles.icon;
        
        return (
          <div key={index} className={`rounded-xl border ${styles.border} bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow`}>
            {/* Header */}
            <div className={`px-4 py-3 border-b ${styles.border} ${styles.bg} flex justify-between items-center`}>
              <div className="flex items-center gap-2">
                <Icon size={18} className={styles.iconColor} />
                <h4 className={`font-semibold ${styles.text} capitalize`}>
                  {issue.type.replace(/_/g, ' ')}
                </h4>
              </div>
              <span className={`text-xs font-bold px-2 py-0.5 rounded border ${styles.badge} ${styles.text} uppercase`}>
                {issue.severity} Risk
              </span>
            </div>
            
            {/* Body */}
            <div className="p-4">
              <div className="flex justify-between items-start mb-3">
                <p className="text-sm text-gray-800 font-medium">{issue.message}</p>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded font-mono">Line {issue.line}</span>
              </div>
              
              {issue.code_snippet && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Vulnerable Code</p>
                  <pre className="bg-gray-900 text-red-300 p-3 rounded-lg text-xs overflow-x-auto font-mono">
                    {issue.code_snippet}
                  </pre>
                </div>
              )}
              
              {issue.remediation && (
                <div className="bg-green-50 p-3 rounded-lg border border-green-100">
                  <p className="text-xs text-green-800 uppercase tracking-wider font-semibold mb-1">Remediation</p>
                  <p className="text-sm text-green-900">{issue.remediation}</p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SecurityList;
