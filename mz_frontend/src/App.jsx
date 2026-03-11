// src/App.jsx
import { useState, useEffect, useRef } from 'react'
import './App.css'
import Terminal from './components/Terminal'
import FileExplorer from './components/FileExplorer'

function App() {
  const [attentionShelf, setAttentionShelf] = useState([]);
  
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
        setLatestMessage(data); // Broadcast the incoming message to all children
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
      wsRef.current.send(JSON.stringify(payload));
    }
  };

  const toggleAttention = (fileNode) => {
    setAttentionShelf(prev => {
      const exists = prev.find(f => f.path === fileNode.path);
      if (exists) {
        return prev.filter(f => f.path !== fileNode.path);
      } else {
        return [...prev, { ...fileNode, sent: false }];
      }
    });
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "row", backgroundColor: "#1e1e1e" }}>
      
      <FileExplorer 
        attentionShelf={attentionShelf} 
        toggleAttention={toggleAttention}
        sendCommand={sendCommand}
        latestMessage={latestMessage}
        isConnected={isConnected}
      />
      
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Terminal 
          attentionShelf={attentionShelf} 
          setAttentionShelf={setAttentionShelf}
          sendCommand={sendCommand}
          latestMessage={latestMessage}
          isConnected={isConnected}
        />
      </div>

    </div>
  )
}

export default App