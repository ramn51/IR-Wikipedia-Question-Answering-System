import React, { useState } from "react";
import axios from "axios";
import Message from "./Message";
import "./ChatWindow.css";

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isPaneOpen, setIsPaneOpen] = useState(true); // Collapsible pane state
  const [activeTab, setActiveTab] = useState("chatbot"); // Current tab
  const [mode, setMode] = useState("Retrieval"); // Toggle mode state

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages([...messages, userMessage]);
    setInput("");

    try {
      // Decide the API endpoint based on the mode
      const endpoint =
        mode === "Retrieval"
          ? "http://127.0.0.1:5000/retrieval"
          : "http://127.0.0.1:5000/chitchat";

      const response = await axios.post(endpoint, {
        message: input,
      });

      const botMessage = { text: response.data.response, sender: "bot" };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = {
        text: "Something went wrong. Please try again.",
        sender: "bot",
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") handleSendMessage();
  };

  const toggleMode = () => {
    setMode((prevMode) => (prevMode === "Retrieval" ? "ChitChat" : "Retrieval"));
  };

  return (
    <div className="chat-layout">
      {/* Left Pane */}
      <div className={`left-pane ${isPaneOpen ? "open" : "closed"}`}>
        <button className="toggle-button" onClick={() => setIsPaneOpen(!isPaneOpen)}>
          {isPaneOpen ? "⮜" : "⮞"}
        </button>
        {isPaneOpen && (
          <div className="tabs">
            <div
              className={`tab ${activeTab === "chatbot" ? "active" : ""}`}
              onClick={() => setActiveTab("chatbot")}
            >
              Chatbot
            </div>
            <div
              className={`tab ${activeTab === "analytics" ? "active" : ""}`}
              onClick={() => setActiveTab("analytics")}
            >
              Analytics
            </div>
          </div>
        )}
      </div>

      {/* Chat Window */}
      <div className="main-content">
        {activeTab === "chatbot" ? (
          <>
            <div className="switch-mode">
              <span className={`mode-label ${mode === "Retrieval" ? "active" : ""}`}>
                Retrieval
              </span>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={mode === "ChitChat"}
                  onChange={toggleMode}
                />
                <span className="slider"></span>
              </label>
              <span className={`mode-label ${mode === "ChitChat" ? "active" : ""}`}>
                ChitChat
              </span>
            </div>
            <div className="messages">
              {messages.map((msg, index) => (
                <Message key={index} text={msg.text} sender={msg.sender} />
              ))}
            </div>
            <div className="input-area">
              <input
                type="text"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <button onClick={handleSendMessage}>Send</button>
            </div>
          </>
        ) : (
          <div className="analytics">Analytics content goes here!</div>
        )}
      </div>
    </div>
  );
};

export default ChatWindow;
