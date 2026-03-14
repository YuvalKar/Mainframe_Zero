// src/components/DocumentViewer.jsx
import { useState, useEffect } from 'react';

export default function DocumentViewer({ activeDocument, sendCommand, latestMessage, isConnected }) {
  const [fileContent, setFileContent] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Fetch file content when activeDocument changes
  useEffect(() => {
    if (isConnected && activeDocument) {
      setIsLoading(true);
      setFileContent(""); // Clear previous content
      
      // Sending exact parameters expected by sense_read_text_file.py
      sendCommand({
        action: "execute",
        action_name: "sense_read_text_file", 
        action_data: { filepath: activeDocument.path }
      });
    }
  }, [activeDocument, isConnected]);

  // Listen for the incoming file content from the backend
  useEffect(() => {
    if (!latestMessage) return;

    // Matching the correct action_name
    if (latestMessage.type === "direct_result" && latestMessage.action_name === "sense_read_text_file") {
      const result = latestMessage.data;
      
      if (result.success) {
        // Python returns 'content' directly in the dictionary
        setFileContent(result.content); 
      } else {
        setFileContent(`Error reading file: ${result.message}`);
      }
      setIsLoading(false);
    }
  }, [latestMessage]);

  // Render placeholder if no document is currently selected
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

  // Render the actual document content
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ paddingBottom: "10px", fontWeight: "bold", color: "var(--text-main)", fontSize: "0.9em" }}>
        {activeDocument.name}
      </div>
      
      <div style={{ 
        flex: 1, 
        overflowY: "auto", 
        backgroundColor: "#f8f9fa", 
        padding: "15px", 
        borderRadius: "6px",
        border: "1px solid var(--border-color)",
        fontFamily: "monospace",
        fontSize: "0.85em",
        whiteSpace: "pre-wrap", // Preserves line breaks
        color: "var(--text-main)"
      }}>
        {isLoading ? (
          <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Loading content...</span>
        ) : (
          fileContent
        )}
      </div>
    </div>
  );
}