// FileUploadContext.js
import React, { createContext, useState, useContext } from "react";
import axios from '../utils/axios'
const Context = createContext();

export const useFileContext = () => useContext(Context);

export const ContextProvider = ({ children }) => {
  const parsedData = JSON.parse(localStorage.getItem('user'));
  console.log(parsedData)
  const [isLoading, setLoading] = useState(false);
  const [token, setToken] = useState( parsedData && parsedData.access_token  ? parsedData.access_token : null);
  const [user, setUser] = useState(parsedData && parsedData.user  ? parsedData.user : null);
  const [error, setError] = useState(null);
  


  const handleUpload = async (selectedFile,axiosInstance) => {
    if (!selectedFile) {
      console.error("No file selected.");
      return { error: "No file selected." }; // Return an error object
    }
  
    const formData = new FormData();
    formData.append("file", selectedFile);
    console.log(formData,selectedFile)
    try {
     
      

      const response = await axiosInstance.post('/api/document/upload', formData);
      console.log("File uploaded successfully:", response);
      return response; // Return the response data
    } catch (error) {
      // Handle error
      console.error("Error uploading file:", error);
      return error; // Return an error object
    }
  };
  
  const registerUser = async (userData) => {
    try {
      setLoading(true);
      setError(null)
      const response = await axios.post('/api/auth/register', userData);
      console.log("User registered successfully:", response);
      setLoading(false);
      return response; // Return the response data
    } catch (error) {
      // Handle error
      console.error("Error registering user:", error);
      setLoading(false);
      setError(error.response.data.detail)
      return error; // Return an error object
    }
  };
  const loginUser  = async (userData) => {
    try {
      setLoading(true);
      setError(null)

      const response = await axios.post('/api/auth/login', userData);
      console.log("User login successfully:", response);
      setLoading(false);
      setToken(response.data.access_token)
      setUser(response.data.user)
      localStorage.setItem('user', JSON.stringify(response.data));
      
      
      return response; 
    } catch (error) {
      // Handle error
      console.error("Error loging user:", error);
      setLoading(false);
      setError(error.response.data.detail)

      return error; // Return an error object
    }
  };
  const logout = async () => {
   
    try {
     
      const response = await axios.post('/api/auth/logout/');
      console.log("User logout successfully:", response);
     
      setToken(null);
      setUser(null);
      localStorage.removeItem('user');
      return response; 
    } catch (error) {
      // Handle error
      console.error("Error lougout user:", error);
     
      return error; 
    }
};
 
  return (
    <Context.Provider
      value={{ handleUpload  , registerUser ,loginUser , error , isLoading, token,setToken,logout, user}}
    >
      {children}
    </Context.Provider>
  );
};
