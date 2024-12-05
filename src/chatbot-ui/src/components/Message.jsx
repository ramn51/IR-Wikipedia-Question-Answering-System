import React from "react";
import "./Message.css";

const Message = ({ text, sender }) => {
  const messageClass = sender === "bot" ? "bot-message" : "user-message";

  return <div className={`message ${messageClass}`}>{text}</div>;
};

export default Message;
