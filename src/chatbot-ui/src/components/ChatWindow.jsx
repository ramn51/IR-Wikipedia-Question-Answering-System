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
          ? "http://34.130.33.83:9999/retriever_docs"
          : "http://127.0.0.1:5000/chitchat";

          // const classifierResponse = await axios.post("http://34.16.74.179:5000/predict", {
          //   query: input,
          // });
          // const classifierData = classifierResponse.data.response; // Extract the response data
          // console.log("Classifier Response:", classifierData);
      
          // Step 2: Use the classifier response in the retriever API call
          const retrieverResponse = await axios.post("http://34.130.33.83:9999/retriever", {
            query: input,
            topics: ["Technology"], // Example topics
          }, 
          {
            withCredentials: true, // Include if cookies are used
          }
        );
          const retrieverData = retrieverResponse.data.response; // Extract the response data
          console.log("Retriever Response:", retrieverData);
      
          // Step 3: Use the retriever response in the summarizer API call
          const summarizerResponse = await axios.post("http://34.16.74.179:5005/summarize", {
            summaries: [retrieverData], // Pass the retriever response as input
          });
          const summarizerData = summarizerResponse.data.response; // Extract the response data
          console.log("Summarizer Response:", summarizerData);

      const botMessage = { text: summarizerData.data.response, sender: "bot" };
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
