// src/components/StaticHud.jsx
import { useState, useEffect } from 'react';
import './StaticHud.css';

// --- Simple HTML Widgets with Bulletproof Data Binding ---

const TextWidget = ({ data, level }) => {
  // Choose color based on the level
  const color = level === 'error' ? '#ff4a4a' : level === 'warning' ? '#ffcc00' : 'currentColor';
  
  // Safe extraction with optional chaining
  const textValue = data?.value || "NO TEXT";

  return (
    <div style={{ background: 'rgba(0,0,0,0.6)', padding: '8px', marginBottom: '8px', borderLeft: `3px solid ${color}` }}>
      {textValue}
    </div>
  );
};

const GaugeWidget = ({ data }) => {
  // Safe extraction with optional chaining and type checking
  const val = typeof data?.value === 'number' ? data.value : 50;
  const label = data?.label || 'LOD';

  return (
    <div style={{ background: 'rgba(0,0,0,0.6)', padding: '8px', marginBottom: '8px', borderLeft: '3px solid currentColor' }}>
      <div style={{ marginBottom: '4px', fontSize: '12px' }}>{label}: {val}%</div>
      <div style={{ background: '#333', width: '100%', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ background: 'currentColor', width: `${val}%`, height: '100%' }} />
      </div>
    </div>
  );
};

const TimerWidget = ({ data, onRemove }) => {
  // Safe extraction with optional chaining
  const label = data?.label || "TASK";
  const [timeLeft, setTimeLeft] = useState(data?.value || 5);

  // Listen for new updates (upsert) from the server to update the time on the fly
  useEffect(() => {
    if (data?.value !== undefined) {
      setTimeLeft(data.value);
    }
  }, [data?.value]);

  // Local countdown
  useEffect(() => {
    if (timeLeft <= 0) {
      onRemove?.();
      return;
    }
    const timerId = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    return () => clearInterval(timerId);
  }, [timeLeft, onRemove]);

  return (
    <div style={{ background: 'rgba(0,0,0,0.6)', padding: '8px', marginBottom: '8px', borderLeft: '3px solid currentColor', display: 'flex', justifyContent: 'space-between' }}>
      <span>{label}</span>
      <strong>{timeLeft}s</strong>
    </div>
  );
};

const ErrorWidget = ({ data }) => {
  // Safe extraction with optional chaining
  const errorCode = data?.code ? `[${data.code}]` : '';
  const errorMessage = data?.value || "Unknown System Error";

  return (
    <div style={{ background: 'rgba(50,0,0,0.8)', padding: '8px', marginBottom: '8px', borderLeft: '3px solid #ff4a4a', color: '#ff4a4a' }}>
      <div style={{ fontSize: '10px', fontWeight: 'bold' }}>SYS.ERROR {errorCode}</div>
      <div>{errorMessage}</div>
    </div>
  );
};

const WIDGETS = {
  "TEXT": TextWidget,
  "GAUGE": GaugeWidget,
  "TIMER": TimerWidget,
  "ERROR": ErrorWidget
};


export default function StaticHud({ appColor = "#4da8da", latestMessage }) {
  const [isVisible, setIsVisible] = useState(true);
  const [entities, setEntities] = useState({});

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && (e.key === 'h' || e.key === 'H' || e.key === 'י')) {
        setIsVisible(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Listen only to the latest message and update the state directly
  useEffect(() => {
    if (latestMessage && latestMessage.type === "hud_update") {
      const log = latestMessage;
      
      setEntities(prev => {
        const next = { ...prev };
        
        if (log.action === "delete") {
          delete next[log.id];
        } 
        else if (log.action === "upsert") {
          // Merge new data with existing data, so partial updates won't overwrite existing info
          const existing = next[log.id] || {};
          next[log.id] = {
            ...existing,
            type: log.widget_type || existing.type || "TEXT",
            level: log.level || existing.level || "info",
            payload: { ...(existing.payload || {}), ...(log.payload || {}) },
            updatedAt: Date.now()
          };
        }
        
        return next;
      });
    }
  }, [latestMessage]);

  // Helper to remove an entity (used by timers when they finish)
  const removeEntity = (idToRemove) => {
    setEntities(prev => {
      const next = { ...prev };
      delete next[idToRemove];
      return next;
    });
  };

  // If hidden, render nothing
  if (!isVisible) return null;

  return (
    <div className="static-hud-overlay">
      
      {/* --- HTML DATA LAYER (Overlay) --- */}
      {/* Placed top-right for initial testing */}
      <div 
        className="hud-data-layer" 
        style={{ 
          position: 'absolute', 
          top: '30px', 
          right: '30px', 
          width: '250px',
          color: appColor, // Inherit app color for all widgets
          fontFamily: 'monospace',
          zIndex: 2 
        }}
      >
        {Object.keys(entities).length > 0 && (
          <div style={{ fontSize: '10px', opacity: 0.5, marginBottom: '10px', textAlign: 'right' }}>
            ACTIVE HUD ENTITIES
          </div>
        )}
        
        {Object.entries(entities).map(([id, entity]) => {
          const WidgetComponent = WIDGETS[entity.type] || TextWidget;
          return (
            <WidgetComponent 
              key={id}
              data={entity.payload} // Using payload properly now
              level={entity.level}  // Passing level for styling
              onRemove={() => removeEntity(id)} 
            />
          );
        })}
      </div>

      {/* HUD LEFT SIDE: Positioned using a wrapping div. 
        Adjust width/height here (e.g., 40vh) to scale the entire group perfectly.
      */}

      <div style={{ 
        position: 'absolute', 
        left: '20%', 
        top: '70%', 
        width: '110vh', 
        height: '110vh', 
        transform: 'translate(-50%, -50%)', // Centers the div exactly on the 25/50 mark
        zIndex: 1, 
        pointerEvents: 'none' 
      }}>
        
        {/* viewBox centers 0,0 right in the middle of a 1000x1000 canvas */}
        <svg viewBox="-500 -500 1000 1000" width="100%" height="100%" overflow="visible">
          <g className="hud-left-group" stroke={appColor} fill="none">
            
            {/* Full inner circle for reference */}
            <circle cx="0" cy="0" r="490" strokeWidth="1" opacity="0.2" />
            
            {/* Top-Right Arc 1. 
              Starts at (0, -510), ends at (510, 0)
            */}
            <path 
              d="M -255 -441.7 A 510 510 0 0 1 441.7 255" 
              strokeWidth="2" 
              strokeDasharray="15 10 5 10" 
              className="hud-spin-slow" 
            />
            
            {/* Top-Right Arc 2 (Thicker, different radius). 
              Starts at (0, -520), ends at (520, 0)
            */}
            <path 
              d="M 92.0 -521.9 A 530 530 0 0 1 498.0 181.3"
              strokeWidth="12" 
              strokeDasharray="60 12" 
              className="hud-spin-fast-reverse" 
            />
            
            {/* Center dot and crosshairs */}
            <line x1="-50" y1="0" x2="-20" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="20" y1="0" x2="50" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="-50" x2="0" y2="-20" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="20" x2="0" y2="50" strokeWidth="1" opacity="0.4" />
          </g>
        </svg>
      </div>  

      {/* --- SVG DECORATION LAYER --- */}
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style={{ position: 'absolute', zIndex: 1, pointerEvents: 'none' }}>
        
        {/* RIGHT SIDE: Fake Static Indicators (We'll replace these later) */}
        <g className="hud-right-group" stroke={appColor} fill="none">
          {/* Blinking blocks shifted left */}
          <rect x="calc( 155px)" y="24" width="15" height="15" fill={appColor} className="hud-blink" stroke="none" />
          <rect x="calc( 135px)" y="24" width="15" height="15" fill="#4fa72e" stroke="none" />
          <rect x="calc( 115px)" y="24" width="15" height="15" fill="#4fa72e" opacity="0.3" stroke="none" />
        </g>

      </svg>
    </div>
  );
}