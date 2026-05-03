import React from 'react';

const CodeInput = ({ code, setCode, disabled }) => {
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (disabled) return;
    
    const file = e.dataTransfer.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => setCode(e.target.result);
      reader.readAsText(file);
    }
  };

  return (
    <textarea
      value={code}
      onChange={(e) => setCode(e.target.value)}
      disabled={disabled}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      placeholder="Paste your Python code here...&#10;&#10;Or drag & drop a file."
      className="w-full h-full min-h-[400px] p-4 bg-gray-50 border border-gray-200 rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-800 shadow-inner"
      spellCheck="false"
    />
  );
};

export default CodeInput;
