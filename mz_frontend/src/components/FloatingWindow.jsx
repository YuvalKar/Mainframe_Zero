// src/components/floating/FloatingWindow.jsx
import React, { useState, useEffect, useRef } from 'react';
import './FloatingWindow.css';

export default function FloatingWindow({ 
  children, 
  color = '#4da8da', // Default fallback color
  initialPosition = { x: 50, y: 50 },
  topDecoration, 
  bottomDecoration, 
  closeButtonPos = { top: 10, right: 10 }, // Independent absolute positioning for the X button
  contentMarginTop = 40, // Space to clear the absolute top decoration
  maxContentHeight = '400px', // Developer controls the dynamic height limit
  width = '400px', // Developer controls the wrapper width
  onClose, 
  isVisible = true,
  className = ''
}) {
  const [position, setPosition] = useState(initialPosition);
  const [isDragging, setIsDragging] = useState(false);
  const offset = useRef({ x: 0, y: 0 });

  // --- Dragging Logic ---
  const handleMouseDown = (e) => {
    // We only initiate drag if the user clicked inside the dedicated drag zone
    if (e.target.closest('.fw-drag-zone')) {
      setIsDragging(true);
      offset.current = {
        x: e.clientX - position.x,
        y: e.clientY - position.y
      };
    }
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - offset.current.x,
      y: e.clientY - offset.current.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Bind global mouse events only when dragging is active
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return (
      <div 
        className={`fw-main-wrapper ${className}`}
        style={{
          display: isVisible ? 'flex' : 'none', /* <--- הוספנו את השורה הזו */
          left: `${position.x}px`,
          top: `${position.y}px`,
          width: width,
          '--fw-theme-color': color
        }}
      >
      {/* --- 1. Absolute Top Layer (Drag Zone & Close Button) --- */}
      <div className="fw-absolute-top">
        
        {/* The Drag Handle area wraps the top decoration */}
        <div 
          className="fw-drag-zone" 
          onMouseDown={handleMouseDown}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          {topDecoration}
        </div>

        {/* The Close Button sits completely independent of the drag zone layout */}
        {onClose && (
          <button 
            className="fw-close-btn" 
            onClick={onClose}
            style={{
              top: `${closeButtonPos.top}px`,
              right: `${closeButtonPos.right}px`
            }}
            title="Close"
          >
            ×
          </button>
        )}
      </div>

      {/* --- 2. Dynamic Scrollable Content Area --- */}
      <div 
        className="fw-content-box" 
        style={{ 
          marginTop: `${contentMarginTop}px`,
          maxHeight: maxContentHeight
        }}
      >
        {children}
      </div>

      {/* --- 3. Bottom Flowing Layer --- */}
      {bottomDecoration && (
        <div className="fw-bottom-wrapper">
          {/* This inner div allows absolute fine-tuning of the bottom SVG */}
          <div className="fw-bottom-absolute-nudge">
            {bottomDecoration}
          </div>
        </div>
      )}
    </div>
  );
}