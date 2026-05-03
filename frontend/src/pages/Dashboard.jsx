import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../components/Header';
import CodeInput from '../components/CodeInput';
import ResultTabs from '../components/ResultTabs';
import { Terminal, Shield, Bug, PenTool } from 'lucide-react';

const Dashboard = () => {
  const [code, setCode] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [liveLogs, setLiveLogs] = useState([]);
  const [useAi, setUseAi] = useState(false);

  useEffect(() => {
    let interval;
    if (loading) {
      const mockLogs = [
        "[START] AI Code Review & Bug Detection System",
        "[INIT] Connecting to Multi-Agent System...",
        "[Node] Code Parser Agent: Extracting AST structure...",
        "[INFO] Analyzing variables, functions, and imports...",
        "[Node] Bug Detector Agent: Running static analysis...",
        "[INFO] Querying LLM for code smells and deep inspection...",
        "[WARN] Potential code complexity detected...",
        "[Node] Security Analyzer Agent: Scanning for vulnerabilities...",
        "[INFO] Checking for SQL injection and unsafe evals...",
        "[Node] Fix Suggestion Agent: Compiling recommendations...",
        "[INFO] Formatting final report...",
        "[SYSTEM] Please wait. Local LLM execution may take 2-5 minutes depending on your hardware..."
      ];
      let step = 0;
      interval = setInterval(() => {
        if (step < mockLogs.length) {
          setLiveLogs((prev) => [...prev, mockLogs[step]]);
          step++;
        }
      }, 1500);
    } else {
      setLiveLogs([]);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please provide some code to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await axios.post('http://localhost:8000/analyze', { code, use_ai: useAi });
      setResults(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to connect to the analysis server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header loading={loading} />
      
      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column: Input */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full min-h-[600px]">
              <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
                <h2 className="font-semibold text-gray-700 flex items-center gap-2">
                  <Terminal size={18} className="text-blue-500" />
                  Source Code
                </h2>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer" title="Uses local Llama 3 LLM (Slow)">
                    <div className="relative">
                      <input 
                        type="checkbox" 
                        className="sr-only" 
                        checked={useAi} 
                        onChange={(e) => setUseAi(e.target.checked)} 
                        disabled={loading} 
                      />
                      <div className={`block w-10 h-6 rounded-full transition-colors ${useAi ? 'bg-purple-500' : 'bg-gray-300'}`}></div>
                      <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${useAi ? 'transform translate-x-4' : ''}`}></div>
                    </div>
                    <span className="text-sm font-medium text-gray-600">Deep AI Analysis</span>
                  </label>
                  <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      loading 
                        ? 'bg-blue-100 text-blue-400 cursor-not-allowed' 
                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:scale-95'
                    }`}
                  >
                    {loading ? 'Analyzing...' : 'Analyze Code'}
                  </button>
                </div>
              </div>
              <div className="flex-1 p-4">
                <CodeInput code={code} setCode={setCode} disabled={loading} />
              </div>
              {error && (
                <div className="p-3 mx-4 mb-4 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Results */}
          <div className="lg:col-span-7 flex flex-col h-full min-h-[600px]">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex-1 flex flex-col overflow-hidden">
              {loading ? (
                <div className="flex-1 flex flex-col h-full bg-gray-900 overflow-hidden">
                  <div className="bg-gray-800/80 px-4 py-3 border-b border-gray-700 flex items-center gap-3">
                    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm font-medium tracking-wide text-gray-200">Agents are analyzing code...</span>
                  </div>
                  <div className="p-4 overflow-y-auto font-mono text-sm flex-1 custom-scrollbar">
                    {liveLogs.map((log, index) => {
                      if (!log) return null;
                      let colorClass = 'text-gray-300';
                      if (log.includes('WARN')) colorClass = 'text-yellow-400';
                      if (log.includes('START') || log.includes('Node:')) colorClass = 'text-blue-400 font-semibold';
                      return (
                        <div key={index} className="py-1 flex gap-3 hover:bg-white/5 px-2 rounded">
                          <span className="text-gray-500 select-none">{String(index + 1).padStart(3, '0')}</span>
                          <span className={`break-words ${colorClass}`}>{log}</span>
                        </div>
                      );
                    })}
                    <div className="py-1 flex gap-3 px-2 mt-2">
                       <span className="text-gray-500">...</span>
                       <span className="text-gray-500 animate-pulse">_</span>
                    </div>
                  </div>
                </div>
              ) : results ? (
                <ResultTabs results={results} />
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-gray-400 p-8 text-center">
                  <div className="flex gap-4 mb-6 opacity-20">
                    <Bug size={48} />
                    <Shield size={48} />
                    <PenTool size={48} />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-600 mb-2">Ready for Analysis</h3>
                  <p className="max-w-md">Paste your code on the left and click Analyze to let our Multi-Agent System inspect for bugs, bad practices, and security vulnerabilities.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default Dashboard;
