import React from 'react';
import './SeedLogo.css';

const SeedLogo = ({ isExpanded, toggleExpand, toggleTerminal, toggleFiles }) => {
  
  const handleToggle = () => {
    toggleExpand();
    if (window.electronAPI && window.electronAPI.toggleWindowSize) {
      window.electronAPI.toggleWindowSize(!isExpanded);
    }
  };

  return (
    <div className={`seed-wrapper ${isExpanded ? 'state-expanded' : 'state-folded'}`}>
      
      <div className="logo-container">
        {/* CRITICAL: draggable="false" prevents HTML native image dragging,
          allowing Electron's -webkit-app-region to work properly.
        */}
        <img 
          src="/nBaya_logo.svg" 
          alt="nBaya Logo" 
          className="logo-img" 
          draggable="false" 
        />
        
        {/* The invisible layer that handles interactions */}
        <div className="interaction-overlay">
          {/* Left zone: 'n' - Dragging the window */}
          <div className="drag-zone" title="Drag to move"></div>
          
          {/* Right zone: 'Baya' - Clicking to expand/fold */}
          <div 
            className="click-zone" 
            onClick={handleToggle}
            title={isExpanded ? "Click to fold" : "Click to expand"}
          ></div>
        </div>
      </div>

      {isExpanded && (
        <div className="seed-toolbar">
          <div className="toolbar-divider" />
          <button className="toolbar-item" onClick={toggleTerminal}>Cortex</button>
          <button className="toolbar-item" onClick={toggleFiles}>Attention</button>
        </div>
      )}
    </div>
  );
};

export default SeedLogo;