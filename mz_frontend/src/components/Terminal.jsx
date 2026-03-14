// src/components/Terminal.jsx
import { useState, useRef, useEffect } from 'react'

// --- Simple Minimalist Icons ---

const UserIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5f6368" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

const BotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1a73e8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2"></rect>
    <circle cx="12" cy="5" r="2"></circle>
    <path d="M12 7v4"></path>
    <line x1="8" y1="16" x2="8" y2="16"></line>
    <line x1="16" y1="16" x2="16" y2="16"></line>
  </svg>
);

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
    
    // Send model change command
    if (isConnected) {
      sendCommand({
        action: "change_model",
        model: newModel
      });
    }
  };

  // Send message
  const sendMessage = () => {
    if (!userInput.trim() || !isConnected) return;

    // Find unsent files
    // const filesToSend = attentionShelf.filter(f => !f.sent);
    const filesToSend = attentionShelf;
    const contextString = filesToSend.map(f => `@${f.path}`).join(" ");
    
    // Prepare string for UI vs Backend
    setChatLog(prev => [...prev, { type: "user", content: userInput }]);
    
    sendCommand({
      action: "chat",
      content: contextString ? `${userInput}\n\n[Context]: ${contextString}` : userInput
    });

    // Mark as sent
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
      display: "flex", 
      flexDirection: "column",
      height: "100%", 
      backgroundColor: "var(--bg-main)",
      position: "relative"
    }}>
      
      {/* Top Bar / Header */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center", 
        padding: "15px 24px",
        borderBottom: "1px solid var(--border-color)",
        backgroundColor: "var(--bg-main)",
        zIndex: 10
      }}>
        <h2 style={{ margin: 0, fontSize: "1.1em", fontWeight: "400", color: "var(--text-main)", letterSpacing: "0.5px" }}>
          Mainframe Zero
        </h2>
        
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {!isConnected && (
            <span style={{ color: "#d93025", fontSize: "0.85em", display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ display: "inline-block", width: "8px", height: "8px", backgroundColor: "#d93025", borderRadius: "50%" }}></span>
              Offline
            </span>
          )}
          <select 
            value={selectedModel} 
            onChange={handleModelChange}
            disabled={!isConnected}
            style={{ 
              padding: "6px 10px", 
              borderRadius: "4px", 
              border: "1px solid transparent",
              backgroundColor: "transparent",
              color: "var(--text-muted)",
              fontSize: "0.9em",
              cursor: isConnected ? "pointer" : "not-allowed",
              outline: "none"
            }}
            onMouseOver={(e) => isConnected && (e.target.style.backgroundColor = "#f1f3f4")}
            onMouseOut={(e) => e.target.style.backgroundColor = "transparent"}
          >
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
            <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite</option>
          </select>
        </div>
      </div>

      {/* Chat Area - Adjusted Padding */}
      <div style={{ 
        flex: 1, 
        overflowY: "auto", 
        padding: "24px 40px", // Replaced the 15% with a fixed, comfortable padding
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        scrollBehavior: "smooth"
      }}>
        {chatLog.length === 0 && (
          <div style={{ margin: "auto", textAlign: "center", color: "var(--text-muted)" }}>
            <h3 style={{ fontWeight: 300, fontSize: "1.5em", marginBottom: "10px" }}>How can I help you today?</h3>
            <p style={{ fontSize: "0.9em" }}>Select files from the explorer or just start typing.</p>
          </div>
        )}

        {chatLog.map((log, index) => (
          <div key={index} style={{ 
            display: "flex", 
            gap: "16px",
            alignItems: "flex-start"
          }}>
            {/* Avatar */}
            <div style={{ 
              minWidth: "32px", 
              height: "32px", 
              borderRadius: "50%", 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center",
              backgroundColor: log.type === "user" ? "#f1f3f4" : "#e8f0fe"
            }}>
              {log.type === "user" ? <UserIcon /> : <BotIcon />}
            </div>
            
            {/* Message Content & Metadata */}
            <div style={{ flex: 1, paddingTop: "4px" }}>
              
              {/* Subtle Label for non-user messages (e.g., 'thought', 'system', 'error') */}
              {log.type !== "user" && (
                <div style={{ 
                  fontSize: "0.7em", 
                  color: log.type === "error" ? "#d93025" : "var(--text-muted)", 
                  marginBottom: "4px", 
                  textTransform: "uppercase", 
                  letterSpacing: "0.5px",
                  fontWeight: "600"
                }}>
                  {log.type}
                </div>
              )}

              <div style={{ 
                color: log.type === "error" ? "#d93025" : "var(--text-main)",
                lineHeight: "1.6",
                fontSize: "0.95em",
                whiteSpace: "pre-wrap" 
              }}>
                {log.content}
              </div>
            </div>
          </div>
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Adjusted Padding to match Chat Area */}
      <div style={{ 
        padding: "20px 40px", 
        backgroundColor: "var(--bg-main)"
      }}>
        <div style={{
          display: "flex", 
          alignItems: "center",
          gap: "10px",
          backgroundColor: "#f1f3f4", 
          borderRadius: "24px",
          padding: "8px 16px",
          border: "1px solid transparent",
          transition: "border-color 0.2s, box-shadow 0.2s"
        }}
        onFocus={(e) => e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.1)"}
        onBlur={(e) => e.currentTarget.style.boxShadow = "none"}
        >
        <input 
            type="text" 
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder={isConnected ? "Message Mainframe..." : "Connecting..."}
            disabled={!isConnected}
            style={{ 
              flex: 1, 
              border: "none", 
              outline: "none", 
              backgroundColor: "transparent", 
              color: "var(--text-muted)",
              fontSize: "0.95em",
              fontWeight: "300", 
              fontFamily: "inherit",
              padding: "8px 0"
            }}
          />
          <button 
            onClick={sendMessage} 
            disabled={!isConnected || !userInput.trim()}
            style={{ 
              background: "transparent",
              border: "none",
              cursor: (!isConnected || !userInput.trim()) ? "default" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "4px",
              color: (!isConnected || !userInput.trim()) ? "#9aa0a6" : "#1a73e8",
              transition: "color 0.2s"
            }}
            title="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}