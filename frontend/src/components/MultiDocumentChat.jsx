import React, { useState, useEffect, useRef } from "react";
import useFetch from "../hook/useFetch";
import Loading from "./Loading";
import { LuSend, LuChevronLeft, LuChevronRight } from "react-icons/lu";
import useAxiosPrivate from "../hook/useAxiosPrivate";
import parse from "html-react-parser";
import sanitizeHtml from "../shared/utils/sanitizeHtml";
import AutoResizableTextarea from "./AutoResizableTextarea";
import { time } from "../utils/time";
import { Dropdown } from "flowbite-react";
import { IoMdSettings } from "react-icons/io";
import { MdOutlineSelectAll, MdClear, MdOutlinePlayCircle } from "react-icons/md";
import { FaRegFileAlt, FaFileAlt, FaCheckCircle } from "react-icons/fa";
import { RiDeleteBin6Line } from "react-icons/ri";

function MultiDocumentChat() {
  const {
    data: filesData,
    error: filesError,
    isLoading: filesIsLoading,
    fetchData: fetchFiles,
  } = useFetch('/api/document/files');

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSetting, setShowSetting] = useState(false);
  const [language, setLanguage] = useState("Auto-detect");
  const [model, setModel] = useState("Mistral");
  const [messages, setMessages] = useState([]);
  const [showingLetters, setShowingLetters] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [processing, setProcessing] = useState({}); // { [fileId]: boolean }
  const chatEndRef = useRef(null);
  const axiosInstance = useAxiosPrivate();

  // Load files and restore cached messages
  useEffect(() => {
    fetchFiles();
    try {
      const cached = localStorage.getItem('multiDocChatCache');
      if (cached) {
        const parsed = JSON.parse(cached);
        const now = Date.now();
        if (parsed && parsed.expiresAt && now < parsed.expiresAt && Array.isArray(parsed.messages)) {
          setMessages(parsed.messages);
        } else {
          localStorage.removeItem('multiDocChatCache');
        }
      }
    } catch (_) {
      // ignore cache errors
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Persist messages to localStorage with 24h TTL
  useEffect(() => {
    try {
      const expiresAt = Date.now() + 24 * 60 * 60 * 1000; // 24 hours
      localStorage.setItem('multiDocChatCache', JSON.stringify({ messages, expiresAt }));
    } catch (_) {
      // ignore storage errors
    }
  }, [messages]);

  // Typing effect for assistant responses (like single-document chat)
  useEffect(() => {
    let timeout;
    const lastMessage = messages[messages.length - 1];
    if (
      showingLetters &&
      lastMessage &&
      !lastMessage.is_user_message &&
      currentIndex < (lastMessage.message?.length || 0)
    ) {
      const randomDelay = Math.floor(Math.random() * (10 - 5) + 1) + 10;
      const randomUpdate = Math.floor(Math.random() * (5 - 1) + 1) + 5;
      timeout = setTimeout(() => {
        setCurrentIndex((prev) => prev + randomUpdate);
      }, randomDelay);
    } else {
      setShowingLetters(false);
    }
    return () => clearTimeout(timeout);
  }, [showingLetters, currentIndex, messages]);

  const handleFileToggle = React.useCallback((fileId) => {
    setSelectedFiles(prev => 
      prev.includes(fileId) 
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  }, []);

  const handleSelectAll = React.useCallback(() => {
    if (filesData) {
      const processedFileIds = Object.values(filesData).flat().filter(file => file.processed).map(file => file.id);
      setSelectedFiles(processedFileIds);
    }
  }, [filesData]);

  const handleDeselectAll = React.useCallback(() => {
    setSelectedFiles([]);
  }, []);

  const handleSubmit = async (question_p = "") => {
    if (selectedFiles.length === 0) {
      alert("Please select at least one document to chat with.");
      return;
    }

    const finalQuestion = question_p.trim() || question.trim();
    if (!finalQuestion) {
      alert("Please enter a question.");
      return;
    }

    setShowingLetters(false);
    setIsLoading(true);
    const currentTime = new Date();
    const formattedTime = currentTime.toISOString();
    
    setMessages([
      ...messages,
      { message: finalQuestion, is_user_message: true, create_at: formattedTime },
    ]);
    
    setQuestion("");

    try {
      const requestData = {
        question: finalQuestion,
        file_ids: selectedFiles,
        language: language,
        model: model,
      };
      
      const response = await axiosInstance.post('/api/chat/multi-document', requestData);
      
      setCurrentIndex(0);
      const currentTime = new Date();
      const formattedTime = currentTime.toISOString();
      
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: response.data.message,
          is_user_message: false,
          create_at: formattedTime,
          documents_used: response.data.documents_used,
        },
      ]);
      
      setShowingLetters(true);
      setQuestion("");
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = error.response?.data?.detail || "Sorry, there was an error processing your request. Please try again.";
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: errorMessage,
          is_user_message: false,
          create_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getSelectedFilesInfo = () => {
    if (!filesData || selectedFiles.length === 0) return [];
    
    const allFiles = Object.values(filesData).flat();
    return allFiles.filter(file => selectedFiles.includes(file.id));
  };

  const selectedFilesInfo = getSelectedFilesInfo();

  // Files helpers
  const getAllFiles = React.useCallback(() => {
    if (!filesData) return [];
    return Object.values(filesData).flat();
  }, [filesData]);

  const allFiles = React.useMemo(() => getAllFiles(), [getAllFiles]);
  const processedFiles = React.useMemo(() => allFiles.filter(f => f.processed), [allFiles]);
  const unprocessedFiles = React.useMemo(() => allFiles.filter(f => !f.processed), [allFiles]);

  const handleProcessFile = async (fileId) => {
    try {
      setProcessing(prev => ({ ...prev, [fileId]: true }));
      await axiosInstance.get(`/api/document/process/${fileId}`);
      await fetchFiles();
    } catch (e) {
      console.error('Failed to process document', e);
    } finally {
      setProcessing(prev => ({ ...prev, [fileId]: false }));
    }
  };

  if (filesIsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loading padding={3} />
      </div>
    );
  }

  return (
    <div className="flex h-full bg-white rounded-lg shadow-sm">
      {/* Sidebar: Documents */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-72'} border-r border-gray-200 flex flex-col`}>
        {!sidebarCollapsed ? (
          <div className="flex items-center justify-between p-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <FaRegFileAlt className="text-primary text-xl" />
              <span className="text-sm font-medium text-gray-700">Documents</span>
            </div>
            <button
              onClick={() => setSidebarCollapsed(true)}
              className="text-primary text-xs px-2 py-1 border border-primary rounded-sm2 flex items-center gap-1"
              title="Collapse documents"
              aria-label="Collapse documents"
            >
              <LuChevronLeft />
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 p-2 border-b border-gray-200">
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="text-primary text-xs p-1 border border-primary rounded-sm2"
              title="Expand documents"
              aria-label="Expand documents"
            >
              <LuChevronRight />
            </button>
            <div className="relative" title={`${selectedFiles.length} selected`} aria-label={`${selectedFiles.length} selected`}>
              <FaRegFileAlt className="text-primary text-xl" />
              {selectedFiles.length > 0 && (
                <span className="absolute -top-1 -right-2 bg-primary text-white text-[10px] leading-none px-1.5 py-0.5 rounded-full">
                  {selectedFiles.length}
                </span>
              )}
            </div>
            <button
              onClick={handleSelectAll}
              className="text-gray-700 text-xs p-1 border border-gray-300 rounded-sm2"
              title="Select all processed documents"
              aria-label="Select all processed documents"
            >
              <MdOutlineSelectAll className="text-base" />
            </button>
            <button
              onClick={handleDeselectAll}
              className="text-gray-700 text-xs p-1 border border-gray-300 rounded-sm2"
              title="Clear selection"
              aria-label="Clear selection"
            >
              <MdClear className="text-base" />
            </button>
          </div>
        )}

        {!sidebarCollapsed && (
          <div className="p-3 space-y-2 overflow-y-auto">
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={handleSelectAll}
                className="text-sm text-primary px-2 py-1 border border-primary rounded-sm2 flex items-center gap-1"
                title="Select all processed documents"
              >
                <MdOutlineSelectAll className="text-base" />
                Select All
              </button>
              <button
                onClick={handleDeselectAll}
                className="text-sm text-gray-700 px-2 py-1 border border-gray-300 rounded-sm2 flex items-center gap-1"
                title="Clear selection"
              >
                <MdClear className="text-base" />
                Clear
              </button>
            </div>

            {/* Unprocessed first with action */}
            {unprocessedFiles.length > 0 && (
              <>
                <p className="text-[11px] uppercase text-gray-400 mt-1">Not processed</p>
                {unprocessedFiles.map((file) => (
                  <div
                    key={file.id}
                    className={`flex items-center gap-2 p-2 rounded-md border border-yellow-300 bg-yellow-50`}
                  >
                    <FaFileAlt className="text-yellow-600" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.file_name}</p>
                      <span className="text-[10px] text-gray-600 uppercase">{file.extention}</span>
                    </div>
                    <button
                      onClick={() => handleProcessFile(file.id)}
                      disabled={!!processing[file.id]}
                      className={`text-xs px-2 py-1 rounded-sm2 flex items-center gap-1 border ${processing[file.id] ? 'opacity-60 cursor-not-allowed' : 'border-yellow-600 text-yellow-600'}`}
                      title="Process this document"
                    >
                      <MdOutlinePlayCircle /> {processing[file.id] ? 'Processing...' : 'Process'}
                    </button>
                  </div>
                ))}
                <hr className="my-2" />
              </>
            )}

            {/* Processed and selectable */}
            {processedFiles.length > 0 ? (
              processedFiles.map((file) => (
                <div
                  key={file.id}
                  className={`flex items-center gap-2 p-2 rounded-md border ${
                    selectedFiles.includes(file.id)
                      ? 'border-primary bg-[rgb(211,74,129,0.06)]'
                      : 'border-gray-200 hover:bg-gray-50'
                  } cursor-pointer`}
                  onClick={() => handleFileToggle(file.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedFiles.includes(file.id)}
                    onChange={() => handleFileToggle(file.id)}
                    className="text-primary focus:ring-primary w-4 h-4"
                  />
                  {/* <FaFileAlt className="text-primary/80" /> */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.file_name}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">{file.extention}</span>
                      {selectedFiles.includes(file.id) && (
                        <span className="text-[10px] inline-flex items-center gap-1 text-primary">
                          <FaCheckCircle /> Selected
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-gray-500">
                <FaRegFileAlt className="mx-auto text-2xl mb-2 text-gray-300" />
                <p>No processed documents available</p>
                <p className="text-xs">Upload and process documents first</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chat panel */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2" aria-live="polite">
            <h2 className="text-lg font-semibold text-gray-800">Multi-Document Chat</h2>
            {selectedFiles.length > 0 && (
              <span className="bg-[rgb(211,74,129,0.1)] text-primary text-xs font-medium px-2.5 py-0.5 rounded-full">
                {selectedFiles.length} selected
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setMessages([]); try { localStorage.removeItem('multiDocChatCache'); } catch(_){} }}
              className="text-[12px] px-2 py-1 border border-gray-300 rounded-sm2 flex items-center gap-1"
              title="Clear history"
            >
              <RiDeleteBin6Line className="text-sm" />
              Clear
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" aria-live="polite">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <FaRegFileAlt className="mx-auto text-4xl mb-4 text-gray-300" />
              <p className="text-lg font-medium">Multi-Document Chat</p>
              <p className="text-sm">Select documents from the left panel and start asking questions.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.is_user_message ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.is_user_message
                      ? "bg-primary text-white"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  <div className="text-sm">
                    {message.is_user_message ? (
                      <p>{message.message}</p>
                    ) : (
                      <div>
                        {message.documents_used && (
                          <div className="mb-2 p-2 bg-[rgb(211,74,129,0.1)] rounded text-xs text-primary flex items-center gap-2">
                            <FaFileAlt className="text-sm" />
                            <span className="font-semibold">Documents used:</span>
                            <span className="text-gray-700">{message.documents_used.map(doc => doc.name).join(', ')}</span>
                          </div>
                        )}
                        <div className="prose prose-sm max-w-none response_style">
                          {showingLetters && index === messages.length - 1
                            ? parse(sanitizeHtml(message.message.slice(0, currentIndex + 1)))
                            : parse(sanitizeHtml(message.message))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className={`text-xs mt-1 ${message.is_user_message ? "text-white" : "text-gray-600"}`}>
                    {time(message.create_at)}
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className={`flex justify-start`}>
              <p className={`max-w-[73%] text-sm py-2 rounded-md px-3 flex gap-3 items-center text-left`}>
                <Loading color="#9ca3af" />
              </p>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

       
        {/* {showSetting && (
          <div className="mb-2 px-4 flex items-center gap-3">
            <div className="[&>button]:border focus:[&>button]:ring-0 hover:[&>button]:border-primary [&>button]:border-gray-300 [&>button]:rounded-sm flex items-center gap-4 [&>button>span>svg]:ml-5 [&>button]:text-gray-700">
              <span className="text-gray-700 text-sm">Response in </span>{" "}
              <Dropdown className="" label={language} placement="top">
                <Dropdown.Item onClick={() => setLanguage("Auto-detect")}>Auto-detect</Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("English")}>English</Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("French")}>French</Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("Arabic")}>Arabic</Dropdown.Item>
              </Dropdown>
            </div>
            <div className="[&>button]:border focus:[&>button]:ring-0 hover:[&>button]:border-primary [&>button]:border-gray-300 [&>button]:rounded-sm flex items-center gap-4 [&>button>span>svg]:ml-5 [&>button]:text-gray-700">
              <span className="text-gray-700 text-sm">Use Model :  </span>{" "}
              <Dropdown className="" label={model} placement="top">
                <Dropdown.Item onClick={() => setModel("Mistral")}>Mistral</Dropdown.Item>
                <Dropdown.Item onClick={() => setModel("Llama")}>Llama</Dropdown.Item>
              </Dropdown>
            </div>
          </div>
        )} */}

        
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-end space-x-2">
            <div className="flex-1">
              <div className={`w-full p-3 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-primary focus-within:border-transparent ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}>
                <AutoResizableTextarea
                  value={question}
                  handleInput={(e) => setQuestion(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={
                    selectedFiles.length === 0
                      ? "Select documents first, then ask a question..."
                      : `Ask a question about ${selectedFiles.length} selected document${selectedFiles.length > 1 ? 's' : ''}...`
                  }
                />
              </div>
            </div>
           
            <button
              onClick={() => handleSubmit()}
              disabled={isLoading || !question.trim() || selectedFiles.length === 0}
              className={`bg-primary text-white rounded-sm2 w-9 h-9 flex justify-center items-center ${
                isLoading || selectedFiles.length === 0 ? "!bg-gray-400" : ""
              }`}
            >
           
                <LuSend className="text-xl" />
            
            </button>
          </div>
        </div>


      </div>
    </div>
  );
}

export default MultiDocumentChat;
