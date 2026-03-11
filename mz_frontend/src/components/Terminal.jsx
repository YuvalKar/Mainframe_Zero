// src/components/Terminal.jsx
import { useState, useRef, useEffect } from 'react'

export default function Terminal({ attentionShelf, setAttentionShelf, sendCommand, latestMessage, isConnected }) {
  const [chatLog, setChatLog] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("gemini-2.5-flash");
  
  const messagesEndRef = useRef(null);

  // Scroll to bottom whenever chatLog changes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatLog]);

  // Listen to incoming messages from the central App hub
  useEffect(() => {
    if (!latestMessage) return;

    // Filter out direct execution results (those belong to the senses, like FileExplorer)
    if (latestMessage.type !== "direct_result") {
      setChatLog(prev => [...prev, latestMessage]);
    }
  }, [latestMessage]);

  const handleModelChange = (e) => {
    const newModel = e.target.value;
    setSelectedModel(newModel);
    
    // Send model change command through the App's central pipe
    if (isConnected) {
      sendCommand({
        action: "change_model",
        model: newModel
      });
    }
  };

  // Send message through the central App hub
  const sendMessage = () => {
    if (!userInput.trim() || !isConnected) return;

    // 1. Find only the files that haven't been sent yet
    const filesToSend = attentionShelf.filter(f => !f.sent);
    
    // 2. Format them as @path strings
    const contextString = filesToSend.map(f => `@${f.path}`).join(" ");
    
    // 3. Prepare the final hidden prompt for the backend
    const finalContent = contextString 
      ? `${userInput}\n\n[Context]: ${contextString}` 
      : userInput;

    // 4. Update UI log (User only sees their clean input)
    setChatLog(prev => [...prev, { type: "user", content: userInput }]);
    
    // 5. Send to Python via the App's sendCommand prop
    sendCommand({
      action: "chat",
      content: finalContent
    });

    // 6. Update the master list: mark these files as 'sent'
    if (filesToSend.length > 0) {
      setAttentionShelf(prev => 
        prev.map(f => 
          filesToSend.some(ts => ts.path === f.path) ? { ...f, sent: true } : f
        )
      );
    }
    
    setUserInput("");
  };

  return (
    <div style={{ 
      padding: "20px", 
      fontFamily: "monospace", 
      maxWidth: "800px", 
      margin: "0 auto", 
      height: "100%", 
      display: "flex", 
      flexDirection: "column",
      color: "#ccc" 
    }}>
      <h1>Mainframe Zero Terminal</h1>

      <div style={{ marginBottom: "15px" }}>
        <label htmlFor="modelSelect" style={{ marginRight: "10px", fontWeight: "bold" }}>Active Engine:</label>
        <select 
          id="modelSelect"
          value={selectedModel} 
          onChange={handleModelChange}
          disabled={!isConnected}
          style={{ padding: "5px", fontFamily: "monospace", borderRadius: "4px" }}
        >
          <option value="gemini-2.5-pro">Deep thinking & complex coding (Gemini 2.5 Pro)</option>
          <option value="gemini-2.5-flash">Fast & fluent conversation (Gemini 2.5 Flash)</option>
          <option value="gemini-2.5-flash-lite">Ultra-fast simple tasks (Gemini 2.5 Flash-Lite)</option>
        </select>
      </div>

      <div style={{ 
        border: "1px solid #ccc", 
        padding: "10px", 
        flex: 1, 
        overflowY: "auto", 
        marginBottom: "10px",
        backgroundColor: "#f9f9f9",
        color: "#333" // Just making sure the text is readable on the light background
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
          style={{ flex: 1, padding: "10px", fontFamily: "monospace", backgroundColor: "#fff", color: "#000" }}
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