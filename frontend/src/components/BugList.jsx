import React from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

const getSeverityStyles = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high':
      return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: AlertCircle, iconColor: 'text-red-500' };
    case 'medium':
      return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', icon: AlertTriangle, iconColor: 'text-yellow-500' };
    default:
      return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: Info, iconColor: 'text-blue-500' };
  }
};

const BugList = ({ bugs }) => {
  if (!bugs || bugs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <div className="bg-green-50 p-4 rounded-full mb-3 text-green-500">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
        </div>
        <p>No bugs detected! Great job.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {bugs.map((bug, index) => {
        const styles = getSeverityStyles(bug.severity);
        const Icon = styles.icon;
        
        return (
          <div key={index} className={`rounded-xl border ${styles.border} ${styles.bg} p-4 shadow-sm transition-all hover:shadow-md`}>
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 ${styles.iconColor}`}>
                <Icon size={20} />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className={`font-semibold ${styles.text} capitalize`}>
                    {bug.type.replace(/_/g, ' ')}
                  </h4>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border ${styles.border} bg-white/50 ${styles.text}`}>
                    Line {bug.line}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mt-2 font-medium">{bug.message}</p>
                {bug.explanation && bug.explanation !== bug.message && (
                  <p className="text-sm text-gray-600 mt-2 bg-white/60 p-2 rounded-lg border border-black/5">
                    {bug.explanation}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default BugList;
