import React, { useState } from "react";
import axios from "axios";
import Message from "./Message";
import "./ChatWindow.css";
import Analytics from "./Analytics";

const logResponses = async (responses) => {
  try {
    const response = await axios.post("http://34.68.123.1:5000/saveLog", {
      ...responses, // Your log data
    });
    console.log("Log data saved:", response.data);
  } catch (error) {
    console.error("Error logging data:", error);
  }
};

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isPaneOpen, setIsPaneOpen] = useState(true); // Collapsible pane state
  const [activeTab, setActiveTab] = useState("chatbot"); // Current tab
  const [mode, setMode] = useState("Retrieval"); // Toggle mode state

  const [selectedTopics, setSelectedTopics] = useState([]); // Selected topics state

  // List of topics for the checkboxes
  const topicsList = [
    "Economy", "Health", "Technology", "Science", "Politics", "Sports",
    "Entertainment", "Travel", "Business", "Education"
  ];

  const handleTopicChange = (topic) => {
    setSelectedTopics((prevSelectedTopics) => {
      if (prevSelectedTopics.includes(topic)) {
        // Remove the topic from the selected topics array
        return prevSelectedTopics.filter((t) => t !== topic);
      } else {
        // Add the topic to the selected topics array
        return [...prevSelectedTopics, topic];
      }
    });
  };

  function isValidJson(data) {
    try {
      JSON.stringify(data); // Attempt to serialize the data
      return true;
    } catch (error) {
      return false;
    }
  }
  const handleSendMessage = async () => {
    if (!input.trim()) return;
  
    const userMessage = { text: input, sender: "user" };
    setMessages([...messages, userMessage]);
    setInput("");
  
    // Add a placeholder bot message to indicate processing
    const loadingMessage = { text: "Processing your request...", sender: "bot" };
    setMessages((prevMessages) => [...prevMessages, loadingMessage]);
  
    try {
      const userInput = userMessage.text;
  
      if (mode === "ChitChat") {
        // Directly call ChitChat API
        console.log("ChitChat Mode Active");
        const chitchatResponse = await axios.post("http://34.68.123.1:5000/chat", {
          message: userInput,
        });
        const botMessage = {
          text: `ChitChat: ${chitchatResponse.data?.response || "No response received."}\n`,
          sender: "bot",
        };
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          updatedMessages.pop(); // Remove loading message
          return [...updatedMessages, botMessage];
        });
        return; // Exit function since ChitChat is handled
      }
  
      // Retrieval Mode
      console.log("Retriever Mode Active");
  
      // If topics are selected, skip classifier call
      let classifierData;
      if (selectedTopics.length > 0) {
        console.log("Selected Topics:", selectedTopics);
        classifierData = {
          topics: selectedTopics,
          probability_values: Array(selectedTopics.length).fill(1),
          time: 0,
          query: userInput,
        };
      } else {
        const classifierResponse = await axios.post("http://34.16.74.179:5005/predict", {
          query: userInput,
        });
        classifierData = classifierResponse.data;
        console.log("Classifier Response:", classifierData?.topics?.[0]);
      }
  
      if (classifierData?.topics?.[0] === "Chitchat") {
        // Call ChitChat API
        const chitchatResponse = { answer: "This is a standard response" };
        const botMessage = { text: `ChitChat: ${chitchatResponse.answer}\n`, sender: "bot" };
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          updatedMessages.pop();
          return [...updatedMessages, botMessage];
        });
        return;
      }
  
      // Retriever API call
      const retrieverResponse = await axios.post(
        "http://34.130.33.83:9999/retriever_docs",
        { ...classifierData },
        { withCredentials: true }
      );
      const retrieverData = retrieverResponse.data.Response;
      const retrieverTimeTaken = retrieverResponse.data.time_taken
      console.log("Retriever Response:", retrieverResponse.data);
      // Summarizer API call
      const summarizerResponse = await axios.post(
        "http://34.16.74.179:5000/summarize",
        { Response: retrieverData },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      console.log("Summarizer Response:", summarizerResponse);
      const summarizerData = summarizerResponse.data;
  
      // Update the final bot response
      const botMessage = { text: `Summary: ${summarizerData?.summary || "No summary available."}\n`, sender: "bot" };
  
      // Log responses
      const allResponses = {
        classifier: classifierData,
        retriever: {"Response": retrieverData, "time_taken": retrieverTimeTaken},
        summarizer: summarizerResponse.data,
      };
      logResponses(allResponses);
  
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages.pop(); // Remove loading message
        return [...updatedMessages, botMessage];
      });
    } catch (error) {
      console.error("Error:", error);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages.pop(); // Remove loading message
        return [
          ...updatedMessages,
          { text: "Something went wrong. Please try again.", sender: "bot" },
        ];
      });
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
            
             {/* Checkbox for topics */}
             <div className="topics-checkboxes">
              {topicsList.map((topic) => (
                <label key={topic}>
                  <input
                    type="checkbox"
                    checked={selectedTopics.includes(topic)}
                    onChange={() => handleTopicChange(topic)}
                  />
                  {topic}
                </label>
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
          <Analytics />
        )}
      </div>
    </div>
  );
};

export default ChatWindow;
