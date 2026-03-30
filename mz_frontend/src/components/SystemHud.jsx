import React, { useState, useEffect, useRef } from 'react';
import './SystemHud.css'; 

const SystemHud = ({ systemLogs = [] }) => {
  const [isVisible, setIsVisible] = useState(false);
  const logsEndRef = useRef(null);

  // Keyboard toggle logic (Ctrl + Shift + H)
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.ctrlKey && event.shiftKey && (event.key.toLowerCase() === 'h' || event.key === 'י')) {
        setIsVisible((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Auto-scroll logic
  useEffect(() => {
    if (isVisible && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs, isVisible]);

  if (!isVisible) return null;

  return (
    <div className="hud-overlay">
      <div className="hud-header">
        <span className="hud-title">System Subconscious</span>
        <div className="hud-status-indicator pulse"></div>
      </div>
      
      <div className="hud-logs-container">
        {systemLogs.map((log, index) => 
          // מסננים החוצה הודעות מערכת ארוכות ומיותרות כמו סריקת התיקיות
          log.type === "direct_result" ? null : (
            <div key={index} className="hud-log-entry">
              
              {/* מציגים רק את סוג ההודעה ואת התוכן שלה, בלי שעת הפעולה */}
              {log.type && (
                <span style={{ color: '#fff', marginRight: '8px', fontWeight: 'bold' }}>
                  [{log.type.toUpperCase()}]
                </span>
              )}
              
              <span className="log-message">
                {log.content || log.message || JSON.stringify(log)}
              </span>
            </div>
          )
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default SystemHud;