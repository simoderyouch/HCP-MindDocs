import React, { useState, useEffect } from 'react';
import { MdDelete } from "react-icons/md";
import {  useNavigate   } from 'react-router-dom';
import { FaRegMessage } from "react-icons/fa6";
import { IoDocumentTextOutline } from "react-icons/io5";

import NavBar from './navBar';
import axios from '../utils/axios'
import { useFileContext } from '../Service/Context';
import useAxiosPrivate from '../hook/useAxiosPrivate';
import { ModalGeneralComponent } from './ModalGeneralComponent';
import { Accordion } from "flowbite-react";
import { Link } from 'react-router-dom';
import useFetch from '../hook/useFetch';
import Loading from './Loading';
import GetCompanyDocument from './getCompanyDocument';
import { RiDeleteBin6Line } from "react-icons/ri";
import { BiMessageSquareDetail } from "react-icons/bi";
import { FaRegFileAlt } from "react-icons/fa";
import { MdOutlinePlayCircle } from "react-icons/md";


function ChatDashboard() {
  const axiosInstance = useAxiosPrivate();
  const navigateTo = useNavigate()
  const [isDragging, setIsDragging] = useState(false);

  const { handleUpload } = useFileContext();
  const {data ,error, isLoading , fetchData } = useFetch('/api/document/files')
  const [deletingIndex, setDeletingIndex] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [processing, setProcessing] = useState({});
  const files = data
  
  const handleFileChange =async (e) => {
    const file = e.target.files[0];
    setIsUploading(true)
    const res  = await handleUpload(file,axiosInstance);
    setIsUploading(false)
    await fetchData();
    console.log(res)
/*     navigateTo(`${res.data.file.id}`)
 */  };
  const handleFileDelete = async (fileId,index) => {
    setDeletingIndex(index);
    try {
      const reponse = await axiosInstance.delete(`/api/document/file/${fileId}`)
       console.log(reponse)
        
        
       setDeletingIndex(null);
       
          fetchData();
    } catch (error) {
      console.error('An error occurred while deleting the file:', error);
      setDeletingIndex(null);
    }
  };
  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    setIsUploading(true)
    const res  = await handleUpload(file,axiosInstance);
    setIsUploading(false)
    
    console.log(res)
    navigateTo(`${res.data.file.id}`)
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleFileProcess = async (fileId) => {
    try {
      setProcessing(prev => ({ ...prev, [fileId]: true }));
      await axiosInstance.get(`/api/document/process/${fileId}`)
      /* await fetchData(); */
      navigateTo(`${fileId}`)
    } catch (error) {
      console.error('An error occurred while processing the file:', error);
    } finally {
      setProcessing(prev => ({ ...prev, [fileId]: false }));
    }
  };

  /* const sortFilesByGroup = (files) => {
    const sortedFiles = {
      'Document ( doc, docx, pdf, txt )': []
    -- 'Spreadsheet ( csv, xls, xlsx )': [], 
     
    };

    // Group files by their types
    for (let fileType in files) {
      if (['doc', 'docx', 'pdf', 'txt'].includes(fileType)) {
        sortedFiles['Document ( doc, docx, pdf, txt )'].push(...files[fileType]);
      } else if (['csv', 'xls', 'xlsx'].includes(fileType)) {
        -- sortedFiles['Spreadsheet ( csv, xls, xlsx )'].push(...files[fileType]);
      } 
    }
    
    console.log(sortedFiles)
    return sortedFiles;
  }; */

  return (
    <div className="flex flex-col bg-gray-50 min-h-[100vh] ">
      <NavBar/>
       
      <div className='flex container pt-8 pb-4 justify-between items-center'>
        <h1 className='font-bold text-2xl'>My Files</h1>
        <div className='flex items-center gap-4'>
          
          <Link to="/multi-chat">
            <button className='bg-primary py-2 text-sm px-5 font-medium text-white rounded-sm2 flex items-center gap-2 transition-colors'>
              <FaRegFileAlt />
              Multi-Document Chat
            </button>
          </Link>

        <ModalGeneralComponent
        Class={' [&>div]:px-0 [&>div]:overflow-hidden [&>div]:!h-[100vh] [&>div>div]:flex [&>div>div]:flex-col [&>div>div]:!h-[100%]' }
        Button={(props) => (
         
          <button  {...props} className='border-primary border py-2 text-sm px-5 font-medium text-primary rounded-sm2'>HCP Document</button>
        )}
        header={
          <h3 className="text-md font-semibold text-gray-900 dark:text-white">
            {" "}
            Select from HCP Document
          </h3>
        }
        body={<GetCompanyDocument fetchfiles={fetchData} />}
      />
          
        <ModalGeneralComponent
        
        Button={(props) => (
         
          <button  {...props} className='bg-primary py-2 text-sm px-5 font-medium text-white rounded-sm2'>Upload Document</button>
        )}
        header={
          <h3 className="text-md font-semibold text-gray-900 dark:text-white">
            {" "}
            Upload your Document
          </h3>
        }
        body={<div class="flex items-center p-3 justify-center w-full">
        <label
          for="dropzone-file"
          class={`${isDragging ? 'border-primary' : 'border-gray-300'} flex flex-col items-center justify-center w-full h-[12rem] border-[1.6px] border-gray-300 border-dashed  rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          
          <div class="flex flex-col items-center justify-center pt-5 pb-6">
            <svg
              class="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 20 16"
            >
              <path
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
              />
            </svg>
            <p class="mb-2 text-sm text-gray-500 dark:text-gray-400">
              <span class="font-semibold">Glissez et déposez</span>  les fichiers ici pour les télécharger
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
            PDF, WORD (DOC, DOCX), TXT, CSV, XLS, XLSX (MAX 200MB)
            </p>

             {isUploading ? <Loading /> : ''}
          </div>
          <input  onChange={handleFileChange} disabled={isUploading} id="dropzone-file" type="file" class="hidden" />
        </label>
      </div>}
      />
        </div>
      </div>
      <hr className='container'></hr>
      {
          isLoading ? <Loading padding={8} /> :  <div>
          <Accordion   className='container mt-4 mb-[5rem] border-0 flex flex-col gap-4'>
         
            {Object.entries(files).map(([type, fileList]) => (
              
<ul className='flex flex-col gap-2 mb-2' id={type}> 
                 {fileList.map((file, index) => {


                    const readableSize = file.size >= 1024 * 1024
                      ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                      : `${(file.size / 1024).toFixed(1)} KB`;

                    
                    const uploadDate = new Date(file.upload_date).toLocaleDateString('en-GB', {
                      day: '2-digit', month: 'short', year: 'numeric',
                    });

                    return (
                    <li  key={file.id} className='border bg-white rounded-sm2 flex justify-between items-center px-4 py-3 text-sm '> 
                    <div className='flex justify-center items-center gap-4'>
                    <span   className="w-9 h-9 flex justify-center items-center bg-[rgb(211,74,129,0.1)] rounded-sm2"><IoDocumentTextOutline size='19px' color='rgb(113 16 55)'/>
                    </span>
                    <div className='flex flex-col gap-2'>
                    <span className='font-bold text-gray-900'>{file.file_name}  { file.extention.toLowerCase() === 'docx' ? '( converted to pdf)' : null} </span>
                    <div className='flex  items-center  gap-2'>
                      <span className='h-4 w-9 bg-[rgb(211,74,129,0.1)] text-center flex justify-center items-center rounded-md font-medium text-primary text-[10px]'> <span>{file.extention}</span></span>
                      <div className=' text-gray-400 text-[11px]'>
            {readableSize}  •  Uploaded on {uploadDate}
          </div>
                    </div>
                    </div>
                 
                      </div>   

                    <div className='flex gap-2 items-center'>
                      {!file.processed && (
                        <button
                          onClick={() => handleFileProcess(file.id)}
                          disabled={!!processing[file.id]}
                          className={`border-primary rounded-sm2 border px-3 py-2 text-primary flex items-center gap-2 ${processing[file.id] ? 'opacity-60 cursor-not-allowed' : ''}`}
                        >
                          {processing[file.id] ? ( <>
                            <Loading w_h='11' />
                            <span>Processing...</span></>

                          ) : (
                            <>
                              <MdOutlinePlayCircle className='text-[1rem]' />
                              <span>Process</span>
                            </>
                          )}
                        </button>
                      )}
                      <button className={`border px-4 py-2 bg-primary text-white rounded-sm2 ${deletingIndex === index ? 'pointer-events-none' : 'pointer-events-auto\t'}`}><Link className="flex justify-center items-center gap-2" to={`/chatroom/${file.id}`}>                     
                      <FaRegMessage />

                      Chat</Link></button>
                      <button  onClick={() => handleFileDelete(file.id,index)}  className='border-primary rounded-sm2 border px-3 py-2 text-primary'>{deletingIndex === index ? <Loading w_h='11' /> : <RiDeleteBin6Line className='text-[1rem]' />}  </button>
                    </div>
                    
                    </li>
                  )})}
                </ul> 



              /*<Accordion.Panel key={type} >
              
              
              <Accordion.Title className=' focus:ring-0 bg-transparent !border-t-0  !border-b px-3 py-2 text-sm '>{type.toUpperCase()}   ( {fileList.length} )</Accordion.Title>
              <Accordion.Content className='!border-t-0'>
                <ul className='flex flex-col gap-2 mb-2'> 
                 {fileList.map((file, index) => {


                    const readableSize = file.size >= 1024 * 1024
                      ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                      : `${(file.size / 1024).toFixed(1)} KB`;

                    
                    const uploadDate = new Date(file.upload_date).toLocaleDateString('en-GB', {
                      day: '2-digit', month: 'short', year: 'numeric',
                    });

                    return (
                    <li  key={file.id} className='border bg-white rounded-sm2 flex justify-between items-center px-4 py-3 text-sm '> 
                    <div className='flex justify-center items-center gap-4'>
                    <span   className="w-9 h-9 flex justify-center items-center bg-[rgb(211,74,129,0.1)] rounded-sm2"><IoDocumentTextOutline size='19px' color='rgb(113 16 55)'/>
                    </span>
                    <div className='flex flex-col gap-2'>
                    <span className='font-bold text-gray-900'>{file.file_name}  { file.extention.toLowerCase() === 'docx' ? '( converted to pdf)' : null} </span>
                    <div className='flex  items-center  gap-2'>
                      <span className='h-4 w-9 bg-[rgb(211,74,129,0.1)] text-center flex justify-center items-center rounded-md font-medium text-primary text-[10px]'> <span>{file.extention}</span></span>
                      <div className=' text-gray-400 text-[11px]'>
            {readableSize}  •  Uploaded on {uploadDate}
          </div>
                    </div>
                    </div>
                 
                      </div>   

                    <div className='flex gap-2 items-center'>
                      <button className={`border px-4 py-2 bg-primary text-white rounded-sm2 ${deletingIndex === index ? 'pointer-events-none' : 'pointer-events-auto\t'}`}><Link className="flex justify-center items-center gap-2" to={`/chatroom/${file.id}`}>                     
                      <FaRegMessage />

                      Chat</Link></button>
                      <button  onClick={() => handleFileDelete(file.id,index)}  className='border-primary rounded-sm2 border px-3 py-2 text-primary'>{deletingIndex === index ? <Loading w_h='11' /> : <RiDeleteBin6Line className='text-[1rem]' />}  </button>
                    </div>
                    
                    </li>
                  )})}
                </ul>
              
              </Accordion.Content>
              
              </Accordion.Panel> */
             
              
            ))}
          
          </Accordion>
          </div>
        }
     
    </div>
  );
}

export default ChatDashboard;
