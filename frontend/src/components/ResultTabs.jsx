import React, { useState } from 'react';
import { LayoutDashboard, Bug, ShieldAlert, Wrench, TerminalSquare } from 'lucide-react';
import BugList from './BugList';
import SecurityList from './SecurityList';
import FixList from './FixList';
import LogsViewer from './LogsViewer';

const ResultTabs = ({ results }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, count: null },
    { id: 'bugs', label: 'Bugs', icon: Bug, count: results.bugs?.length || 0 },
    { id: 'security', label: 'Security', icon: ShieldAlert, count: results.security_issues?.length || 0 },
    { id: 'fixes', label: 'Fixes', icon: Wrench, count: results.fixes?.length || 0 },
    { id: 'logs', label: 'Logs', icon: TerminalSquare, count: null },
  ];

  return (
    <div className="flex flex-col h-full bg-white rounded-xl">
      {/* Tabs Header */}
      <div className="flex border-b border-gray-200 overflow-x-auto custom-scrollbar bg-gray-50/50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 bg-white'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-100/50'
            }`}
          >
            <tab.icon size={16} className={activeTab === tab.id ? 'text-blue-500' : 'text-gray-400'} />
            {tab.label}
            {tab.count !== null && (
              <span className={`ml-1.5 py-0.5 px-2 rounded-full text-xs ${
                activeTab === tab.id 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-4 bg-gray-50/30">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Code Structure</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {results.parsed_data?.structure?.functions?.length || 0} <span className="text-sm font-normal text-gray-400">funcs</span>
                  </p>
                </div>
                <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-500">
                  <LayoutDashboard size={20} />
                </div>
              </div>
              
              <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Overall Severity</p>
                  <div className="flex items-center gap-2">
                    <p className="text-2xl font-bold text-gray-800 capitalize">
                      {results.summary?.overall_severity || 'Low'}
                    </p>
                    <span className="flex h-3 w-3 rounded-full bg-red-500"></span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center text-red-500">
                  <ShieldAlert size={20} />
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Complexity</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {results.summary?.complexity?.score || 0} <span className="text-sm font-normal text-gray-400">score</span>
                  </p>
                </div>
                <div className="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center text-orange-500">
                  <Activity size={20} />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Analysis Summary</h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex justify-between items-center py-2 border-b border-gray-50">
                  <span>Total Bugs Detected:</span>
                  <span className="font-bold text-gray-900">{results.summary?.total_bugs || 0}</span>
                </li>
                <li className="flex justify-between items-center py-2 border-b border-gray-50">
                  <span>Security Vulnerabilities:</span>
                  <span className="font-bold text-gray-900">{results.summary?.total_security_issues || 0}</span>
                </li>
                <li className="flex justify-between items-center py-2 border-b border-gray-50">
                  <span>Fixes Suggested:</span>
                  <span className="font-bold text-gray-900">{results.summary?.total_fixes || 0}</span>
                </li>
              </ul>
            </div>
          </div>
        )}
        {activeTab === 'bugs' && <BugList bugs={results.bugs || []} />}
        {activeTab === 'security' && <SecurityList issues={results.security_issues || []} />}
        {activeTab === 'fixes' && <FixList fixes={results.fixes || []} />}
        {activeTab === 'logs' && <LogsViewer logs={results.logs || []} />}
      </div>
    </div>
  );
};

// Activity icon for overview
const Activity = ({ size, className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
);

export default ResultTabs;
