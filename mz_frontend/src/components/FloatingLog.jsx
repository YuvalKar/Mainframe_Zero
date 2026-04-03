// src/components/FloatingLog.jsx
import { useState, useEffect, useRef } from 'react';
import './FloatingLog.css';

export default function FloatingLog({ systemLogs }) {
  // State for visibility controlled by Ctrl+Shift+Q
  const [isVisible, setIsVisible] = useState(false);
  
  // State and refs for dragging logic
  const [position, setPosition] = useState({ x: 30, y: 70 });
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef(null);
  const offset = useRef({ x: 0, y: 0 });
  
  // Ref for auto-scrolling to bottom
  const messagesEndRef = useRef(null);

  // Handle Ctrl+Shift+Q toggle
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && (e.key === 'q' || e.key === 'Q')) {
        setIsVisible(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Auto-scroll when new logs arrive
  useEffect(() => {
    if (messagesEndRef.current && isVisible) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs, isVisible]);

  // --- Dragging Logic ---
  const handleMouseDown = (e) => {
    setIsDragging(true);
    // Calculate the offset between the mouse click and the top-left of the component
    offset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y
    };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - offset.current.x,
      y: e.clientY - offset.current.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Attach and detach global mouse events for smooth dragging
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]); // Re-bind when dragging state changes

  // If not visible, do not render anything to save resources
  if (!isVisible) return null;

  return (
    <div 
      className="floating-log-overlay"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`
      }}
    >
      {/* Header acts as the drag handle */}
      {/* TODO:add svg here? */}
      
      <div 
        className="floating-log-header" 
        onMouseDown={handleMouseDown}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        {/* Render the SVG image */}
        <img 
          src="Logger-top.svg"
          alt="Logger Top Decoration" 
          className="floating-log-top-svg" 
        />
        
        {/* Hide the text because the SVG already says 'SYS LOG' */}
        {/* <span className="floating-log-title">SYS.FULL_LOG</span> */}

        <button 
          className="floating-log-close" 
          onClick={() => setIsVisible(false)}
          title="Close (Ctrl+Shift+Q)"
        >
          ×
        </button>
      </div>
      
      <div className="floating-log-container">
        {systemLogs.map((log, index) => (
          // Filter out spammy update types if needed, otherwise show all
          (log.type === "hud_update") ? null : (
            <div key={index} className="floating-log-entry">
              {log.type && (
                <span className="log-type">
                  [{log.type.toUpperCase()}]
                </span>
              )}
              <span className="log-message">
                {typeof log.content === 'string' ? log.content : JSON.stringify(log.data || log)}
              </span>
            </div>
          )
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom decoration */}
      <img 
        src="Logger-bottom.svg" 
        alt="Logger Bottom" 
        className="floating-log-bottom-svg" 
      />
    </div>
  );
}