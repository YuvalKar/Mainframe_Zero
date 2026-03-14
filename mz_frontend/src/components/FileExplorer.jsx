// src/components/FileExplorer.jsx
import { useState, useEffect } from 'react';

// --- Minimalist Inline SVG Icons ---

// Chevron for expanding/collapsing folders
const ChevronIcon = ({ isOpen }) => (
  <svg 
    width="12" 
    height="12" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    style={{ 
      transform: isOpen ? 'rotate(90deg)' : 'none', 
      transition: 'transform 0.15s ease',
      color: '#9aa0a6' // Subtle gray
    }}
  >
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

// Clean yellow folder icon
const FolderIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="#fbbc04" stroke="#fbbc04" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  </svg>
);

// Delicate document icon
const DocumentIcon = ({ isSelected }) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={isSelected ? "#1a73e8" : "#dadce0"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
    <polyline points="13 2 13 9 20 9"></polyline>
  </svg>
);

// --- File Tree Node Component ---

const FileTreeNode = ({ node, toggleAttention, attentionShelf }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isSelected = attentionShelf.some(f => f.path === node.path);

  // Render directory
  if (node.type === 'directory') {
    return (
      <div style={{ marginLeft: "10px", marginTop: "2px" }}>
        <div 
          onClick={() => setIsOpen(!isOpen)} 
          style={{ 
            cursor: "pointer", 
            fontWeight: "400", // Reduced weight to de-emphasize
            fontSize: "0.85em", // Smaller font size
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 0",
            userSelect: "none"
          }}
        >
          <ChevronIcon isOpen={isOpen} />
          <FolderIcon />
          <span>{node.name}</span>
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
        marginLeft: "28px", 
        cursor: "pointer", 
        color: isSelected ? "#1a73e8" : "#80868b", // Subtle gray for unselected, blue for selected
        backgroundColor: isSelected ? "#e8f0fe" : "transparent",
        fontSize: "0.85em",
        padding: "4px 8px",
        borderRadius: "4px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
        transition: "background-color 0.15s ease",
        userSelect: "none"
      }}
    >
      <DocumentIcon isSelected={isSelected} />
      <span>{node.name}</span>
    </div>
  );
};

// --- Main FileExplorer Component ---

export default function FileExplorer({ 
  attentionShelf, 
  toggleAttention, 
  sendCommand, 
  latestMessage, 
  isConnected,
  activeDocument,     // New prop
  setActiveDocument   // New prop
}) {
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
  }, [isConnected]); 

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
  }, [latestMessage]); 

  return (
    <div style={{ 
      display: "flex", 
      flexDirection: "column", 
      padding: "20px 10px", 
      height: "100%",
      boxSizing: "border-box"
    }}>
      
      {/* Explorer Section */}
      <div style={{ flex: 1, overflowY: "auto", borderBottom: "1px solid var(--border-color)", paddingBottom: "15px" }}>
        <h3 style={{ color: "var(--text-muted)", margin: "0 0 15px 10px", fontSize: "0.75em", letterSpacing: "1px", fontWeight: "600" }}>
          EXPLORER
        </h3>
        
        {isLoading ? (
          <div style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.85em", paddingLeft: "10px" }}>Scanning workspace...</div>
        ) : treeData.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.85em", paddingLeft: "10px" }}>No files found.</div>
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
      <div style={{ height: "30%", minHeight: "200px", overflowY: "auto", paddingTop: "15px" }}>
        <h3 style={{ color: "var(--text-muted)", margin: "0 0 15px 10px", fontSize: "0.75em", letterSpacing: "1px", fontWeight: "600" }}>
          ATTENTION SHELF ({attentionShelf.length})
        </h3>
        
        {attentionShelf.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: "0.85em", paddingLeft: "10px" }}>No files selected...</div>
        ) : (
          attentionShelf.map((file, idx) => {
            // Check if this file is the one currently showing in the viewer
            const isActive = activeDocument && activeDocument.path === file.path;

            return (
              <div 
                key={idx} 
                onClick={() => setActiveDocument(file)} // Set active on click
                style={{ 
                  display: "flex", 
                  justifyContent: "space-between", 
                  alignItems: "center",
                  marginBottom: "8px", 
                  padding: "6px 10px", 
                  // Visual feedback: blueish if active, greenish if sent, white otherwise
                  backgroundColor: isActive ? "#e8f0fe" : (file.sent ? "#e6f4ea" : "#ffffff"), 
                  border: isActive ? "1px solid #1a73e8" : (file.sent ? "1px solid #ceead6" : "1px solid var(--border-color)"),
                  borderRadius: "4px", 
                  fontSize: "0.85em",
                  boxShadow: "0 1px 2px rgba(0,0,0,0.02)",
                  transition: "all 0.2s ease",
                  cursor: "pointer" // Pointer implies it's clickable
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden" }}>
                  <span style={{ fontSize: "1.1em", color: file.sent ? "#1e8e3e" : "inherit" }}>
                    {file.sent ? "✓" : "⏳"}
                  </span>
                  <span style={{ 
                    overflow: "hidden", 
                    textOverflow: "ellipsis", 
                    whiteSpace: "nowrap",
                    color: isActive ? "#1a73e8" : (file.sent ? "#1e8e3e" : "var(--text-main)"),
                    fontWeight: (isActive || file.sent) ? "500" : "400"
                  }}>
                    {file.name}
                  </span>
                </div>
                <span 
                  onClick={(e) => {
                    e.stopPropagation(); // Prevent the parent div onClick from firing
                    toggleAttention(file);
                  }} 
                  style={{ cursor: "pointer", color: "#9aa0a6", fontWeight: "bold", fontSize: "1.2em", paddingLeft: "10px" }}
                  title="Remove"
                >
                  ×
                </span>
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}