import Loading from './Loading';
import useFetch from '../hook/useFetch';
import { Accordion } from "flowbite-react";
import { useState } from 'react';
import {  useNavigate   } from 'react-router-dom';
import axios  from 'axios';
import { useFileContext } from '../Service/Context';
import useAxiosPrivate from '../hook/useAxiosPrivate';


const GetCompanyDocument = ({fetchfiles} ) => {
    const {data ,error, isLoading , fetchData } = useFetch('/api/document/hcp_files')
    const axiosInstance = useAxiosPrivate();
     const navigateTo = useNavigate()

    const { handleUpload } = useFileContext();
    const [isUploading, setIsUploading] = useState(false);
    const [fetchUrl, setFetchUrl] = useState(null);

    const downloadPdfAsFile = async (url, filename) => {
        const response = await axiosInstance.post('/api/document/get_pdf', null, {
            params: { url: url },
            responseType: 'json'
        });
    
        return response.data.file; // Adjust according to your response structure
    };
    
   
    const handleUrlChange = async (fileid , filename , fileIndex)=> {
        const url = 'https://www.hcp.ma' + fileid;
       
        setFetchUrl(fileIndex)
        try {
            const fileData = await downloadPdfAsFile(url, filename);
            // handle the fileData if needed
            setFetchUrl(null)
            fetchfiles()
            navigateTo(`/chatroom/${fileData.id}`)
           
        } catch (error) {
            console.error('Error processing URL:', error);
            setFetchUrl(null)
        }
    };
    const fetchdocument = async ()=> {
        setIsUploading(true);
        try {
            const response = await axiosInstance.get('/api/document/extract_urls/');
            setIsUploading(false);
           console.log(response)
           fetchData()
        } catch (error) {
            console.error('Error Fetch Document:', error);
            setIsUploading(false);
        }
    };
    return (
        <div className="    flex flex-col h-full !overflow-y-scroll w-full">
            {isLoading || isUploading  ? (
                <Loading />
            ) : (   <Accordion   className='border-0'>
                    {data && data.length > 0 ? (
                        data.map((item, index) => (
                            <Accordion.Panel key={index} >
                           
                            <Accordion.Title className=' focus:ring-0 bg-transparent    px-5 py-2 text-sm '>{item.text}</Accordion.Title>
                            <Accordion.Content className=''>
                               {item.files && item.files.length > 0 && (
                                  
                                  <ul className='flex flex-col px-4 py-3 gap-2 mb-2'> 
                                                {item.files.map((file, fileIndex) => (
                                                    <li className='border bg-white rounded-sm2 flex justify-start items-center gap-3 px-4 py-3 text-sm ' key={fileIndex}>
                                            {fetchUrl === file.id ? <span><Loading  w_h='12'  /></span> : <button onClick={()=> handleUrlChange(file.url,file.text, file.id)} className={`border flex justify-center items-center !w-[1rem] !h-[1rem] p-3 bg-primary text-white ${ fetchUrl || fetchUrl === file.id  ? 'pointer-events-none' : 'pointer-events-auto'	} rounded-full `}> <span> +</span>   </button>
                                                }
                                                        <span>{file.text}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                    
                                    )}
                               
                               </Accordion.Content>
                            </Accordion.Panel>
                        ))
                    ) : (
                       <div className='flex flex-col py-8 justify-center items-center gap-2'>
                         <p>No documents found.   
                           
                           </p>
                            <button className='border border-primary text-primary py-2 px-5 ' onClick={()=> fetchdocument()}>Fetch Document</button>
                       </div>
                    )}
                        </Accordion>

            )}
        </div>
    );
}


export default GetCompanyDocument 