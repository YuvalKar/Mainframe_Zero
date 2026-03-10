import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [chatLog, setChatLog] = useState([]);
  const [userInput, setUserInput] = useState("");
  // We don't strictly need isLoading for WebSockets in the same way, 
  // but let's use it to disable inputs if disconnected.
  const [isConnected, setIsConnected] = useState(false);
  
  const messagesEndRef = useRef(null);
  // Store the WebSocket instance
  const wsRef = useRef(null);

  // Scroll to bottom whenever chatLog changes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [chatLog]);

  // Establish the WebSocket connection on component mount
  useEffect(() => {
    // Connect to the new endpoint
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setChatLog(prev => [...prev, { type: "system", content: "Connected to Mainframe Zero via WebSocket." }]);
    };

    // Listen for incoming messages from the server
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setChatLog(prev => [...prev, data]);
      } catch (err) {
        console.error("Failed to parse incoming message:", event.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setChatLog(prev => [...prev, { type: "system", content: "Disconnected from server." }]);
    };

    // Cleanup function when the component unmounts
    return () => {
      ws.close();
    };
  }, []);

  // Send message through the open WebSocket
  const sendMessage = () => {
    if (!userInput.trim() || !wsRef.current || !isConnected) return;

    // Show the user's message in the UI immediately
    setChatLog(prev => [...prev, { type: "user", content: userInput }]);
    
    // Send the raw text to the server (our server expects text right now)
    wsRef.current.send(userInput);
    
    setUserInput("");
  };

  return (
    <div style={{ padding: "20px", fontFamily: "monospace", maxWidth: "800px", margin: "0 auto" }}>
      <h1>Mainframe Zero Terminal</h1>
      
      <div style={{ 
        border: "1px solid #ccc", 
        padding: "10px", 
        height: "400px", 
        overflowY: "auto", 
        marginBottom: "10px",
        backgroundColor: "#f9f9f9"
      }}>
        {chatLog.map((log, index) => (
          <div key={index} style={{ marginBottom: "10px" }}>
            <strong>[{log.type.toUpperCase()}]: </strong>
            <span style={{ whiteSpace: "pre-wrap" }}>{log.content}</span>
          </div>
        ))}
        
        {!isConnected && <div style={{ color: "red" }}>[SYSTEM: Offline. Waiting for connection...]</div>}

        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: "flex", gap: "10px" }}>
        <input 
          type="text" 
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Enter command..."
          disabled={!isConnected}
          style={{ flex: 1, padding: "10px", fontFamily: "monospace" }}
        />
        <button 
          onClick={sendMessage} 
          disabled={!isConnected}
          style={{ padding: "10px 20px", cursor: !isConnected ? "not-allowed" : "pointer" }}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default App