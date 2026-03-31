// src/components/DocumentViewer.jsx
import { useState, useEffect } from 'react';

// Import the official Monaco Editor for React
import Editor from '@monaco-editor/react';
import './DocumentViewer.css'; // Added import for our clean styles

export default function DocumentViewer({ activeDocument, sendCommand, latestMessage, isConnected, onSelectionChange }) {
  const [fileContent, setFileContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Helper function to determine the language from the file extension
  const getLanguage = (filename) => {
    if (!filename) return 'text';
    const ext = filename.split('.').pop().toLowerCase();
    
    const languageMap = {
      'js': 'javascript',
      'jsx': 'jsx',
      'py': 'python',
      'md': 'markdown',
      'json': 'json',
      'html': 'html',
      'css': 'css'
    };
    
    return languageMap[ext] || 'text'; // Fallback to plain text if unknown
  };

  // Native Monaco editor selection handler
  const handleEditorDidMount = (editor, monaco) => {
    // Listen to selection changes directly from the editor instance
    editor.onDidChangeCursorSelection((e) => {
      // Get the exact text based on the user's selection range
      const selectedText = editor.getModel().getValueInRange(e.selection).trim();
      
      // Send it up to App.jsx just like before
      if (onSelectionChange) {
        onSelectionChange(selectedText);
      }
    });
  };

  // Fetch file content when activeDocument changes
  useEffect(() => {
    if (isConnected && activeDocument) {
      setIsLoading(true);
      setFileContent(""); 
      
      sendCommand({
        action: "execute",
        action_name: "sense_read_text_file", 
        action_data: { filepath: activeDocument.path }
      });
    }
  }, [activeDocument, isConnected]);

  // Listen for the incoming file content
  useEffect(() => {
    if (!latestMessage) return;

    if (latestMessage.type === "direct_result" && latestMessage.action_name === "sense_read_text_file") {
      const result = latestMessage.data;
      
      if (result.success) {
        setFileContent(result.content); 
      } else {
        setFileContent(`Error reading file: ${result.message}`);
      }
      setIsLoading(false);
    }
  }, [latestMessage]);

  if (!activeDocument) {
    return (
      <div className="document-viewer-empty">
        Select a file from the shelf to preview...
      </div>
    );
  }

  return (
    <div className="document-viewer-container">
      <div className="document-viewer-header">
        {activeDocument.name}
      </div>
      
      <div className="document-viewer-content">
        {isLoading ? (
          <div className="document-viewer-loading">
            Loading content...
          </div>
        ) : (
          <Editor
            height="100%"
            language={getLanguage(activeDocument.name)}
            theme="light" // Monaco's light theme fits the grayscale aesthetic well
            value={fileContent}
            onMount={handleEditorDidMount}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              wordWrap: 'on',
              fontSize: 12,
              // Apply a square, technical font family for the code editor
              fontFamily: "'Fira Code', Consolas, 'Courier New', monospace",
              // Cleaner look for the editor lines
              renderLineHighlight: 'none' 
            }}
          />
        )}
      </div>
    </div>
  );
}