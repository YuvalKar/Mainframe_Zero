// src/App.jsx
import { useState, useEffect, useRef } from 'react'
import './App.css'
import Terminal from './components/Terminal'
import FileExplorer from './components/FileExplorer'
import DocumentViewer from './components/DocumentViewer'
import SystemHud from './components/SystemHud'
import DynamicHud from './components/DynamicHud'

function App() {
  const [attentionShelf, setAttentionShelf] = useState([]);
  
  // 2. Add the state for the currently active document in the viewer
  const [activeDocument, setActiveDocument] = useState(null);
  // Add state to hold the currently selected text from the viewer
  const [selectedText, setSelectedText] = useState("");

  // Panel state
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const [isRightOpen, setIsRightOpen] = useState(false); 
  const [systemLogs, setSystemLogs] = useState([]);
  
  // Lifted WebSocket State
  const [isConnected, setIsConnected] = useState(false);
  const [latestMessage, setLatestMessage] = useState(null);
  const wsRef = useRef(null);

  // Centralized WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLatestMessage(data);

        // Add EVERY incoming message to the HUD subconscious log
        setSystemLogs(prevLogs => [...prevLogs, data]);

      } catch (err) {
        console.error("Parse error:", err);
      }
    };

    ws.onclose = () => setIsConnected(false);

    // Cleanup on unmount
    return () => ws.close();
  }, []);

  // Generic sender function passed to children
  const sendCommand = (payload) => {
    if (wsRef.current && isConnected) {
      
      // Enhance the payload with our current UI context
      const enhancedPayload = {
        ...payload,
        client_context: {
          activeDocument: activeDocument ? activeDocument.path : null,
          selectedText: selectedText || null,
          // Extract only the paths, and filter out the active document to avoid duplication
          attentionShelf: attentionShelf
            .filter(f => !activeDocument || f.path !== activeDocument.path)
            .map(f => f.path)
        }
      };

      // Optional: Log it just to see the magic happening before it leaves the browser
      console.log("Sending payload to server:", enhancedPayload);

      wsRef.current.send(JSON.stringify(enhancedPayload));
    }
  };

  const toggleAttention = (fileNode) => {
    setAttentionShelf(prev => {
      const exists = prev.find(f => f.path === fileNode.path);
      if (exists) {
        // 3. If removing from shelf, also clear the viewer if it was the active one
        if (activeDocument && activeDocument.path === fileNode.path) {
          setActiveDocument(null);
        }
        return prev.filter(f => f.path !== fileNode.path);
      } else {
        return [...prev, { ...fileNode, sent: false }];
      }
    });
  };

  // Calculate dynamic widths: Collapsed panels take exactly 4%
  const getColumnWidths = () => {
    const leftWidth = isLeftOpen ? 20 : 4;
    const rightWidth = isRightOpen ? (100 - leftWidth) / 2 : 4;
    const centerWidth = 100 - leftWidth - rightWidth;

    return {
      left: `${leftWidth}%`,
      center: `${centerWidth}%`,
      right: `${rightWidth}%`
    };
  };

  const widths = getColumnWidths();

  // Reusable style for the delicate toggle buttons
  const toggleButtonStyle = {
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: 'var(--text-muted)',
    fontSize: '1em',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
  };

  return (
    <div className="app-container">
      
      {/* LEFT COLUMN (File Explorer) */}
      <div className="column-panel left-column" style={{ width: widths.left }}>
        
        {/* Left Toggle Bar */}
        <div style={{ 
          display: 'flex', 
          justifyContent: isLeftOpen ? 'flex-end' : 'center', 
          padding: '10px',
          borderBottom: isLeftOpen ? 'none' : '1px solid transparent'
        }}>
          <button 
            style={toggleButtonStyle} 
            onClick={() => setIsLeftOpen(!isLeftOpen)}
            title={isLeftOpen ? "Collapse Explorer" : "Expand Explorer"}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.05)'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            {isLeftOpen ? '◀' : '▶'}
          </button>
        </div>
        
        {/* Left Content */}
        <div style={{ display: isLeftOpen ? 'block' : 'none', height: 'calc(100% - 44px)', overflow: 'hidden' }}>
          <FileExplorer 
            attentionShelf={attentionShelf} 
            toggleAttention={toggleAttention}
            sendCommand={sendCommand}
            latestMessage={latestMessage}
            isConnected={isConnected}
            // Passing down the active document state
            activeDocument={activeDocument}
            setActiveDocument={setActiveDocument}
          />
        </div>
      </div>
      
      {/* CENTER COLUMN (Terminal) */}
      <div className="column-panel center-column" style={{ width: widths.center }}>
        <Terminal 
          attentionShelf={attentionShelf} 
          setAttentionShelf={setAttentionShelf}
          sendCommand={sendCommand}
          latestMessage={latestMessage}
          isConnected={isConnected}
        />
      </div>

      {/* RIGHT COLUMN (Document Viewer / Widgets) */}
      <div className="column-panel right-column" style={{ width: widths.right }}>
         
         {/* Right Toggle Bar */}
         <div style={{ 
          display: 'flex', 
          justifyContent: isRightOpen ? 'flex-start' : 'center', 
          padding: '10px'
        }}>
          <button 
            style={toggleButtonStyle} 
            onClick={() => setIsRightOpen(!isRightOpen)}
            title={isRightOpen ? "Collapse Viewer" : "Expand Viewer"}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.05)'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            {isRightOpen ? '▶' : '◀'}
          </button>
        </div>

        {/* Right Content */}
        <div style={{ display: isRightOpen ? 'flex' : 'none', flexDirection: 'column', height: 'calc(100% - 44px)', padding: '0 20px 20px 20px' }}>
          
          <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '15px', marginBottom: '15px' }}>
            <h3 style={{ color: "var(--text-muted)", margin: 0, fontSize: "0.85em", letterSpacing: "1px", fontWeight: "600" }}>
              DOCUMENT VIEWER
            </h3>
          </div>

          {/* 4. Our new actual Document Viewer component */}
          <DocumentViewer 
            activeDocument={activeDocument}
            sendCommand={sendCommand}
            latestMessage={latestMessage}
            isConnected={isConnected}
            // Catch the selected text and save it in our new state
            onSelectionChange={setSelectedText}
          />

        </div>
      </div>

      <SystemHud systemLogs={systemLogs} />
      <DynamicHud systemLogs={systemLogs} />

    </div>
  )
}

export default App