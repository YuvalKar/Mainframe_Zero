import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  // State to hold the chat history (an array of log objects)
  const [chatLog, setChatLog] = useState([]);
  // State to hold the current text in the input field
  const [userInput, setUserInput] = useState("");
  // State to disable the button while waiting for the server
  const [isLoading, setIsLoading] = useState(false);
  // Create a reference to attach to the bottom of the chat container
  const messagesEndRef = useRef(null);
  // Function to smoothly scroll to the referenced element
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  // Listen for changes in the chatLog array and trigger the scroll
  useEffect(() => {
    scrollToBottom();
  }, [chatLog]);

  // Function to send the message to the FastAPI server
  const sendMessage = async () => {
    if (!userInput.trim()) return;

    // Add the user's message to the log visually immediately
    setChatLog(prev => [...prev, { type: "user", content: userInput }]);
    setIsLoading(true);

    try {
      // Call the FastAPI endpoint
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ user_input: userInput })
      });

      const data = await response.json();

      // Ensure we got a valid log back, then append it to our screen
      if (data.status === "completed" && data.log) {
        setChatLog(prev => [...prev, ...data.log]);
      } else {
        setChatLog(prev => [...prev, { type: "error", content: "Invalid response format from server." }]);
      }
    } catch (error) {
      setChatLog(prev => [...prev, { type: "error", content: `Connection error: ${error.message}` }]);
    } finally {
      // Clear the input and re-enable the button
      setUserInput("");
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "monospace", maxWidth: "800px", margin: "0 auto" }}>
      <h1>Mainframe Zero Terminal</h1>
      
      {/* The Chat Log Area */}
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
        {isLoading && <div style={{ color: "gray" }}>[SYSTEM: Processing...]</div>}

        {/* The invisible anchor element for scrolling */}
        <div ref={messagesEndRef} />
        
      </div>

      {/* The Input Area */}
      <div style={{ display: "flex", gap: "10px" }}>
        <input 
          type="text" 
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Enter command..."
          disabled={isLoading}
          style={{ flex: 1, padding: "10px", fontFamily: "monospace" }}
        />
        <button 
          onClick={sendMessage} 
          disabled={isLoading}
          style={{ padding: "10px 20px", cursor: isLoading ? "wait" : "pointer" }}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default App