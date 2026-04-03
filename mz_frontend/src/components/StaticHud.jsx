// src/components/StaticHud.jsx
import { useState, useEffect, useRef } from 'react';

import './StaticHud.css';

// --- Shared Placeholder SVG Component ---
const PlaceholderBg = ({ color }) => (
  <svg className="hud-widget-svg-bg" preserveAspectRatio="none" viewBox="0 0 100 100">
    <rect 
      x="1" y="1" width="98" height="98" 
      fill={color} fillOpacity="0.1" 
      stroke={color} strokeWidth="2" strokeDasharray="4 4" 
    />
  </svg>
);

// --- Widgets ---
const TextWidget = ({ data, level, defaultColor }) => {
  const color = level === 'error' ? '#ff4a4a' : level === 'warning' ? '#ffcc00' : defaultColor;
  const textValue = data?.value || "NO TEXT";

  return (
    <div className="hud-widget-wrapper" style={{ color }}>
      {/* Use the new background div instead of PlaceholderBg */}
      <div className="hud-widget-background" style={{ borderColor: color }} />
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
    <div className="hud-widget-wrapper widget-gauge-wrapper" style={{ color: defaultColor }}>
      {/* --- Replaced PlaceholderBg with DIVs --- */}
      <div className="hud-widget-background" style={{ borderColor: defaultColor }} />
      <div className="hud-widget-content">
        <div className="hud-text-truncate widget-gauge-label">
          {label}: {val}%
        </div>
        <div className="widget-gauge-track">
          <div className="widget-gauge-fill" style={{ background: defaultColor, width: `${val}%` }} />
        </div>
      </div>
    </div>
  );
};


const WorkerWidget = ({ data, defaultColor }) => {
  const val = typeof data?.value === 'number' ? data.value : 0;
  const label = data?.label || 'WRK'; 

  return (
    <div className="hud-widget-wrapper widget-worker-wrapper" style={{ color: defaultColor }}>
      {/* --- Replaced PlaceholderBg with DIVs --- */}
      <div className="hud-widget-background" style={{ borderColor: defaultColor }} />
      <div className="hud-widget-content widget-worker-content">
        <div className="hud-text-truncate widget-worker-label">
          {label}
        </div>
        
        <div className="widget-worker-track">
          <div className="widget-worker-fill" style={{ background: defaultColor, height: `${val}%` }} />
        </div>
        
        <div className="widget-worker-value">
          {val}%
        </div>
      </div>
    </div>
  );
};

const TimerWidget = ({ data, onRemove, defaultColor }) => {
  const label = data?.label || "TASK";
  
  // We use refs instead of state. Changing a ref DOES NOT trigger a re-render.
  const timeLeftRef = useRef(data?.value || 5);
  // This ref will point directly to the HTML DOM element (the div showing the number)
  const displayRef = useRef(null);

  useEffect(() => {
    // Update the ref value if parent passes a new data.value
    if (data?.value !== undefined) {
      timeLeftRef.current = data.value;
      if (displayRef.current) {
        displayRef.current.textContent = timeLeftRef.current;
      }
    }
  }, [data?.value]);

  useEffect(() => {
    const timerId = setInterval(() => {
      // Decrease the internal value
      timeLeftRef.current -= 1;

      // Direct DOM manipulation - Vanilla JS inside React!
      if (displayRef.current) {
        displayRef.current.textContent = timeLeftRef.current;
      }

      // Check if time is up
      if (timeLeftRef.current <= 0) {
        clearInterval(timerId);
        onRemove?.();
      }
    }, 1000);

    return () => clearInterval(timerId);
  }, [onRemove]);

  return (
    <div className="hud-widget-wrapper widget-timer-wrapper" style={{ color: defaultColor }}>
      <div className="hud-widget-background" style={{ borderColor: defaultColor }} />
      <div className="hud-widget-content widget-timer-content">
        
        <div className="widget-timer-circle" style={{ color: defaultColor }}>
          
          <div className="widget-timer-spinner">
            {/* We can use the existing efficient-spin class we already have in CSS */}
            <svg 
              viewBox="0 0 50 50" 
              className="hud-efficient-spin" 
            >
              <use href="/nbaya_timer.svg#timer-ring" />
            </svg>
          </div>

          {/* We attach the ref to this div. React will render it once, and then we take over. */}
          <div className="widget-timer-value" ref={displayRef}>
            {timeLeftRef.current}
          </div>
          
        </div>

        <span className="hud-text-truncate widget-timer-label">
          {label}
        </span>
      </div>
    </div>
  );
};

const ErrorWidget = ({ data }) => {
  const errorCode = data?.code ? `[${data.code}]` : '';
  const errorMessage = data?.value || "Unknown System Error";
  const color = '#ff4a4a'; 

  return (
    <div className="hud-widget-wrapper widget-error-wrapper" style={{ color }}>
      {/* Use the new background div with the error color */}
      <div className="hud-widget-background" style={{ borderColor: color }} />
      <div className="hud-widget-content">
        <div className="hud-text-truncate widget-error-label">
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

  useEffect(() => {
    if (latestMessage && latestMessage.type === "hud_update") {
      const log = latestMessage;
      
      setEntities(prev => {
        const next = { ...prev };
        
        if (log.action === "delete") {
          delete next[log.id];
        } 
        else if (log.action === "upsert") {
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

  const removeEntity = (idToRemove) => {
    setEntities(prev => {
      const next = { ...prev };
      delete next[idToRemove];
      return next;
    });
  };

  const textEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "TEXT");
  const errorEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "ERROR");
  const timerEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "TIMER");
  const gaugeEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "GAUGE");
  const workerEntities = Object.entries(entities).filter(([_, entity]) => entity.type === "WORKER");

  if (!isVisible) return null;

  return (
    <div className="static-hud-overlay">
      
      <div className="hud-anchors-container">
        
        <div className="hud-anchor-zone zone-top-left">
           {timerEntities.map(([id, entity]) => (
             <TimerWidget key={id} data={entity.payload} onRemove={() => removeEntity(id)} defaultColor={appColor} />
           ))}
        </div>

        <div className="hud-anchor-zone zone-top-right">
           {workerEntities.map(([id, entity]) => (
             <WorkerWidget key={id} data={entity.payload} defaultColor={appColor} />
           ))}
        </div>   

        <div className="hud-anchor-zone zone-error">
           {errorEntities.map(([id, entity]) => (
             <ErrorWidget key={id} data={entity.payload} />
           ))}
        </div>        

        <div className="hud-anchor-zone zone-mid">
           {textEntities.map(([id, entity]) => (
             <TextWidget key={id} data={entity.payload} level={entity.level} defaultColor={appColor} />
           ))}
        </div>

        <div className="hud-anchor-zone zone-bottom">
           {gaugeEntities.map(([id, entity]) => (
             <GaugeWidget key={id} data={entity.payload} defaultColor={appColor} />
           ))}
        </div>

      </div>

      <div className="hud-left-decoration">
        <svg viewBox="-500 -500 1000 1000" width="100%" height="100%" overflow="visible">
          <g className="hud-left-group" stroke={appColor} fill="none">
            <circle cx="0" cy="0" r="490" strokeWidth="1" opacity="0.2" />
            <circle cx="0" cy="0" r="530" fill="none" className="hud-spin-fast-reverse" stroke={appColor} strokeWidth="3" strokeDasharray="60 12 10 12" />
            <circle cx="0" cy="0" r="510" fill="none" className="hud-spin-slow" stroke={appColor} strokeWidth="15" strokeDasharray="20 5 20 5 20 500" />

            <line x1="-50" y1="0" x2="-20" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="20" y1="0" x2="50" y2="0" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="-50" x2="0" y2="-20" strokeWidth="1" opacity="0.4" />
            <line x1="0" y1="20" x2="0" y2="50" strokeWidth="1" opacity="0.4" />
          </g>
        </svg>
      </div>  

      <svg className="hud-top-indicator" xmlns="http://www.w3.org/2000/svg">
        <g className="hud-right-group" stroke={appColor} fill="none">
          <rect x="calc(155px)" y="24" width="15" height="15" fill={appColor} className="hud-blink" stroke="none" />
          <rect x="calc(135px)" y="24" width="15" height="15" fill="#4fa72e" stroke="none" />
          <rect x="calc(115px)" y="24" width="15" height="15" fill="#4fa72e" opacity="0.3" stroke="none" />
        </g>
      </svg>
    </div>
  );
}