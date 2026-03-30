import { useEffect, useRef } from 'react';

// A lightweight hook for simple drag-and-drop, bypassing physics engines
export const useDraggable = (entities, systemLogRef) => {
  const draggedElementRef = useRef(null);

  // 1. Handle drag events
  useEffect(() => {
    const handleMouseDown = (e) => {
      // Find if we clicked on a draggable HUD element
      const element = e.target.closest('.hud-entity, .hud-overlay');
      if (!element) return;

      draggedElementRef.current = element;
      
      // Bring the dragged element to the front
      element.style.zIndex = "10000";

      // If the element is still in its initial "hidden" state, calculate its current real position
      if (!element.style.left || element.style.left === '-1000px') {
        const rect = element.getBoundingClientRect();
        element.style.left = `${rect.left}px`;
        element.style.top = `${rect.top}px`;
        // Remove transform so manual left/top tracking works perfectly with mouse movement
        element.style.transform = 'none'; 
      }
    };

    const handleMouseMove = (e) => {
      if (!draggedElementRef.current) return;

      const element = draggedElementRef.current;
      
      // Get current coordinates
      const currentLeft = parseFloat(element.style.left) || 0;
      const currentTop = parseFloat(element.style.top) || 0;

      // Add the mouse movement delta (movementX/movementY) to the element's position
      element.style.left = `${currentLeft + e.movementX}px`;
      element.style.top = `${currentTop + e.movementY}px`;
    };

    const handleMouseUp = () => {
      if (draggedElementRef.current) {
        // Reset z-index so it doesn't stay permanently above everything
        draggedElementRef.current.style.zIndex = "9998";
        draggedElementRef.current = null;
      }
    };

    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  // 2. Spawn new entities in the center initially
  useEffect(() => {
    Object.keys(entities).forEach(id => {
      const element = document.getElementById(`hud-entity-${id}`);
      // If it's a newly created element, move it from -1000px to the center
      if (element && element.style.left === '-1000px') {
         // Scatter them slightly around the center so they don't perfectly overlap
         const offsetX = Math.random() * 40 - 20;
         const offsetY = Math.random() * 40 - 20;
         
         element.style.left = `${window.innerWidth / 2 + offsetX}px`;
         element.style.top = `${window.innerHeight / 2 + offsetY}px`;
         element.style.transform = 'translate(-50%, -50%)';
      }
    });
  }, [entities]);

  return null;
};