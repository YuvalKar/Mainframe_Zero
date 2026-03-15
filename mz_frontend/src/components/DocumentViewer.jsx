// src/components/DocumentViewer.jsx
import { useState, useEffect } from 'react';

// Import the official Monaco Editor for React
import Editor from '@monaco-editor/react';

export default function DocumentViewer({ activeDocument, sendCommand, latestMessage, isConnected, onSelectionChange }) {
  const [fileContent, setFileContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // 2. Helper function to determine the language from the file extension
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
      
      //console.log("Monaco selection:", selectedText);

      // Send it up to App.jsx just like before
      if (onSelectionChange) {
        onSelectionChange(selectedText);
      }
    });
  };

  // 3.Fetch file content when activeDocument changes
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
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        backgroundColor: '#ffffff',
        border: '1px dashed var(--border-color)',
        borderRadius: '8px',
        color: 'var(--text-muted)',
        fontStyle: 'italic',
        fontSize: '0.9em'
      }}>
        Select a file from the shelf to preview...
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ paddingBottom: "10px", fontWeight: "bold", color: "var(--text-main)", fontSize: "0.9em" }}>
        {activeDocument.name}
      </div>
      
      <div style={{ 
          flex: 1, 
          overflowY: "auto", 
          backgroundColor: "#f8f9fa", 
          borderRadius: "6px",
          border: "1px solid var(--border-color)",
          color: "var(--text-main)"
        }}
      >
        {isLoading ? (
          <div style={{ padding: "15px", color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.85em" }}>
            Loading content...
          </div>
        ) : (
          <Editor
            height="100%"
            language={getLanguage(activeDocument.name)}
            theme="light"
            value={fileContent}
            onMount={handleEditorDidMount}
            options={{
              // Keep it read-only for now, setting the stage for future editing
              readOnly: true,
              // Hide the minimap on the right so it stays looking like a simple viewer
              minimap: { enabled: false },
              // Wrap long lines so we don't have horizontal scrollbars
              wordWrap: 'on',
              fontSize: 12
            }}
          />
        )}
      </div>
    </div>
  );
}