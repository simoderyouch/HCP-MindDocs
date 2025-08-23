import React, { useEffect, useState } from "react";
import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaTimes } from "react-icons/fa";

function Notification({ 
  type = "info", 
  message, 
  duration = 5000, 
  onClose, 
  show = true 
}) {
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    setIsVisible(show);
    
    if (show && duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose();
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [show, duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case "success":
        return <FaCheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <FaExclamationTriangle className="w-5 h-5 text-red-500" />;
      case "warning":
        return <FaExclamationTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return <FaInfoCircle className="w-5 h-5 text-blue-500" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case "success":
        return "bg-green-50 border-green-200 text-green-800";
      case "error":
        return "bg-red-50 border-red-200 text-red-800";
      case "warning":
        return "bg-yellow-50 border-yellow-200 text-yellow-800";
      default:
        return "bg-blue-50 border-blue-200 text-blue-800";
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-sm w-full p-4 rounded-lg border shadow-lg fade-in ${getStyles()}`}>
      <div className="flex items-start space-x-3">
        {getIcon()}
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={() => {
            setIsVisible(false);
            if (onClose) onClose();
          }}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <FaTimes className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default Notification;
