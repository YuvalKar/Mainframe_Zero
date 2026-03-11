// src/components/FileExplorer.jsx
import { useState, useEffect } from 'react';

// Recursive component to render folders and files
const FileTreeNode = ({ node, toggleAttention, attentionShelf }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isSelected = attentionShelf.some(f => f.path === node.path);

  // Render directory
  if (node.type === 'directory') {
    return (
      <div style={{ marginLeft: "10px", marginTop: "5px" }}>
        <div 
          onClick={() => setIsOpen(!isOpen)} 
          style={{ cursor: "pointer", fontWeight: "bold", color: "#dcdcaa" }}
        >
          {isOpen ? "📂" : "📁"} {node.name}
        </div>
        {isOpen && node.children && (
          <div>
            {node.children.map((child, idx) => (
              <FileTreeNode 
                key={idx} 
                node={child} 
                toggleAttention={toggleAttention} 
                attentionShelf={attentionShelf} 
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // Render file
  return (
    <div 
      onClick={() => toggleAttention(node)}
      style={{ 
        marginLeft: "20px", 
        cursor: "pointer", 
        color: isSelected ? "#4CAF50" : "#cccccc",
        textDecoration: isSelected ? "underline" : "none"
      }}
    >
      📄 {node.name}
    </div>
  );
};

// Main FileExplorer component
export default function FileExplorer({ attentionShelf, toggleAttention, sendCommand, latestMessage, isConnected }) {
  const [treeData, setTreeData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // 1. Request the directory tree once we are connected to the server
  useEffect(() => {
    if (isConnected) {
      setIsLoading(true);
      sendCommand({
        action: "execute",
        action_name: "sense_get_directory_tree",
        action_data: { root_path: "." }
      });
    }
  }, [isConnected]); // Re-run if connection status changes

  // 2. Listen to incoming messages and filter only what belongs to us
  useEffect(() => {
    if (!latestMessage) return;

    // Filter: Is this a direct result for our specific sense?
    if (latestMessage.type === "direct_result" && latestMessage.action_name === "sense_get_directory_tree") {
      const result = latestMessage.data;
      
      if (result.success) {
        setTreeData(result.data);
      } else {
        console.error("Sense execution failed:", result.message);
      }
      
      setIsLoading(false);
    }
  }, [latestMessage]); // Re-run every time a new message arrives from the App

  return (
    <div style={{ 
      width: "300px", 
      borderRight: "1px solid #333", 
      display: "flex", 
      flexDirection: "column", 
      padding: "10px", 
      backgroundColor: "#1e1e1e", 
      color: "#d4d4d4",
      height: "100%"
    }}>
      
      {/* Explorer Section */}
      <div style={{ flex: 1, overflowY: "auto", borderBottom: "1px solid #333", paddingBottom: "10px" }}>
        <h3 style={{ color: "#9cdcfe", margin: "0 0 10px 0" }}>EXPLORER</h3>
        
        {isLoading ? (
          <div style={{ color: "#808080", fontStyle: "italic", fontSize: "0.9em" }}>Scanning workspace...</div>
        ) : treeData.length === 0 ? (
          <div style={{ color: "#808080", fontStyle: "italic", fontSize: "0.9em" }}>No files found.</div>
        ) : (
          treeData.map((node, idx) => (
            <FileTreeNode 
              key={idx} 
              node={node} 
              toggleAttention={toggleAttention} 
              attentionShelf={attentionShelf} 
            />
          ))
        )}
      </div>

      {/* Attention Shelf Section */}
      <div style={{ height: "250px", overflowY: "auto", paddingTop: "10px" }}>
        <h3 style={{ color: "#ce9178", margin: "0 0 10px 0" }}>ATTENTION SHELF ({attentionShelf.length})</h3>
        
        {attentionShelf.length === 0 ? (
          <div style={{ color: "#808080", fontStyle: "italic", fontSize: "0.9em" }}>No files selected...</div>
        ) : (
          attentionShelf.map((file, idx) => (
            <div key={idx} style={{ 
              display: "flex", 
              justifyContent: "space-between", 
              marginBottom: "5px", 
              padding: "5px", 
              backgroundColor: "#2d2d2d", 
              borderRadius: "3px", 
              fontSize: "0.9em" 
            }}>
              <span style={{ 
                overflow: "hidden", 
                textOverflow: "ellipsis", 
                whiteSpace: "nowrap",
                color: file.sent ? "#4CAF50" : "#ce9178"
              }}>
                {file.sent ? "✅ " : "⏳ "} {file.name}
              </span>
              <span 
                onClick={() => toggleAttention(file)} 
                style={{ cursor: "pointer", color: "#f44336", fontWeight: "bold", paddingLeft: "10px" }}
                title="Remove"
              >
                X
              </span>
            </div>
          ))
        )}
      </div>

    </div>
  );
}