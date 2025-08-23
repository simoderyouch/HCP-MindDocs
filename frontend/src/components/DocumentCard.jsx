import React from "react";
import { FaRegFileAlt, FaRegFilePdf, FaRegFileWord, FaRegFileExcel, FaRegFilePowerpoint } from "react-icons/fa";

const getFileIcon = (extension) => {
  const ext = extension.toLowerCase();
  switch (ext) {
    case 'pdf':
      return <FaRegFilePdf className="w-4 h-4 text-red-500" />;
    case 'doc':
    case 'docx':
      return <FaRegFileWord className="w-4 h-4 text-blue-500" />;
    case 'xls':
    case 'xlsx':
      return <FaRegFileExcel className="w-4 h-4 text-green-500" />;
    case 'ppt':
    case 'pptx':
      return <FaRegFilePowerpoint className="w-4 h-4 text-orange-500" />;
    default:
      return <FaRegFileAlt className="w-4 h-4 text-gray-500" />;
  }
};

const formatFileSize = (size) => {
  if (!size) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let index = 0;
  let fileSize = size;
  
  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024;
    index++;
  }
  
  return `${fileSize.toFixed(1)} ${units[index]}`;
};

function DocumentCard({ 
  file, 
  isSelected, 
  onToggle, 
  showIcon = true, 
  showStatus = true, 
  showSize = false,
  compact = false 
}) {
  return (
    <div
      className={`p-3 rounded-lg border transition-all duration-200 cursor-pointer group ${
        isSelected
          ? 'bg-blue-50 border-blue-300 shadow-sm'
          : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
      } ${compact ? 'p-2' : 'p-3'}`}
      onClick={onToggle}
    >
      <div className="flex items-center space-x-3">
        {/* Custom Checkbox */}
        <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
          isSelected
            ? 'bg-blue-600 border-blue-600'
            : 'border-gray-300 group-hover:border-blue-400'
        }`}>
          {isSelected && (
            <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )}
        </div>
        
        {/* File Icon */}
        {showIcon && (
          <div className="flex-shrink-0">
            {getFileIcon(file.extention)}
          </div>
        )}
        
        {/* File Info */}
        <div className="flex-1 min-w-0">
          <p className={`font-medium text-gray-900 truncate ${compact ? 'text-sm' : 'text-sm'}`}>
            {file.file_name}
          </p>
          <div className="flex items-center space-x-2 mt-1">
            <span className={`text-gray-500 ${compact ? 'text-xs' : 'text-xs'} uppercase`}>
              {file.extention}
            </span>
            
            {showSize && file.size && (
              <>
                <span className="text-gray-300">•</span>
                <span className={`text-gray-500 ${compact ? 'text-xs' : 'text-xs'}`}>
                  {formatFileSize(file.size)}
                </span>
              </>
            )}
            
            {showStatus && (
              <>
                <span className="text-gray-300">•</span>
                <span className={`flex items-center ${compact ? 'text-xs' : 'text-xs'} ${
                  file.processed ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full mr-1 ${
                    file.processed ? 'bg-green-500' : 'bg-yellow-500'
                  }`}></span>
                  {file.processed ? 'Processed' : 'Processing...'}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DocumentCard;
