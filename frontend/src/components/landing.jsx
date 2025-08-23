import { GoArrowRight } from "react-icons/go";
import { useFileContext } from '../Service/Context.jsx';
import { Link, useNavigate  } from 'react-router-dom';
import NavBar from "./navBar.jsx";
import Loading from "./Loading.jsx";
import { useState, useEffect } from 'react';
import useAxiosPrivate from "../hook/useAxiosPrivate.js";
const Landing = () => {
  const { handleUpload, token, user } = useFileContext();
  const [isDragging, setIsDragging] = useState(false);
  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);

   const axiosInstance = useAxiosPrivate()
   const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = (error) => reject(error);
    });
  };
  const base64ToFile = (base64, filename) => {
    const arr = base64.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
  
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
  
    return new File([u8arr], filename, { type: mime });
  };
  useEffect(() => {
    const fetchData = async () => {
      const storedFile = localStorage.getItem('pendingFile');
      if (storedFile && token && user) {
        setIsUploading(true);
        try {
          const { base64, name } = JSON.parse(storedFile);
          const file = base64ToFile(base64, name);
          const res = await handleUpload(file, axiosInstance);
          setIsUploading(false);
          navigate(`/chatroom/${res.data.file.id}`);
          localStorage.removeItem('pendingFile');
        } catch (error) {
          console.error('Error uploading file:', error);
          setIsUploading(false);
        }
      }
    };
  
    fetchData();
  }, [token, user, handleUpload]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    console.log(file)
    setFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const setFile = async (file) => {
    if (token && user) {
      setIsUploading(true);
      const res = await handleUpload(file, axiosInstance);
      setIsUploading(false);
      navigate(`/chatroom/${res.data.file.id}`);
    } else {
      const base64File = await fileToBase64(file);
      localStorage.setItem('pendingFile', JSON.stringify({ base64: base64File, name: file.name }));
      navigate('/user/login');
    }
  };
  return (
    <div className="flex flex-col bg-slate-100 min-h-[100vh] backgroud-landing">
      <NavBar />
      <div className="container max-w-[50rem] mx-auto pt-[3.6rem] pb-[5rem]">
        <h1 className="font-bold text-dark text-[2.6rem] leading-[2.8rem] tracking-tighter mb-5 text-center">
          <span className="text-primary text-[2.5rem]">
            Discutez avec votre documents
          </span>
          <br></br>Explorez, Analysez, Comprendre
        </h1>
        <h2 className="text-gray-500 text-sm leading-7 text-center">
          Discutez avec des PDF, des documents Word, Excel.<br></br>Un assistant de fichiers alimenté par l'IA et NLP, Il permet aux utilisateurs de poser des questions
          liées aux documents et d'obtenir des réponses et des résumer concises avec les extraits pertinents et les références de page. <Link to="/user/login" className="text-primary items-center ">
            Commencez maintenant
          </Link>
        </h2>

        <div className="px-5 py-6 mt-5 border border-gray-100 bg-white rounded-lg">
          <label
          for="dropzone-file"
            className={`flex items-center justify-center w-full h-[12rem] border-[1.6px] ${isDragging ? 'border-primary' : 'border-gray-300'} border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg
                className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 20 16"
              >
                <path
                  stroke="currentColor"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
                />
              </svg>
              <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                <span className="font-semibold">Glissez et déposez</span> les fichiers ici pour les télécharger
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                PDF, WORD (DOC, DOCX), TXT, CSV, XLS, XLSX (MAX 200MB)
              </p>
              {isUploading ? <Loading /> : ''}
            </div>
            <input onChange={handleFileChange} id="dropzone-file" type="file" className="hidden" />
          </label>
        </div>
      </div>
    </div>
  );
};

export default Landing;
