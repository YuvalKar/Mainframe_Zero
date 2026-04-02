// src/App.jsx
import { useState, useEffect, useRef } from 'react'
import './App.css'
import Terminal from './components/Terminal'
import FileExplorer from './components/FileExplorer'
import DocumentViewer from './components/DocumentViewer'
import FloatingLog from './components/FloatingLog'
import StaticHud from './components/StaticHud'

function App() {
  // --- Global App State ---
  const [appColor, setAppColor] = useState("#4da8da"); 

  // --- File and Document State ---
  const [attentionShelf, setAttentionShelf] = useState([]);
  const [activeDocument, setActiveDocument] = useState(null);
  const [selectedText, setSelectedText] = useState("");

  // --- UI Layout State ---
  const [activeToolTab, setActiveToolTab] = useState('explorer'); 

  // --- WebSocket & System Logs State ---
  const [systemLogs, setSystemLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  
  // NEW: Queue system to prevent React batching from swallowing rapid messages
  const [messageQueue, setMessageQueue] = useState([]);
  const [latestMessage, setLatestMessage] = useState(null);
  
  const wsRef = useRef(null);

  // Process the message queue one by one
  useEffect(() => {
    if (messageQueue.length > 0) {
      // 1. Give the current message to the children
      setLatestMessage(messageQueue[0]);
      
      // 2. Clear it from the queue after a tiny delay so React has time to render
      const timer = setTimeout(() => {
        setMessageQueue(prev => prev.slice(1));
      }, 50);
      
      return () => clearTimeout(timer);
    }
  }, [messageQueue]);

  // Centralized WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Add EVERY incoming message to the logs immediately
        setSystemLogs(prevLogs => [...prevLogs, data]);
        
        // Push to queue instead of overwriting latestMessage directly
        setMessageQueue(prev => [...prev, data]);

      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    ws.onclose = () => setIsConnected(false);

    return () => {
      ws.close();
    };
  }, []);

  // Helper function to send commands via WebSocket
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

      // Add to our floating log so we can see what we ACTUALLY sent
      const outgoingMsg = { type: 'user_command', content: enhancedPayload };
      setSystemLogs(prevLogs => [...prevLogs, outgoingMsg]);
      
      wsRef.current.send(JSON.stringify(enhancedPayload));
    }
  };

  // Helper function to toggle files on the attention shelf
  const toggleAttention = (fileNode) => {
    setAttentionShelf(prev => {
      const exists = prev.find(f => f.path === fileNode.path);
      if (exists) {
        if (activeDocument && activeDocument.path === fileNode.path) {
          setActiveDocument(null);
        }
        return prev.filter(f => f.path !== fileNode.path);
      } else {
        return [...prev, { ...fileNode, sent: false }];
      }
    });
  };

  return (
    <div className="app-container">
      
      {/* HUD Layers */}
      <StaticHud appColor={appColor} />
      <FloatingLog systemLogs={systemLogs} />

      {/* Left Column: AI Terminal */}
      <div className="left-column" style={{ width: '50%' }}>
        <Terminal 
          isConnected={isConnected}
          sendCommand={sendCommand}
          latestMessage={latestMessage}
          attentionShelf={attentionShelf}
          setAttentionShelf={setAttentionShelf}
          setAppColor={setAppColor} 
        />
      </div>

      {/* Right Column: Dynamic Tools Panel */}
      <div className="right-panel" style={{ width: '50%', display: 'flex', flexDirection: 'column' }}>
        
        {/* Tool Selection Tabs */}
        <div className="tools-tabs">
          <button 
            className={`tab-btn ${activeToolTab === 'explorer' ? 'active' : ''}`}
            onClick={() => setActiveToolTab('explorer')}
          >
            File Explorer
          </button>
          <button 
            className={`tab-btn ${activeToolTab === 'viewer' ? 'active' : ''}`}
            onClick={() => setActiveToolTab('viewer')}
          >
            Doc Viewer
          </button>
        </div>

        {/* Dynamic Tool Content */}
        <div className="tools-content">
          {activeToolTab === 'explorer' ? (
            <FileExplorer 
              attentionShelf={attentionShelf}
              toggleAttention={toggleAttention}
              activeDocument={activeDocument}
              setActiveDocument={setActiveDocument}
              sendCommand={sendCommand}
              latestMessage={latestMessage}
              isConnected={isConnected}
            />
          ) : (
            <DocumentViewer 
              activeDocument={activeDocument}
              sendCommand={sendCommand}
              latestMessage={latestMessage}
              isConnected={isConnected}
              onSelectionChange={setSelectedText}
            />
          )}
        </div>

      </div>
    </div>
  )
}

export default App