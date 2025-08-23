import React, { useState, useCallback, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import useAxiosPrivate from "../hook/useAxiosPrivate";

import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { HiOutlinePlusSm, HiMinusSm } from "react-icons/hi";
import { BsLayoutSidebarInset } from "react-icons/bs";
import Loading from "./Loading";

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

export default function PdfViewer({ url, fileData, fetchData, loading }) {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [selectedText, setSelectedText] = useState("");
  const [ss, setSs] = useState(
    "Structure d’un arbre de d´ecision et d´efinitions Un arbre de d´ecision (decision tree) est une structure tr`es utilis´ee en apprentissage machine. Son fonctionnement repose sur des heuristiques construites selon des techniques d’apprentissage supervis´ees"
  );
  const [showButton, setShowButton] = useState(false);
  const [isProcessing, setisProcessing] = useState(false);
  const [showSideBar, setShowSideBar] = useState(false);
  const [buttonPosition, setButtonPosition] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(0.5);
  const pdfContainerRef = useRef(null);
  const axiosInstance = useAxiosPrivate();
  useEffect(() => {
    function handleScroll() {
      setShowButton(false);
      if (pdfContainerRef && pdfContainerRef.current) {
        // Calculate the current page based on the scroll position
        const container = pdfContainerRef.current;
        const scrollTop = container.scrollTop;
        const pageHeight = container.scrollHeight / numPages;
        let currentPage = Math.floor(scrollTop / pageHeight) + 1;
        // Ensure currentPage is within the valid range of 1 to numPages
        currentPage = Math.min(Math.max(currentPage, 1), numPages);
        setPageNumber(currentPage);
      }
    }
    if(numPages < 70) {

    if (pdfContainerRef && pdfContainerRef.current) {
      pdfContainerRef.current.addEventListener("scroll", handleScroll);
      return () => {
        if (pdfContainerRef.current) {
          pdfContainerRef.current.removeEventListener("scroll", handleScroll);
        }
      };
    }
  }
  }, [numPages]);


 
 

  const textRenderer = (textItem) => {
    return `<p>${textItem.str}</p>`;
  };

  
  const handleProcess = async () => {
    console.log("loading");
    setisProcessing(true);
    try {
      const response = await axiosInstance.get(`/api/document/process/${fileData.id}`);
      console.log(response);
      setisProcessing(false);

      fetchData();
    } catch (error) {
      console.log(error);
      setisProcessing(false);
    }
  };
  
 
  function handleSideBarPage(page) {
    const pageElement = document.querySelector(
      `[page_number="${page}"]`
    );
    console.log(pageElement)
    if (pageElement) {
      pageElement.scrollIntoView({  block: "start" });

    }

    setPageNumber(page)
  }
  
 
  function handleChange(number) {
    
   
    const pageElement = document.querySelector(
      `[page_number="${number}"]`
    );
    console.log(pageElement)
    if (pageElement) {
      pageElement.scrollIntoView({  block: "start" });

    }
    setPageNumber(number);

  }
  function prevPage() {
    const newPageNumber = Math.max(pageNumber - 1, 1);
   
    const pageElement = document.querySelector(
      `[page_number="${newPageNumber}"]`
    );
    console.log(pageElement)
    if (pageElement) {
      pageElement.scrollIntoView({  block: "start"  });

    }
    setPageNumber(newPageNumber);
   }

  function nextPage() {
    const newPageNumber = Math.min(pageNumber + 1, numPages);
   
    const pageElement = document.querySelector(
      `[page_number="${newPageNumber}"]`
    );
    console.log(pageElement)
    if (pageElement) {
      pageElement.scrollIntoView({  block: "start" });

    }
    setPageNumber(newPageNumber);

  }


  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  function handleZoomIn() {
    setZoom((prevZoom) => Math.min(prevZoom + 0.1, 4)); // Limit zoom to 400%
  }

  function handleZoomOut() {
    setZoom((prevZoom) => Math.max(prevZoom - 0.1, 0.4)); // Limit zoom to 10%
  }

  const CustomRenderer = ({ pageNumber, customTextRenderer }) => {
    // Your custom rendering logic here
    return (
      <div className="custom-page">
        {/* Render text layer using customTextRenderer */}
        {customTextRenderer({ str: "Your custom text", itemIndex: 0 })}
        {/* You can add other custom elements or components here */}
      </div>
    );
  };
  const textLayerRenderer = ({ str, itemIndex }) => {
    return str;
  };

  return (
    <div className="relative border flex flex-col rounded-sm2  md:min-w-[23rem] md:max-w-[23rem]   lg:min-w-[35rem] lg:max-w-[35rem] max-h-[85vh] min-h-[85vh]">
      <div className="top-0 left-0 px-8  justify-between h-[4rem]  bg-white z-20 flex py-2 border-b">
        <button onClick={() => setShowSideBar(!showSideBar)}>
          <BsLayoutSidebarInset className="text-gray-800" />
        </button>

        <div className="flex items-center gap-4">
          <button
            onClick={prevPage}
            disabled={pageNumber === 1}
            className="hover:bg-gray-50"
          >
            <IoIosArrowUp className="-rotate-90 text-gray-900" />
          </button>
          <div className="font-medium text-sm">
            <input
              type="number"
              value={pageNumber}
              min="1"
              max={numPages}
              onChange={(e) => handleChange(parseInt(e.target.value))}
              className="border w-16 py-1 px-2 text-sm border-gray-200 rounded-sm2 focus:border-primary outline-none focus:ring-0"
            />{" "}
            of {numPages}
          </div>
          <button
            onClick={nextPage}
            disabled={pageNumber === numPages}
            className="hover:bg-gray-50"
          >
            <IoIosArrowDown className="-rotate-90 text-gray-900" />
          </button>
        </div>

        <div className="flex [&>button]:flex [&>button]:items-center [&>button]:justify-center [&>button]:h-6 [&>button]:w-6 items-center  text-gray-900 gap-3 ">
          <button
            onClick={handleZoomIn}
            className="hover:bg-gray-50 rounded-full"
          >
            <HiOutlinePlusSm />
          </button>
          <span className="text-sm">{Math.round(zoom * 100)}%</span>
          <button
            onClick={handleZoomOut}
            className="hover:bg-gray-50 rounded-full"
          >
            <HiMinusSm />
          </button>
        </div>
      </div>

      <div
     
        className="relative  w-full !h-[calc(100%-4rem)] "
      >
       
        {!loading ? (
          <Document  file={url} className={'flex relative h-full w-full'} onLoadSuccess={onDocumentLoadSuccess}>
             {showSideBar ? (
          <div className="bg-gray-300 sticky w-[15rem] h-full overflow-y-scroll flex items-center  flex-col gap-3  py-5 px-9 ">
            
              {Array.from(new Array(numPages), (el, index) => (
                <button  key={`page_side_bar_${index + 1}`} onClick={()=> handleSideBarPage(index + 1)}>
                  <Page
                  
                  pageNumber={index + 1}
                  renderMode="canvas"
                  
                  renderTextLayer={false}
                  width={130}
                  className={` bg-transparant border w-full hover:opacity-100  ${pageNumber === (index + 1) ? 'opacity-100 ring-1 ring-primary' : 'opacity-55'}`}
                />
                </button>
              ))}
           
          </div>
        ) : null} 


            <div   ref={pdfContainerRef}  className="overflow-scroll  bg-gray-50 h-full w-full" >
            {numPages > 70 ? (
             <div id={`page_${pageNumber}`}  className="[&>div]:!bg-white mt-5 text-center flex justify-center items-center   [&>div]:border">
              <Page
                id={`page_${pageNumber}`}
                key={`page_${pageNumber}`}
                pageNumber={pageNumber}
                renderMode="canvas"
                customTextRenderer={textRenderer}
                scale={zoom}
                className={"bg-transparant"}
              />
              </div>
            ) : (
              Array.from(new Array(numPages), (el, index) => (
                <div id={`page_${index + 1}`}  className="[&>div]:!bg-white mt-5 text-center flex justify-center items-center   [&>div]:border"
                key={`page_${index + 1}`}  page_number={index + 1}>
                  <Page
                  
                  pageNumber={index + 1}
                  customTextRenderer={textRenderer}
                  renderMode="canvas"
                  scale={zoom}
                  className={`page_${index + 1} `}
                />
                </div>
              ))
            )}
            </div>
          
          </Document>
        ) : (
          <Loading padding={3} />
        )}
      </div>

      {fileData && !fileData.processed ? (
        isProcessing ? (
          <div className="absolute w-full h-full flex justify-center items-center z-50 bg-black bg-opacity-65  top-0 left-0 ">
            {" "}
            <Loading color="#ffffff" />{" "}
          </div>
        ) : (
          <div className="absolute w-full h-full flex justify-center items-center z-50 bg-black bg-opacity-65  top-0 left-0 ">
            <button
              className="border-dashed  border-2  border-white py-2 px-8 rounded-sm2 text-white"
              onClick={() => handleProcess()}
            >
              Analyse
            </button>
          </div>
        )
      ) : null}
    </div>
  );
}
