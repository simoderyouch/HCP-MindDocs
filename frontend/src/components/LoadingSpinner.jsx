import React from "react";

function LoadingSpinner({ size = "md", color = "blue", className = "" }) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-5 h-5", 
    lg: "w-6 h-6",
    xl: "w-8 h-8"
  };

  const colorClasses = {
    blue: "border-blue-600 border-t-transparent",
    white: "border-white border-t-transparent",
    gray: "border-gray-600 border-t-transparent"
  };

  return (
    <div 
      className={`${sizeClasses[size]} ${colorClasses[color]} border-2 rounded-full animate-spin ${className}`}
    />
  );
}

export default LoadingSpinner;
