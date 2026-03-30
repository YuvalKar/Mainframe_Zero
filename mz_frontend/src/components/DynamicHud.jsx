import React, { useState, useEffect } from 'react';

// --- WIDGET FACTORY ---

const TextWidget = ({ data }) => (
  <div style={{ color: '#00ffff' }}>{typeof data === 'object' ? JSON.stringify(data) : data}</div>
);

const GaugeWidget = ({ data }) => {
  // Assuming data is a number 0-100
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

const TimerWidget = ({ data }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
    <svg width="20" height="20" viewBox="0 0 20 20">
      <circle cx="10" cy="10" r="8" fill="none" stroke="cyan" strokeWidth="2" strokeDasharray="10 5">
        <animateTransform attributeName="transform" type="rotate" from="0 10 10" to="360 10 10" dur="2s" repeatCount="indefinite" />
      </circle>
    </svg>
    <span>{data}</span>
  </div>
);

// Map of types to components
const WIDGETS = {
  "TEXT": TextWidget,
  "GAUGE": GaugeWidget,
  "TIMER": TimerWidget
};

const DynamicHud = ({ systemLogs = [] }) => {
  const [entities, setEntities] = useState({});
  const [isVisible, setIsVisible] = useState(true); // Toggle for visibility

  // Keyboard toggle logic (Ctrl + Shift + D)
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Supporting both English 'd' and Hebrew 'ג'
      if (event.ctrlKey && event.shiftKey && (event.key.toLowerCase() === 'd' || event.key === 'ג')) {
        setIsVisible((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (systemLogs.length > 0) {
      const latest = systemLogs[systemLogs.length - 1];
      
      if (latest.type === "hud_update") {
        setEntities(prev => ({
          ...prev,
          [latest.id]: {
            type: latest.data.type || "TEXT", 
            value: latest.data.value,
            updatedAt: Date.now()
          }
        }));
      }
    }
  }, [systemLogs]);

  // If hidden, we don't render anything to the DOM
  if (!isVisible) return null;

  return (
    <div className="dynamic-hud-canvas" style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      width: '100vw', 
      height: '100vh', 
      pointerEvents: 'none', 
      zIndex: 10000 
    }}>
      {/* Indicator that Dynamic HUD is active (optional, for UX) */}
      <div style={{ 
        position: 'absolute', 
        top: '10px', 
        left: '50%', 
        transform: 'translateX(-50%)',
        fontSize: '10px',
        color: 'rgba(0, 255, 255, 0.3)',
        letterSpacing: '2px'
      }}>
        DYNAMIC HUD ACTIVE [CTRL+SHIFT+D TO HIDE]
      </div>

      {Object.entries(entities).map(([id, entity]) => {
        const WidgetComponent = WIDGETS[entity.type] || TextWidget;
        
        return (
          <div key={id} className="hud-entity" style={{
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            padding: '15px',
            background: 'rgba(0, 20, 20, 0.8)', 
            border: '1px solid cyan',
            borderRadius: '8px', 
            color: 'cyan', 
            fontFamily: 'monospace',
            transform: 'translate(-50%, -50%)', 
            minWidth: '180px', 
            pointerEvents: 'auto',
            transition: 'all 0.3s ease' // Smooth appearance
          }}>
            <div style={{ fontSize: '9px', opacity: 0.5, marginBottom: '8px' }}>{id}</div>
            <WidgetComponent data={entity.value} />
          </div>
        );
      })}
    </div>
  );
};

export default DynamicHud;