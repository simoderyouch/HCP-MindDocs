import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import useFetch from "../hook/useFetch";
import Loading from "./Loading";
import { LuSend } from "react-icons/lu";
import useAxiosPrivate from "../hook/useAxiosPrivate";
import parse from "html-react-parser";
import sanitizeHtml from "../shared/utils/sanitizeHtml";
import AutoResizableTextarea from "./AutoResizableTextarea";
import { time } from "../utils/time";
import { Dropdown } from "flowbite-react";
import { IoMdSettings } from "react-icons/io";
import TableComponent from "./TableComponents";
import { FaRegLightbulb } from "react-icons/fa";

function Chats({ fileData }) {
  const { id } = useParams();
  const {
    data: messagesData,
    error: messagesError,
    isLoading: messagesIsLoading,
    fetchData,
  } = useFetch(`/api/chat/messages/${id}`);
  const [question, setQuestion] = useState("");
  const [pdf_questions, setPdfQuestions] = useState([]);
  const [pdf_summary, setPdfSummary] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const [showSetting, setShowSetting] = useState(false);
  const [language, setLanguage] = useState("Auto-detect");
  const [model, setModel] = useState("Mistral");

  const [messages, setMessages] = useState([]);
  const axiosInstance = useAxiosPrivate();
  const [showingLetters, setShowingLetters] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const chatEndRef = useRef(null);
  const [showAllSuggestions, setShowAllSuggestions] = useState(false);

  useEffect(() => {
    if (messagesIsLoading || !Array.isArray(messagesData)) return;

    // No messages
    if (messagesData.length === 0) {
      setPdfSummary("");
      setPdfQuestions([]);
      setMessages([]);
      return;
    }

    // Summary (first item)
    const summaryMessage = messagesData[0]?.message ?? "";
    setPdfSummary(summaryMessage);

    // Questions (second item) – robust parsing with fallbacks
    let parsedQuestions = [];
    const rawQuestions = messagesData[1]?.message;
    if (typeof rawQuestions === "string") {
      try {
        parsedQuestions = JSON.parse(rawQuestions.toString());
      } catch (e) {
        // If parsing fails, keep empty; we'll fill fallbacks below
        parsedQuestions = [];
      }
    }

    // Normalize to string array
    const normalizedQuestions = Array.isArray(parsedQuestions)
      ? parsedQuestions.map((q) => (typeof q === "string" ? q : JSON.stringify(q)))
      : [];

    // Fallback suggestions if questions missing/invalid
    const fallbackQuestions = [
      "Give me a brief summary.",
      "List the key points with bullets.",
      "What are the main entities (names, dates, amounts)?",
      "What are the conclusions or recommendations?",
      "Are there any action items or deadlines?",
    ];

    setPdfQuestions(normalizedQuestions.length > 0 ? normalizedQuestions : fallbackQuestions);

    // History: from the third element onward
    const history = messagesData.slice(2);
    setMessages(history);
  }, [id, messagesData, messagesIsLoading]);

  useEffect(() => {
    fetchData();
  }, [fileData]);

  const handleSubmit = async (question_p = "", task = "response") => {
   
    setShowingLetters(false);
    setIsLoading(true);
    const currentTime = new Date();
    const formattedTime = currentTime.toISOString();
    question_p = typeof question_p === "string" ? question_p : question;
    setMessages([
      ...messages,
      { message: question_p, is_user_message: true, create_at: formattedTime },
    ]);
    const question_temp = question_p
    setQuestion("");

    try {
      

      const response = await axiosInstance.post(`/api/chat/${id}`, {
        question: question_temp,
        language: language,
        model: model,
        document: id,
        task: task,
      });
      
     
      
      setCurrentIndex(0);
      const currentTime = new Date();
      const formattedTime = currentTime.toISOString();
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          message: response.data.message,
          is_user_message: false,
          create_at: formattedTime,
        },
      ]);
      setShowingLetters(true);
      setQuestion("");
    } catch (error) {
      console.error("Error submitting question:", error);
    } finally {
      setIsLoading(false);
    }
  };


  const providedQuestion = (question) => {
    handleSubmit(question);
  };
  /*   const extractData = () => {
    handleSubmit('Extract Data','data');
  }; */

  useEffect(() => {
    let timeout;
    if (
      showingLetters &&
      currentIndex < messages[messages.length - 1]?.message.length
    ) {
      const randomDelay = Math.floor(Math.random() * (10 - 5) + 1) + 10;
      const randomUpdate = Math.floor(Math.random() * (5 - 1) + 1) + 5;

      timeout = setTimeout(() => {
        setCurrentIndex((prevIndex) => prevIndex + randomUpdate);
      }, randomDelay);
    } else {
      setShowingLetters(false);
    }
    return () => clearTimeout(timeout);
  }, [showingLetters, currentIndex, messages]);

  

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "auto", block: "end" });
    }
  }, [messages, currentIndex]);

  return (
    <div className="bg-white relative flex flex-col border pt-2 w-full h-[85vh] ">
      <div className="flex  flex-1 overflow-y-scroll w-full h-[87vh] flex-col py-5 px-3 gap-5" aria-live="polite">
        {messagesIsLoading ? (
          <Loading padding={3} />
        ) : (
          <>
            {/* Summary block always at top */}
            {pdf_summary && (
              <div className={`flex justify-start`}>
                <div className={`max-w-[83%] break-words flex flex-col gap-1 leading-7 text-sm py-3 rounded-md px-4 bg-gray-100`}>
                  <div className="flex flex-col gap-2 leading-7 text-sm response_style">
                    <p>{parse(pdf_summary)}</p>
                  </div>
                </div>
              </div>
            )}

           

            {messages &&
              messages.map((message, index) => {
                const isLastMessage = messages.length === index + 1;
                return (
                  <div
                    key={index}
                    className={`flex ${
                      message.is_user_message ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      ref={isLastMessage ? chatEndRef : null}
                      className={`max-w-[83%] break-words		 flex flex-col gap-1 leading-7 text-sm py-3 rounded-md px-4 ${
                        message.is_user_message
                          ? " bg-primary !text-white"
                          : " bg-gray-100"
                      }`}
                    >
                      <div className="flex flex-col break-words	 gap-2 leading-7 text-sm response_style">
                        {message.is_user_message ? (
                          <p className="!text-white whitespace-pre-wrap	break-all	">
                            {message.message}
                          </p>
                        ) : showingLetters && isLastMessage ? (
                          parse(message.message.slice(0, currentIndex + 1))
                        ) : (
                          parse(sanitizeHtml(message.message))
                        )}
                      </div>

                      <span
                        className={`text-end text-[0.7rem] ${
                          message.is_user_message ? "text-white" : "text-gray-600"
                        }`}
                      >
                        {time(message.create_at)}
                      </span>
                    </div>
                  </div>
                );
              })}

            {isLoading && (
              <div className={`flex justify-start`}>
                <p
                  className={`max-w-[73%] text-sm py-2 rounded-md px-3 flex gap-3 items-center text-left `}
                >
                  <Loading color="#9ca3af" />{" "}
                  {
                    // <span className="text-gray-900">en reflexion....</span>
                  }
                </p>
              </div>
            )}
 {/* Suggested questions (moved under summary) */}
 {!showingLetters && !isLoading && pdf_questions && pdf_questions.length > 0 && (
              <div className="flex justify-start">
                <div className="max-w-[97%] w-full bg-[rgb(211,74,129,0.06)] border border-[rgb(211,74,129,0.15)] rounded-sm2 px-3 py-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-gray-800">
                      <FaRegLightbulb className="text-primary" />
                      <span className="text-sm font-semibold">Suggested questions</span>
                    </div>
                    {pdf_questions.length > 6 && (
                      <button
                        type="button"
                        onClick={() => setShowAllSuggestions(!showAllSuggestions)}
                        className="text-[12px] text-primary border border-primary rounded-sm2 px-2 py-1"
                        aria-label={showAllSuggestions ? "Show fewer suggestions" : "Show all suggestions"}
                      >
                        {showAllSuggestions ? "Show less" : `Show all (${pdf_questions.length})`}
                      </button>
                    )}
                  </div>
                  <ul className="flex flex-wrap gap-2">
                    {(showAllSuggestions ? pdf_questions : pdf_questions.slice(0, 6)).map((question, index) => (
                      <li key={index}>
                        <button
                          type="button"
                          onClick={() => providedQuestion(question)}
                          className="px-3 py-1.5 rounded-full border border-gray-300 text-xs md:text-sm text-gray-700 bg-white hover:border-primary hover:bg-[rgb(211,74,129,0.06)] focus:outline-none focus:ring-2 focus:ring-primary"
                          aria-label={`Ask: ${question}`}
                        >
                          <span className="font-bold mr-1">{index + 1}.</span>
                          {question}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            
          </> 
        )}
      </div>

      <div className="flex flex-col left-0 bottom-0 w-full bg-white p-3">
       {/*  {showSetting && (
          <div className="mb-4 flex items-center gap-3">
            <div className="[&>button]:border focus:[&>button]:ring-0 hover:[&>button]:border-primary [&>button]:border-gray-300 [&>button]:rounded-sm   flex items-center gap-4 [&>button>span>svg]:ml-5  [&>button]:text-gray-700">
              <span className="text-gray-700 text-sm">Response in </span>{" "}
              <Dropdown className="" label={language} placement="top">
                <Dropdown.Item onClick={() => setLanguage("Auto-detect")}>
                  Auto-detect
                </Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("English")}>
                  English
                </Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("French")}>
                  French
                </Dropdown.Item>
                <Dropdown.Item onClick={() => setLanguage("Arabic")}>
                  Arabic
                </Dropdown.Item>
              </Dropdown>
            </div>
            <div className="[&>button]:border focus:[&>button]:ring-0 hover:[&>button]:border-primary [&>button]:border-gray-300 [&>button]:rounded-sm   flex items-center gap-4 [&>button>span>svg]:ml-5  [&>button]:text-gray-700">
              <span className="text-gray-700 text-sm">Use Model :  </span>{" "}
              <Dropdown className="" label={model} placement="top">
                <Dropdown.Item onClick={() => setModel("Mistral")}>
                  Mistral
                </Dropdown.Item>
                <Dropdown.Item onClick={() => setModel("Finetuned BERT")}>
                Finetuned BERT

                </Dropdown.Item>
                
              </Dropdown>
            </div>
          </div>
        )} */}

        <div className="flex  items-end p-2 border border-gray-150 rounded-sm2 w-full relative ">
          <AutoResizableTextarea
            placeholder={"Saisissez votre question ici..."}
            value={question}
            handleInput={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          <div className=" right-2 flex items-center gap-2 bottom-2">
            {/* <button
              className={` text-primary border  rounded-sm2  w-9 h-9 flex justify-center items-center ${
                isLoading || (fileData && !fileData.processed)
                  ? "!bg-gray-400 border-gray-400 !text-white"
                  : "border-primary"
              }`}
              onClick={() => setShowSetting(!showSetting)}
              disabled={isLoading || (fileData && !fileData.processed)}
            >
              <IoMdSettings className="text-xl" />
            </button> */}
            <button
              className={`bg-primary text-white   rounded-sm2  w-9 h-9 flex justify-center items-center ${
                isLoading || (fileData && !fileData.processed)
                  ? "!bg-gray-400"
                  : ""
              }`}

              type="submit"
              onClick={handleSubmit}
              disabled={isLoading || (fileData && !fileData.processed)}
            >
              <LuSend className="text-xl" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chats;
