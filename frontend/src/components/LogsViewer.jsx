import React from 'react';
import { Terminal } from 'lucide-react';

const LogsViewer = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Terminal size={32} className="text-gray-300 mb-3" />
        <p>No execution logs available.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-xl overflow-hidden h-full flex flex-col border border-gray-800 shadow-inner">
      <div className="bg-gray-800/80 px-4 py-2.5 border-b border-gray-700 flex items-center gap-2">
        <Terminal size={14} className="text-gray-400" />
        <span className="text-xs font-medium tracking-wide text-gray-300 uppercase">System Logs</span>
      </div>
      
      <div className="p-4 overflow-y-auto font-mono text-sm flex-1 custom-scrollbar">
        {logs.map((log, index) => {
          let colorClass = 'text-gray-300';
          if (log.includes('ERROR') || log.includes('failed')) colorClass = 'text-red-400';
          if (log.includes('WARN')) colorClass = 'text-yellow-400';
          if (log.includes('START') || log.includes('END') || log.includes('SUCCESS') || log.includes('Node:')) colorClass = 'text-blue-400 font-semibold';
          if (log.includes('->')) colorClass = 'text-purple-400';

          return (
            <div key={index} className="py-1 flex gap-3 hover:bg-white/5 px-2 rounded">
              <span className="text-gray-600 select-none">
                {String(index + 1).padStart(3, '0')}
              </span>
              <span className={`break-words ${colorClass}`}>
                {log}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LogsViewer;
