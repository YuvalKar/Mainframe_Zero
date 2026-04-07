// src/components/FileExplorer.jsx
import { useState, useEffect } from 'react';
import './FileExplorer.css'; // Make sure the CSS file is imported
import FloatingWindow from './FloatingWindow';

// --- Minimalist Inline SVG Icons ---

const ChevronIcon = ({ isOpen }) => (
  <svg 
    width="12" 
    height="12" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="1.5" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    style={{ 
      transform: isOpen ? 'rotate(90deg)' : 'none', 
      transition: 'transform 0.15s ease'
    }}
  >
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const FolderIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  </svg>
);

const DocumentIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
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
      <div className="tree-node-wrapper">
        <div className="tree-node-dir" onClick={() => setIsOpen(!isOpen)}>
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
      className={`tree-node-file ${isSelected ? 'selected' : ''}`}
      onClick={() => toggleAttention(node)}
    >
      <DocumentIcon />
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
  activeDocument,
  setActiveDocument,
  isVisible, 
  onClose,
  appColor
}) {
  const [treeData, setTreeData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Request the directory tree once we are connected to the server
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

  // Listen to incoming messages and filter only what belongs to us
  useEffect(() => {
    if (!latestMessage) return;

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

  // Calculate a safe starting X position to prevent rendering off-screen.
  // Places the window 420px from the right edge, but never less than 20px from the left.
  const safeStartX = typeof window !== 'undefined' ? Math.max(20, window.innerWidth - 420) : 500;
  
return (
    <FloatingWindow
      isVisible={isVisible}
      onClose={onClose}
      initialPosition={{ x: safeStartX, y: 150 }} // ממקם אותו בצד ימין
      width="380px" // סייר קבצים בדרך כלל צר יותר מטרמינל
      color={appColor || "#4da8da"}
      contentMarginTop={24}
      closeButtonPos={{ top: 2, right: 10 }}
      className="explorer-floating-instance"
      topDecoration={
        <div className="explorer-drag-bar">
          <span>Attention Span</span>
        </div>
      }
    >
      {/* --- File Explorer UI --- */}
      <div className="explorer-container">
        
        {/* Explorer Section */}
        <div className="explorer-section">
          <h3 className="section-title">Parietal Lobe</h3>
          
          {isLoading ? (
            <div className="empty-message">Scanning workspace...</div>
          ) : treeData.length === 0 ? (
            <div className="empty-message">No files found.</div>
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
        <div className="shelf-section">
          <h3 className="section-title">
            Attention ({attentionShelf.length})
          </h3>
          
          {attentionShelf.length === 0 ? (
            <div className="empty-message">No files selected...</div>
          ) : (
            attentionShelf.map((file, idx) => {
              const isActive = activeDocument && activeDocument.path === file.path;
              const itemClasses = `shelf-item ${isActive ? 'active' : ''} ${file.sent ? 'sent' : ''}`;
              const statusClasses = `shelf-item-status ${file.sent ? 'sent' : ''}`;

              return (
                <div 
                  key={idx} 
                  onClick={() => setActiveDocument(file)} 
                  className={itemClasses}
                >
                  <div className="shelf-item-content">
                    <span className={statusClasses}>
                      {file.sent ? "✓" : "⏳"}
                    </span>
                    <span className="shelf-item-name">
                      {file.name}
                    </span>
                  </div>
                  <span 
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleAttention(file);
                    }} 
                    className="shelf-item-remove"
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
    </FloatingWindow>
  );
}