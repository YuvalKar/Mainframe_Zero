import { useEffect, useRef } from 'react';
import Matter from 'matter-js';

// Constant for the special ID of the central log HUD
const SYSTEM_LOG_ID = "system_log";

// Custom Hook to handle HUD physics, including dragging, via Matter.js
export const useHudPhysics = (entities, systemLogRef) => {
  const engineRef = useRef(Matter.Engine.create({ enableSleeping: true }));
  const bodiesRef = useRef({}); // Mapping: { entityId or SYSTEM_LOG_ID: MatterBody }

  // Variables to manage user interaction / dragging
  const draggedBodyRef = useRef(null);
  const dragOffsetRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const engine = engineRef.current;
    engine.gravity.y = 0; 
    engine.gravity.x = 0; 

    const world = engine.world;
    const runner = Matter.Runner.create();
    Matter.Runner.run(runner, engine);

    // 1. Initialize the special body for the central log HUD
    // It spawns at the bottom-left, like its old static CSS position
    const logWidth = 800; // Match CSS width
    const logHeight = 400; // Estimated height, can be dynamic later
    const logBody = Matter.Bodies.rectangle(logWidth / 2 + 30, window.innerHeight - logHeight / 2 - 150, logWidth, logHeight, { 
      restitution: 0.1, // Low bounce so it settles down quickly
      frictionAir: 0.05,
      mass: 5, // Make it heavier so it's harder to push
      label: SYSTEM_LOG_ID,
      chamfer: { radius: 12 }, // rounded corners for better collision feel
    });

    bodiesRef.current[SYSTEM_LOG_ID] = logBody;
    Matter.World.add(world, logBody);

    // 2. Apply custom physics rules before every engine tick
    const handleBeforeUpdate = () => {
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;

      Object.values(bodiesRef.current).forEach(body => {
        // Skip central gravity for the body currently being dragged
        if (draggedBodyRef.current && draggedBodyRef.current.id === body.id) return;

        // SKIP: Skip sleeping bodies to save CPU cycles
        if (body.isSleeping) return;

        // CENTRAL GRAVITY: Apply a gentle pull towards the center
        // Increase the factor slightly as it's harder to push dynamic HUD
        const forceMagnitude = 0.00008 * body.mass;
        Matter.Body.applyForce(body, body.position, {
          x: (centerX - body.position.x) * forceMagnitude,
          y: (centerY - body.position.y) * forceMagnitude
        });

        // AUTO-SLEEP: Force sleep if speed drops below threshold to prevent eternal jittering
        if (body.speed < 0.05) {
          Matter.Sleeping.set(body, true);
        }
      });
    };

    Matter.Events.on(engine, 'beforeUpdate', handleBeforeUpdate);

    // 3. The main rendering loop - updating DOM nodes directly
    const update = () => {
      Object.entries(bodiesRef.current).forEach(([id, body]) => {
        // Find the element - either dynamic entity OR the special log overlay
        const element = (id === SYSTEM_LOG_ID) 
          ? (systemLogRef.current) 
          : (document.getElementById(`hud-entity-${id}`));

        if (element) {
          // Direct DOM manipulation based on physics body coordinates
          element.style.left = `${body.position.x}px`;
          element.style.top = `${body.position.y}px`;
          // Omitted rotation for readability, can be added back if spinning widgets are desired
          element.style.transform = `translate(-50%, -50%)`;
        }
      });
      requestAnimationFrame(update);
    };

    const animationId = requestAnimationFrame(update);

    // Cleanup on unmount
    return () => {
      cancelAnimationFrame(animationId);
      Matter.Events.off(engine, 'beforeUpdate', handleBeforeUpdate);
      Matter.Runner.stop(runner);
      Matter.Engine.clear(engine);
    };
  }, []); // Run once on initialization

  // Sync React entities state with Matter.js bodies
  useEffect(() => {
    const world = engineRef.current.world;
    let ecosystemChanged = false;

    // Add new dynamic dynamic entity bodies
    Object.keys(entities).forEach((id) => {
      if (!bodiesRef.current[id]) {
        ecosystemChanged = true;
        
        // Spawn in a wide circle around the center
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const radius = 300; 
        const angle = Math.random() * Math.PI * 2;
        
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        
        // Dynamic dynamic entity bodies
        const body = Matter.Bodies.rectangle(x, y, 200, 80, { 
          restitution: 0.2, 
          frictionAir: 0.05,
          label: id 
        });

        // Give it an initial kick towards the center
        const pushMagnitude = 0.02;
        Matter.Body.applyForce(body, body.position, {
          x: (centerX - x) * pushMagnitude,
          y: (centerY - y) * pushMagnitude
        });

        bodiesRef.current[id] = body;
        Matter.World.add(world, body);
      }
    });

    // Remove deleted dynamic entity bodies
    Object.keys(bodiesRef.current).forEach((id) => {
      if (id === SYSTEM_LOG_ID) return; // Never remove the system log body
      if (!entities[id]) {
        ecosystemChanged = true;
        Matter.World.remove(world, bodiesRef.current[id]);
        delete bodiesRef.current[id];
      }
    });

    // If bodies were added or removed, wake everyone up to rearrangement and avoid getting stuck
    if (ecosystemChanged) {
      Object.values(bodiesRef.current).forEach(body => {
        Matter.Sleeping.set(body, false);
      });
    }
  }, [entities]);

  // Handle Drag & Drop interaction on DOM elements
  useEffect(() => {
    const world = engineRef.current.world;

    const handleMouseDown = (event) => {
      // Find the parent element that holds the ID (either .hud-entity or .hud-overlay)
      const element = event.target.closest('.hud-entity, .hud-overlay');
      if (!element) return;

      // Check if it's dynamic dynamic entity or the log overlay
      let bodyId = null;
      if (element.classList.contains('hud-entity')) {
        bodyId = element.id.replace('hud-entity-', '');
      } else if (element.classList.contains('hud-overlay') && element.id === "hud-system-log") {
        bodyId = SYSTEM_LOG_ID;
      }

      const body = bodiesRef.current[bodyId];
      if (body) {
        draggedBodyRef.current = body;
        // Calculate offset between mouse click and body center
        dragOffsetRef.with({
          x: event.clientX - body.position.x,
          y: event.clientY - body.position.y
        });

        // Wake up everyone else so they rearrange around the dragged body
        Object.values(bodiesRef.current).forEach(b => {
          Matter.Sleeping.set(b, false);
        });

        // IMPORTANT: Temporarily disable static flag or manual positioning can fail
        // However, making it static avoids internal forces during drag. 
        // We chose manual positioning, so we make it static.
        Matter.Body.with(body, { isStatic: true });
      }
    };

    const handleMouseMove = (event) => {
      if (draggedBodyRef.current) {
        // Manually set body position based on mouse - offset
        Matter.Body.setPosition(draggedBodyRef.current, {
          x: event.clientX - dragOffsetRef.current.x,
          y: event.clientY - dragOffsetRef.current.y
        });
      }
    };

    const handleMouseUp = () => {
      if (draggedBodyRef.current) {
        // Stop dragging, make the body dynamic again so it can be pushed
        Matter.Body.set(draggedBodyRef.current, { isStatic: false });
        draggedBodyRef.current = null;
      }
    };

    // Add global mouse listeners
    window.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // Cleanup listeners
    return () => {
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return null;
};