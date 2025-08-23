import React from 'react';
import NavBar from './navBar';
import MultiDocumentChat from './MultiDocumentChat';

function MultiDocumentChatPage() {
  return (
    <div className="flex flex-col bg-gray-50 min-h-[100vh]">
      <NavBar />
      
      <div className="flex-1 p-4">
        <div className="max-w-7xl mx-auto h-[calc(100vh-120px)]">
          <MultiDocumentChat />
        </div>
      </div>
    </div>
  );
}

export default MultiDocumentChatPage;
