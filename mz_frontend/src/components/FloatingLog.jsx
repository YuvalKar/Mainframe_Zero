// src/components/FloatingLog.jsx
import { useState, useEffect, useRef } from 'react';
import FloatingWindow from './FloatingWindow';
import './FloatingLog.css';

const MAX_VISIBLE_LOGS = 10;

export default function FloatingLog({ systemLogs, appColor }) {
  // State for visibility controlled by Ctrl+Shift+Q
  const [isVisible, setIsVisible] = useState(false);
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
      messagesEndRef.current.scrollIntoView({ behavior: 'auto' });
    }
  }, [systemLogs, isVisible]);

  // Define the SVG decorations
  const loggerTopDeco = (
    <img 
      src="Logger-top.svg"
      alt="Logger Top" 
      style={{ width: '100%', display: 'block', pointerEvents: 'none' }} 
    />
  );

  const loggerBottomDeco = (
    <img 
      src="Logger-bottom.svg" 
      alt="Logger Bottom" 
      style={{ width: '100%', display: 'block', pointerEvents: 'none' }} 
    />
  );

  return (
    <FloatingWindow
      isVisible={isVisible}
      onClose={() => setIsVisible(false)}
      initialPosition={{ x: 30, y: 70 }}
      width="700px"
      maxContentHeight="450px"
      color={appColor || "#4da8da"} // Fallback color, though logger uses its own SVGs
      topDecoration={loggerTopDeco}
      bottomDecoration={loggerBottomDeco}
      // Nudge the close button to sit nicely on the diagonal part of your specific SVG
      closeButtonPos={{ top: -10, right: 35 }} 
      contentMarginTop={5} // Just a tiny gap from the top SVG
      className="floating-log-specific"
    >
      <div className="floating-log-messages">
        {systemLogs.slice(-MAX_VISIBLE_LOGS).map((log, index) => (
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
    </FloatingWindow>
  );
}