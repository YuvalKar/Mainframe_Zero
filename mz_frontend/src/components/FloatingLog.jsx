// src/components/FloatingLog.jsx
import { useState, useEffect, useRef } from 'react';
import FloatingWindow from './FloatingWindow';
import './FloatingLog.css';

const MAX_VISIBLE_LOGS = 20;

export default function FloatingLog({ systemLogs, appColor }) {
  // State for visibility controlled by Ctrl+Shift+Q
  const [isVisible, setIsVisible] = useState(false);
  const messagesEndRef = useRef(null);
  const my_color= appColor || "#4da8da";

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
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1190 227" width="100%" height="100%">
        <path d="M389.5,87 L406,87 L394.7,67 L378.2,67 Z M368.3,87 L384.8,87 L373.5,67 L357,67 Z M346.2,87 L362.7,87 L351.4,67 L335,67 Z" 
        fill={my_color} fill-opacity="1.0"/>
        <path d="M0,227 L0,91 L28,45 L178,45 L191.7,68 L329.8,68 L342,91 L1175.7,90.7 L1189,113.8 L1189,149.1" 
        stroke={my_color} stroke-width="4" fill="none"/>
        <path d="M5,92 L31,50 L175,50 L189,72 L327,72 L337,91 Z" fill={my_color} fill-opacity="0.5" stroke={my_color} stroke-width="2"/>
        <text x="30" y="78" font-family="'Source Sans Pro', sans-serif" font-size="20" fill="#ffffff" font-weight="400">Inner Monologue</text>
        <path d="M1180,86 L1180,30 L1166.8,7 L1089,7" stroke={my_color} stroke-width="2" fill="none"/>
        <path d="M1156,86 L1180,86 L1190,104" stroke={my_color} stroke-width="2" fill="none"/>
        <circle cx="1080" cy="15" r="14" fill={my_color} fill-opacity="0.8" stroke={my_color} stroke-width="2"/>
      </svg>
  );

  const loggerBottomDeco = (
    <div style={{ marginTop:'-32px'}}>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1187 80" width="100%" height="100%">
      <path d="M854,57 L1131,57 L1117.7,80 L867.3,80 Z" fill={my_color} fill-opacity="1.0"/>
      <path d="M0,0 L0,57 L1172,57 L1187,31 L1187,11.7" stroke={my_color} stroke-width="4" fill="none"/>
    </svg>
    </div>
  );

  return (
    <FloatingWindow
      isVisible={isVisible}
      onClose={() => setIsVisible(false)}
      initialPosition={{ x: 30, y: 70 }}
      width="700px"
      maxContentHeight="450px"
      color= {my_color}
      topDecoration={loggerTopDeco}
      bottomDecoration={loggerBottomDeco}
      // Nudge the close button to sit nicely on the diagonal part of your specific SVG
      closeButtonPos={{ top: -1, right: 55 }} 
      contentMarginTop={54} // Just a tiny gap from the top SVG
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