import React, { useState } from "react";
import axios from "axios";
import Message from "./Message";
import "./ChatWindow.css";
import Analytics from "./Analytics";

const logResponses = async (responses) => {
  try {
    const response = await axios.post("http://localhost:5000/saveLog", {
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
      // Classifier API call
      const userInput = userMessage.text;
      if (selectedTopics.length > 0) {
        // Dont do classifier call if topics are selected
        console.log("Selected Topics:", selectedTopics);
        const classifierData = { topics: selectedTopics, probability_values: Array(selectedTopics.length).fill(1), time: 0, query: userInput };

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
        const botMessage = { text: `Summary: ${summarizerData.summary}\n`, sender: "bot" };

        // Save all the results onto a json file for analytics
        const allResponses = {
          'classifier': classifierData,
          'retriever': {"Response": retrieverData, "time_taken": retrieverTimeTaken},
          'summarizer': summarizerResponse.data,
        };

        logResponses(allResponses);
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          updatedMessages.pop();
          return [...updatedMessages, botMessage];
        });
      }
      const classifierResponse = await axios.post("http://34.16.74.179:5005/predict", {
        query: userInput,
      });
      const classifierData = classifierResponse.data;
      console.log("Classifier Response:", classifierData.topics[0]);

      if( classifierData.topics[0] === 'Chitchat'){
        // const chitchatResponse = await axios.post("http://localhost:5000/chat", {
        //   query: userInput,
        // });
        // Replace this line with the above line if the chat_app.py server is running without issues
        const chitchatResponse = { answer: "This is a standard response" };
        const botMessage = { text: `ChitChat: ${chitchatResponse.answer}\n`, sender: "bot" };
        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          updatedMessages.pop();
          return [...updatedMessages, botMessage];
        });
      }

      else {
          // Retriever API call
          const retrieverResponse = await axios.post(
            "http://34.130.33.83:9999/retriever_docs",
            { ...classifierData },
            { withCredentials: true }
          );
          const retrieverData = retrieverResponse.data.Response;
          const retrieverTimeTaken = retrieverResponse.data.time_taken
          console.log("Retriever Response:", retrieverResponse.data);
          // console.log("Retriever Response:", retrieverData); 

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
          const botMessage = { text: `Summary: ${summarizerData.summary}\n`, sender: "bot" };

          // Save all the results onto a json file for analytics
          const allResponses = {
            'classifier': classifierData,
            'retriever': {"Response": retrieverData, "time_taken": retrieverTimeTaken},
            'summarizer': summarizerResponse.data,
          };

          logResponses(allResponses);
          setMessages((prevMessages) => {
            const updatedMessages = [...prevMessages];
            updatedMessages.pop();
            return [...updatedMessages, botMessage];
          });
      }
  
      
    } catch (error) {
      console.error("Error:", error);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages.pop();
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
