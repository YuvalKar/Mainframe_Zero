import React, { useState, useEffect, useRef } from 'react';
import './SystemHud.css'; 
import { useDraggable } from '../hooks/useDraggable';

// This tells Vite to gather all SVG paths from your new folder
const hologramModules = import.meta.glob('../assets/holograms/*.svg', { 
  eager: true, 
  query: '?url', 
  import: 'default' 
});
const hologramStack = Object.values(hologramModules);


// --- WIDGET FACTORY ---
const TextWidget = ({ data }) => (
  <div style={{ color: '#00ffff' }}>{typeof data === 'object' ? JSON.stringify(data) : data}</div>
);

const GaugeWidget = ({ data }) => {
  const val = typeof data === 'number' ? data : 50;
  return (
    <div style={{ width: '100%' }}>
      <div style={{ fontSize: '10px', marginBottom: '4px' }}>VALUE: {val}%</div>
      <div style={{ height: '4px', background: '#333', border: '1px solid cyan' }}>
        <div style={{ height: '100%', width: `${val}%`, background: 'cyan', boxShadow: '0 0 10px cyan' }} />
      </div>
    </div>
  );
};

const TimerWidget = ({ data, onRemove }) => {
  const initialTime = data?.time || 5;
  const text = data?.text || (typeof data === 'string' ? data : "System Task");
  
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [selectedImg, setSelectedImg] = useState(null);

  // 1. Lottery: Pick a random image from the folder ONCE on mount
  useEffect(() => {
    if (hologramStack.length > 0) {
      const randomIndex = Math.floor(Math.random() * hologramStack.length);
      setSelectedImg(hologramStack[randomIndex]);
    }
  }, []);

  // 2. Countdown Logic
  useEffect(() => {
    if (timeLeft <= 0) {
      onRemove?.();
      return;
    }
    const timerId = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    return () => clearInterval(timerId);
  }, [timeLeft, onRemove]);

  return (
    <div className="hologram-timer-container">
      {selectedImg && (
        <img 
          src={selectedImg} 
          className="hologram-svg-rotating" 
          alt="hologram" 
        />
      )}
      <div className="hologram-content">
        <span className="hologram-label">{text}</span>
        <span className="hologram-number">{timeLeft}</span>
        <span className="hologram-unit">SEC</span>
      </div>
    </div>
  );
};

const WIDGETS = {
  "TEXT": TextWidget,
  "GAUGE": GaugeWidget,
  "TIMER": TimerWidget
};
// ----------------------

const SystemHud = ({ systemLogs = [] }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [entities, setEntities] = useState({});
  const logsEndRef = useRef(null);
  const systemLogRef = useRef(null);
  const removeEntity = (idToRemove) => {
    setEntities(prev => {
      const next = { ...prev };
      delete next[idToRemove];
      return next;
    });
  };

  // Keyboard toggle logic (Ctrl + Shift + H)
  useEffect(() => {
    //Supporting both English 'h' and Hebrew 'י'
    const handleKeyDown = (event) => {
      if (event.ctrlKey && event.shiftKey && (event.key.toLowerCase() === 'h' || event.key === 'י')) {
        setIsVisible((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Sync React entities state
  useEffect(() => {
    if (systemLogs.length > 0) {
      const updatedEntities = {};
      systemLogs.forEach(log => {
        if (log.type === "hud_update") {
          const isWidgetFormat = typeof log.data === 'object' && log.data !== null && 'value' in log.data;
          updatedEntities[log.id] = {
            type: isWidgetFormat && log.data.type ? log.data.type : "TEXT",
            value: isWidgetFormat ? log.data.value : log.data,
            updatedAt: Date.now()
          };
        }
      });
      setEntities(updatedEntities);
    }
  }, [systemLogs]);

  // Auto-scroll for the log container
  useEffect(() => {
    if (isVisible && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs, isVisible]);

  // Use the new lightweight drag hook
  useDraggable(entities, systemLogRef);


  return (
    <>
      {/* 1. THE FLOATING ENTITIES (DYNAMIC HUD) */}
      <div 
        className="dynamic-hud-layer" 
        style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          width: '100vw', 
          height: '100vh', 
          zIndex: 9998,
          // NEW: Control visibility via CSS instead of unmounting the DOM
          opacity: isVisible ? 1 : 0,
          visibility: isVisible ? 'visible' : 'hidden',
          pointerEvents: isVisible ? 'none' : 'none', // The layer itself is always non-interactive
          transition: 'opacity 0.2s ease-in-out' // Smooth fade effect
        }}
      >
        {Object.entries(entities).map(([id, entity]) => {
          const WidgetComponent = WIDGETS[entity.type] || TextWidget;
          return (
            <div 
              key={id} 
              id={`hud-entity-${id}`}
              className="hud-entity" 
              style={{
                position: 'fixed',
                top: '-1000px',
                left: '-1000px',
                padding: '15px',
                background: 'rgba(5, 5, 5, 0.2)', 
                border: '1px solid cyan',
                borderRadius: '8px', 
                color: 'cyan', 
                fontFamily: 'monospace',
                minWidth: '100px', 
                pointerEvents: isVisible ? 'auto' : 'none', // Only clickable when visible
                backdropFilter: 'blur(3px)'
              }}
            >
              <div style={{ fontSize: '9px', opacity: 0.5, marginBottom: '8px' }}>{id}</div>
              <WidgetComponent 
                data={entity.value} 
                onRemove={() => removeEntity(id)} 
              />
            </div>
          );
        })}
      </div>

      {/* 2. THE SYSTEM LOG (SUBCONSCIOUS) */}
      <div 
        ref={systemLogRef} 
        id="hud-system-log" 
        className="hud-overlay"
        style={{
          position: 'fixed',
          pointerEvents: isVisible ? 'auto' : 'none',
          left: '30px',
          bottom: '30px',
          // NEW: Control visibility via CSS
          opacity: isVisible ? 1 : 0,
          visibility: isVisible ? 'visible' : 'hidden',
          transition: 'opacity 0.2s ease-in-out'
        }}
      >
        <div className="hud-header">
          <span className="hud-title">System Subconscious</span>
          <div className="hud-status-indicator pulse"></div>
        </div>
        
        <div className="hud-logs-container">
          {systemLogs.map((log, index) => 
            // Skip rendering for both direct_result and hud_update types
            (log.type === "direct_result" || log.type === "hud_update") ? null : (
              <div key={index} className="hud-log-entry">
                {log.type && (
                  <span style={{ color: '#fff', marginRight: '8px', fontWeight: 'bold' }}>
                    [{log.type.toUpperCase()}]
                  </span>
                )}
                <span className="log-message">
                  {typeof log.content === 'string' ? log.content : JSON.stringify(log.data || log)}
                </span>
              </div>
            )
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </>
  );
};

export default SystemHud;