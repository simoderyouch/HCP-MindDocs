import { useState, useEffect } from 'react';
import useAxiosPrivate from './useAxiosPrivate';

const useFetch = (url) => {
  const axiosInstance = useAxiosPrivate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const response = await axiosInstance.get(url);
      
      setData(response.data);
      console.log(response.data)
      setError(null);
    } catch (error) {
      setError(error);
      setData(null);
    }
    setIsLoading(false);
  };
  useEffect(() => {
    

    fetchData();

    // Cleanup function to cancel the request if component unmounts
    return () => {
      // Cancel the axios request if it's still pending
    };
  }, [url]);

  return { data, error, isLoading , fetchData };
};

export default useFetch;
