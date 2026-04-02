// src/components/StaticHud.jsx
import { useState, useEffect } from 'react';
import './StaticHud.css';

export default function StaticHud({ appColor = "#4da8da" }) {
  // Controlled by Ctrl+Shift+H
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey && e.shiftKey && (e.key === 'h' || e.key === 'H')) {
        setIsVisible(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // If hidden, render nothing
  if (!isVisible) return null;

  return (
    <div className="static-hud-overlay">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        
        {/* --- LEFT SIDE: Circular Animation (Over the AI Terminal) --- */}
        {/* Placed at x=150, y=150 so it floats nicely in the top-left area */}
        <g className="hud-left-group" transform="translate(150, 150)" stroke={appColor} fill="none">
          
          {/* Outer static thin ring */}
          <circle cx="0" cy="0" r="70" strokeWidth="1" opacity="0.2" />
          
          {/* Middle dashed spinning ring */}
          <circle 
            cx="0" cy="0" r="55" 
            strokeWidth="2" 
            strokeDasharray="15 10 5 10" 
            className="hud-spin-slow" 
          />
          
          {/* Inner dotted spinning ring (rotates in reverse) */}
          <circle 
            cx="0" cy="0" r="40" 
            strokeWidth="3" 
            strokeDasharray="4 8" 
            className="hud-spin-fast-reverse" 
          />
          
          {/* Center pulsating dot */}
          <circle cx="0" cy="0" r="5" fill={appColor} className="hud-pulse" stroke="none" />
          
          {/* Crosshairs */}
          <line x1="-80" y1="0" x2="-20" y2="0" strokeWidth="1" opacity="0.4" />
          <line x1="20" y1="0" x2="80" y2="0" strokeWidth="1" opacity="0.4" />
          <line x1="0" y1="-80" x2="0" y2="-20" strokeWidth="1" opacity="0.4" />
          <line x1="0" y1="20" x2="0" y2="80" strokeWidth="1" opacity="0.4" />
        </g>

        {/* --- RIGHT SIDE: Indicators & Data (Over the Tools Panel) --- */}
        <g className="hud-right-group" stroke={appColor} fill="none">
          {/* Decorative frame lines anchored to the right edge */}
          <polyline points="calc(100% - 20),100 calc(100% - 20),20 calc(100% - 120),20" strokeWidth="2" opacity="0.8" />
          <line x1="calc(100% - 20)" y1="120" x2="calc(100% - 20)" y2="250" strokeWidth="1" opacity="0.3" strokeDasharray="4 4" />
          
          {/* Status bars */}
          <rect x="calc(100% - 85)" y="35" width="15" height="4" fill={appColor} className="hud-blink" stroke="none" />
          <rect x="calc(100% - 65)" y="35" width="15" height="4" fill={appColor} stroke="none" />
          <rect x="calc(100% - 45)" y="35" width="15" height="4" fill={appColor} opacity="0.3" stroke="none" />
          
          {/* Mock Text Data - using textAnchor="end" to align properly from the right */}
          <text x="calc(100% - 30)" y="65" fill={appColor} fontSize="11" fontFamily="var(--font-delicate)" stroke="none" letterSpacing="1" textAnchor="end">
            SYS.STATUS: ONLINE
          </text>
          <text x="calc(100% - 30)" y="85" fill={appColor} fontSize="11" fontFamily="var(--font-delicate)" stroke="none" letterSpacing="1" textAnchor="end">
            MEM.CORE: STABLE
          </text>
        </g>

        {/* --- BOTTOM: Subtle horizon line --- */}
        <g className="hud-bottom-group" stroke={appColor} fill="none">
          <line x1="5%" y1="calc(100% - 30px)" x2="95%" y2="calc(100% - 30px)" strokeWidth="1" opacity="0.1" />
        </g>

      </svg>
    </div>
  );
}