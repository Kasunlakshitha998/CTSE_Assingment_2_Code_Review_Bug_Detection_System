import React, { useState } from 'react';
import { CheckCircle2, Copy, Check } from 'lucide-react';

const FixList = ({ fixes }) => {
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!fixes || fixes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <div className="bg-gray-100 p-4 rounded-full mb-3">
          <CheckCircle2 size={32} className="text-gray-400" />
        </div>
        <p>No fixes suggested.</p>
      </div>
    );
  }

  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-6">
      {fixes.map((fix, index) => (
        <div key={index} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Header */}
          <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`flex w-2.5 h-2.5 rounded-full ${
                fix.severity === 'high' ? 'bg-red-500' : 
                fix.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
              }`}></span>
              <h4 className="font-semibold text-gray-800 capitalize">
                Fix for {fix.issue_type.replace(/_/g, ' ')}
              </h4>
            </div>
            <span className="text-xs bg-white border border-gray-200 px-2.5 py-1 rounded-md text-gray-600 font-mono">
              Line {fix.line}
            </span>
          </div>

          <div className="p-5">
            <div className="mb-4">
              <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Current Problem</h5>
              <p className="text-sm text-gray-700 bg-red-50/50 p-2.5 rounded border border-red-100/50">
                {fix.current_problem}
              </p>
            </div>

            <div className="mb-4">
              <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Suggested Fix</h5>
              <p className="text-sm text-gray-700 bg-green-50/50 p-2.5 rounded border border-green-100/50">
                {fix.suggested_fix}
              </p>
            </div>

            {fix.code_example && (
              <div className="mt-4 relative group">
                <div className="flex items-center justify-between bg-gray-800 rounded-t-lg px-4 py-2 border-b border-gray-700">
                  <span className="text-xs font-medium text-gray-400">Code Example</span>
                  <button 
                    onClick={() => copyToClipboard(fix.code_example, index)}
                    className="text-gray-400 hover:text-white transition-colors"
                    title="Copy code"
                  >
                    {copiedIndex === index ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                  </button>
                </div>
                <pre className="bg-gray-900 text-gray-300 p-4 rounded-b-lg text-sm overflow-x-auto font-mono">
                  {fix.code_example}
                </pre>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default FixList;
