import React from 'react';
import { Cpu, Activity } from 'lucide-react';

const Header = ({ loading }) => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="bg-blue-600 p-2 rounded-lg shadow-sm shadow-blue-200">
          <Cpu className="text-white" size={24} />
        </div>
        <div>
          <h1 className="font-bold text-xl text-gray-900 leading-tight">AI Code Review</h1>
          <p className="text-xs text-gray-500 font-medium tracking-wide uppercase">Multi-Agent System</p>
        </div>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-full border border-gray-100 shadow-inner">
        <Activity size={14} className={loading ? 'text-blue-500 animate-pulse' : 'text-green-500'} />
        <span className="text-xs font-semibold text-gray-600">
          {loading ? 'AGENTS RUNNING' : 'SYSTEM READY'}
        </span>
      </div>
    </header>
  );
};

export default Header;
