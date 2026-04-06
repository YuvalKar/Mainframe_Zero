// src/components/DocumentViewer.jsx
import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import FloatingWindow from './FloatingWindow';
import './DocumentViewer.css'; 

export default function DocumentViewer({ 
  activeDocument, 
  sendCommand, 
  latestMessage, 
  isConnected, 
  onSelectionChange,
  isVisible, 
  onClose,
  appColor
}) {
  const [fileContent, setFileContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const getLanguage = (filename) => {
    if (!filename) return 'text';
    const ext = filename.split('.').pop().toLowerCase();
    
    const languageMap = {
      'js': 'javascript', 'jsx': 'jsx', 'py': 'python',
      'md': 'markdown', 'json': 'json', 'html': 'html', 'css': 'css'
    };
    
    return languageMap[ext] || 'text'; 
  };

  const handleEditorDidMount = (editor, monaco) => {
    editor.onDidChangeCursorSelection((e) => {
      const selectedText = editor.getModel().getValueInRange(e.selection).trim();
      if (onSelectionChange) {
        onSelectionChange(selectedText);
      }
    });
  };

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

  // Center the viewer slightly, offset from the terminal
  const safeStartX = typeof window !== 'undefined' ? Math.max(20, window.innerWidth / 2 - 250) : 200;

  return (
    <FloatingWindow
      isVisible={isVisible}
      onClose={onClose}
      initialPosition={{ x: safeStartX, y: 100 }} 
      width="650px" // Wider than explorer for code readability
      color={appColor || "#4da8da"}
      contentMarginTop={24}
      closeButtonPos={{ top: 2, right: 10 }}
      className="viewer-floating-instance"
      topDecoration={
        <div className="viewer-drag-bar">
          <span>SYS.VIEWER</span>
        </div>
      }
    >
      <div className="document-viewer-container">
        
        {!activeDocument ? (
          <div className="document-viewer-empty">
            Select a file from the shelf to preview...
          </div>
        ) : (
          <>
            <div className="document-viewer-header">
              {activeDocument.name}
            </div>
            
            <div className="document-viewer-content">
              {isLoading ? (
                <div className="document-viewer-loading">
                  Loading content...
                </div>
              ) : (
                /* BULLETPROOF MONACO WRAPPER: Bypasses nested flexbox height calculation bugs */
                <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, right: 0 }}>
                  <Editor
                    height="100%"
                    language={getLanguage(activeDocument.name)}
                    theme="vs-dark" 
                    value={fileContent}
                    onMount={handleEditorDidMount}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      wordWrap: 'on',
                      fontSize: 12,
                      fontFamily: "'Fira Code', Consolas, 'Courier New', monospace",
                      renderLineHighlight: 'none' 
                    }}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </FloatingWindow>
  );
}