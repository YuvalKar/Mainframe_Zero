// src/components/StaticHud.jsx
import { useState, useEffect } from 'react';
import './StaticHud.css';

// --- Shared Placeholder SVG Component ---
// This acts as the background for our widgets until you create the real ones.
const PlaceholderBg = ({ color }) => (
  <svg className="hud-widget-svg-bg" preserveAspectRatio="none" viewBox="0 0 100 100">
    <rect 
      x="1" y="1" width="98" height="98" 
      fill={color} fillOpacity="0.1" 
      stroke={color} strokeWidth="2" strokeDasharray="4 4" 
    />
  </svg>
);

// --- Refactored HTML Widgets ---

const TextWidget = ({ data, level, defaultColor }) => {
  // Choose color based on the level
  const color = level === 'error' ? '#ff4a4a' : level === 'warning' ? '#ffcc00' : defaultColor;
  const textValue = data?.value || "NO TEXT";

  return (
    <div className="hud-widget-wrapper" style={{ color: color }}>
      <PlaceholderBg color={color} />
      <div className="hud-widget-content">
        <span className="hud-text-truncate">{textValue}</span>
      </div>
    </div>
  );
};

const GaugeWidget = ({ data, defaultColor }) => {
  const val = typeof data?.value === 'number' ? data.value : 50;
  const label = data?.label || 'LOD';

  return (
    <div className="hud-widget-wrapper" style={{ color: defaultColor, minHeight: '50px' }}>
      <PlaceholderBg color={defaultColor} />
      <div className="hud-widget-content">
        <div className="hud-text-truncate" style={{ marginBottom: '4px', fontSize: '12px' }}>
          {label}: {val}%
        </div>
        <div style={{ background: 'rgba(0,0,0,0.5)', width: '100%', height: '8px', overflow: 'hidden' }}>
          <div style={{ background: defaultColor, width: `${val}%`, height: '100%' }} />
        </div>
      </div>
    </div>
  );
};

// --- New Worker Widget ---
// Behaving like a Gauge for now until customized
const WorkerWidget = ({ data, defaultColor }) => {
  const val = typeof data?.value === 'number' ? data.value : 0;
  const label = data?.label || 'WORKER';

  return (
    <div className="hud-widget-wrapper" style={{ color: defaultColor, minHeight: '50px' }}>
      <PlaceholderBg color={defaultColor} />
      <div className="hud-widget-content">
        <div className="hud-text-truncate" style={{ marginBottom: '4px', fontSize: '12px' }}>
          {label}: {val}%
        </div>
        <div style={{ background: 'rgba(0,0,0,0.5)', width: '100%', height: '8px', overflow: 'hidden' }}>
          <div style={{ background: defaultColor, width: `${val}%`, height: '100%' }} />
        </div>
      </div>
    </div>
  );
};

const TimerWidget = ({ data, onRemove, defaultColor }) => {
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
    <div className="hud-widget-wrapper" style={{ color: defaultColor }}>
      <PlaceholderBg color={defaultColor} />
      <div className="hud-widget-content" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="hud-text-truncate" style={{ paddingRight: '10px' }}>{label}</span>
        <strong>{timeLeft}s</strong>
      </div>
    </div>
  );
};

const ErrorWidget = ({ data }) => {
  const errorCode = data?.code ? `[${data.code}]` : '';
  const errorMessage = data?.value || "Unknown System Error";
  const color = '#ff4a4a'; // Force red for errors

  return (
    <div className="hud-widget-wrapper" style={{ color: color, minHeight: '60px' }}>
      <PlaceholderBg color={color} />
      <div className="hud-widget-content">
        <div className="hud-text-truncate" style={{ fontSize: '10px', fontWeight: 'bold' }}>
          SYS.ERROR {errorCode}
        </div>
        <div className="hud-text-truncate">{errorMessage}</div>
      </div>
    </div>
  );
};

const WIDGETS = {
  "TEXT": TextWidget,
  "GAUGE": GaugeWidget,
  "TIMER": TimerWidget,
  "ERROR": ErrorWidget,
  "WORKER": WorkerWidget
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

  // Filter entities by type to distribute them to their test zones
  const textEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "TEXT");
  const errorEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "ERROR");
  const timerEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "TIMER");
  const gaugeEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "GAUGE");
  const workerEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "WORKER");

  // If hidden, render nothing
  if (!isVisible) return null;

  return (
    <div className="static-hud-overlay">
      
      {/* Container holding all our anchor zones */}
      <div className="hud-anchors-container">
        
        {/* Top Left Anchor - Displaying Timers widgets */}
        <div className="hud-anchor-zone zone-top-left">
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px' }}>TOP LEFT ZONE (Timers)</div>
           {timerEntities.map(([id, entity]) => (
             <TimerWidget key={id} data={entity.payload} onRemove={() => removeEntity(id)} defaultColor={appColor} />
           ))}
        </div>

        {/* Top Right Anchor - Displaying Workers widgets */}
        <div className="hud-anchor-zone zone-top-right">
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px' }}>TOP RIGHT ZONE (Workers)</div>
           {workerEntities.map(([id, entity]) => (
             <WorkerWidget key={id} data={entity.payload} defaultColor={appColor} />
           ))}
        </div>   

        {/* Left Anchor - Displaying ERROR widgets */}
        <div className="hud-anchor-zone zone-error">
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px' }}>LEFT ZONE (ERRORS)</div>
           {errorEntities.map(([id, entity]) => (
             <ErrorWidget key={id} data={entity.payload} />
           ))}
        </div>        

        {/* Mid Anchor - Displaying text widgets */}
        <div className="hud-anchor-zone zone-mid">
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px' }}>MID ZONE (TEXT)</div>
           {textEntities.map(([id, entity]) => (
             <TextWidget key={id} data={entity.payload} level={entity.level} defaultColor={appColor} />
           ))}
        </div>

        {/* Bottom Anchor - Displaying GAUGE widgets */}
        <div className="hud-anchor-zone zone-bottom">
           <div style={{ color: 'white', fontWeight: 'bold', fontSize: '12px' }}>BOTTOM ZONE (GAUGES)</div>
           {gaugeEntities.map(([id, entity]) => (
             <GaugeWidget key={id} data={entity.payload} defaultColor={appColor} />
           ))}
        </div>

      </div>

      {/* HUD LEFT SIDE: Positioned using a wrapping div */}
      <div style={{ 
        position: 'absolute', 
        left: '20%', 
        top: '70%', 
        width: '110vh', 
        height: '110vh', 
        transform: 'translate(-50%, -50%)',
        zIndex: 1, 
        pointerEvents: 'none' 
      }}>
        
        <svg viewBox="-500 -500 1000 1000" width="100%" height="100%" overflow="visible">
          <g className="hud-left-group" stroke={appColor} fill="none">
            <circle cx="0" cy="0" r="490" strokeWidth="1" opacity="0.2" />
            <path 
              d="M -255 -441.7 A 510 510 0 0 1 441.7 255" 
              strokeWidth="2" 
              strokeDasharray="15 10 5 10" 
              className="hud-spin-slow" 
            />
            <path 
              d="M 92.0 -521.9 A 530 530 0 0 1 498.0 181.3"
              strokeWidth="12" 
              strokeDasharray="60 12" 
              className="hud-spin-fast-reverse" 
            />
            <line x1="-50" y1="0" x2="-20" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="20" y1="0" x2="50" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="-50" x2="0" y2="-20" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="20" x2="0" y2="50" strokeWidth="1" opacity="0.4" />
          </g>
        </svg>
      </div>  

      {/* --- Top connection indicator --- */}
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style={{ position: 'absolute', zIndex: 1, pointerEvents: 'none' }}>
        <g className="hud-right-group" stroke={appColor} fill="none">
          <rect x="calc( 155px)" y="24" width="15" height="15" fill={appColor} className="hud-blink" stroke="none" />
          <rect x="calc( 135px)" y="24" width="15" height="15" fill="#4fa72e" stroke="none" />
          <rect x="calc( 115px)" y="24" width="15" height="15" fill="#4fa72e" opacity="0.3" stroke="none" />
        </g>
      </svg>
    </div>
  );
}