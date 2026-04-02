import React, { useState, useEffect, useRef } from 'react';
import './SystemHud.css'; 
import { useDraggable } from '../hooks/useDraggable';
import { CornerGraphic } from './hud-graphics';

const hologramModules = import.meta.glob('../assets/holograms/*.svg', { 
  eager: true, 
  query: '?url', 
  import: 'default' 
});
const hologramStack = Object.values(hologramModules);

// --- WIDGET FACTORY ---
const TextWidget = ({ data }) => (
  <div className="fui-text-widget">
    {typeof data === 'object' ? JSON.stringify(data) : data}
  </div>
);

const GaugeWidget = ({ data }) => {
  const val = typeof data === 'number' ? data : 50;
  return (
    <div className="fui-gauge-container">
      <div className="fui-gauge-label">LOD: {val}%</div>
      <div className="fui-gauge-track">
        <div className="fui-gauge-fill" style={{ width: `${val}%` }} />
      </div>
    </div>
  );
};

const TimerWidget = ({ data, onRemove }) => {
  const initialTime = data?.time || 5;
  const text = data?.text || (typeof data === 'string' ? data : "TASK");
  
  const [timeLeft, setTimeLeft] = useState(initialTime);
  const [selectedImg, setSelectedImg] = useState(null);

  useEffect(() => {
    if (hologramStack.length > 0) {
      const randomIndex = Math.floor(Math.random() * hologramStack.length);
      setSelectedImg(hologramStack[randomIndex]);
    }
  }, []);

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

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.ctrlKey && event.shiftKey && (event.key.toLowerCase() === 'h' || event.key === 'י')) {
        setIsVisible((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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

  useEffect(() => {
    if (isVisible && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs, isVisible]);

  useDraggable(entities, systemLogRef);

  return (
    <>
      {/* 1. THE FLOATING ENTITIES (DYNAMIC HUD) */}
      <div 
        className="dynamic-hud-layer" 
        style={{ 
          opacity: isVisible ? 1 : 0,
          visibility: isVisible ? 'visible' : 'hidden',
          pointerEvents: isVisible ? 'none' : 'none', 
        }}
      >
        {Object.entries(entities).map(([id, entity]) => {
          const WidgetComponent = WIDGETS[entity.type] || TextWidget;
          const isTimer = entity.type === 'TIMER'; // Check if it's the naked hologram
          
          return (
            <div 
              key={id} 
              id={`hud-entity-${id}`}
              className={`hud-entity ${isTimer ? 'hologram-naked' : ''}`} 
              style={{
                position: 'fixed',
                top: '-1000px',
                left: '-1000px',
                pointerEvents: isVisible ? 'auto' : 'none', 
              }}
            >
              {/* --- ADDED GRAPHIC HERE: Render only if it's not a naked timer --- */}
              {!isTimer && <CornerGraphic className="fui-widget-corner" />}

              {!isTimer && <div className="hud-entity-id">ID:{id}</div>}
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
          pointerEvents: isVisible ? 'auto' : 'none',
          opacity: isVisible ? 1 : 0,
          visibility: isVisible ? 'visible' : 'hidden',
        }}
      >
        {/* <CornerGraphic className="hud-overlay-graphic" /> */}

        <div className="hud-header">
          <span className="hud-title">SYS.SUBCONSCIOUS</span>
          <div className="hud-status-indicator pulse"></div>
        </div>
        
        <div className="hud-logs-container">
          {systemLogs.map((log, index) => 
            (log.type === "direct_result" || log.type === "hud_update") ? null : (
              <div key={index} className="hud-log-entry">
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
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </>
  );
};

export default SystemHud;