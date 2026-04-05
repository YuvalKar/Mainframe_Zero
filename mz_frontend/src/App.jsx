// src/App.jsx
import { useState, useEffect, useRef } from 'react'
import './App.css'
import Terminal from './components/Terminal'
import FileExplorer from './components/FileExplorer'
import DocumentViewer from './components/DocumentViewer'
import FloatingLog from './components/FloatingLog'
import StaticHud from './components/StaticHud'

const MAX_LOGS_IN_MEMORY = 50;

// --- Icons for the Tool Tabs ---
const ExplorerIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
  </svg>
);

const ViewerIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
    <line x1="16" y1="13" x2="8" y2="13"></line>
    <line x1="16" y1="17" x2="8" y2="17"></line>
    <polyline points="10 9 9 9 8 9"></polyline>
  </svg>
);

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
  const [messageQueue, setMessageQueue] = useState([]);
  const [latestMessage, setLatestMessage] = useState(null);
  const wsRef = useRef(null);

  // Process the message queue one by one
  useEffect(() => {
    if (messageQueue.length > 0) {
      setLatestMessage(messageQueue[0]);
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
        
        setSystemLogs(prevLogs => {
          const updatedLogs = [...prevLogs, data];
          // Keep only the last MAX_LOGS_IN_MEMORY logs in memory to prevent memory leaks
          return updatedLogs.slice(-MAX_LOGS_IN_MEMORY); 
        });
        
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
      const enhancedPayload = {
        ...payload,
        client_context: {
          activeDocument: activeDocument ? activeDocument.path : null,
          selectedText: selectedText || null,
          attentionShelf: attentionShelf
            .filter(f => !activeDocument || f.path !== activeDocument.path)
            .map(f => f.path)
        }
      };

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
      <StaticHud appColor={appColor} latestMessage={latestMessage} />
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
        
        {/* Tool Selection Tabs with SVG Icons */}
        <div className="tools-tabs">
          <button 
            className={`tab-btn ${activeToolTab === 'explorer' ? 'active' : ''}`}
            onClick={() => setActiveToolTab('explorer')}
            title="File Explorer"
          >
            <ExplorerIcon />
          </button>
          <button 
            className={`tab-btn ${activeToolTab === 'viewer' ? 'active' : ''}`}
            onClick={() => setActiveToolTab('viewer')}
            title="Doc Viewer"
          >
            <ViewerIcon />
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