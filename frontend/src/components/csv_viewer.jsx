import React, { useState, useEffect } from "react";
import Papa from "papaparse";
import useAxiosPrivate from '../hook/useAxiosPrivate';
import Loading from "./Loading";

function CSVViewer({ url, fileData, fetchData, loading }) {
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [isProcessing, setisProcessing] = useState(false);
  const axiosInstance = useAxiosPrivate();

  useEffect(() => {
    const fetchDataFromUrl = async () => {
      try {
        const response = await fetch(url);
        console.log(response)
        const text = await response.text();
       
        const result = Papa.parse(text, { header: true });
        const { data, meta: { fields } } = result;
        setData(data);
        setColumns(makeColumns(fields));
      } catch (error) {
        console.error("Error fetching CSV data:", error);
      }
    };

    if (url) {
      fetchDataFromUrl();
    }
  }, [url]);

  const makeColumns = rawColumns => {
    return rawColumns.map(column => {
      return { Header: column, accessor: column };
    });
  };
  const  handleProcess  = async () => {
    console.log('loading')
    setisProcessing(true)
    try {
        const response = await axiosInstance.get(`/api/process/${fileData.id}`)
        console.log(response)
        setisProcessing(false)

        fetchData()
    } catch (error) {
        console.log(error)
        setisProcessing(false)
    }
   
   }
  return (
    <div
     
      className="relative border flex flex-col rounded-sm2 overflow-scroll  md:min-w-[23rem] md:max-w-[23rem]   lg:min-w-[35rem] lg:max-w-[35rem] max-h-[87vh] min-h-[87vh]"
    > 
     {fileData && !fileData.processed  ? (
   isProcessing ?  <div className="absolute w-full h-full flex justify-center items-center z-50 bg-black bg-opacity-65  top-0 left-0 "> <Loading color='#ffffff' />  </div>: <div className="absolute w-full h-full flex justify-center items-center z-50 bg-black bg-opacity-65  top-0 left-0 ">
      <button className="border-dashed  border-2  border-white py-2 px-8 rounded-sm2 text-white" onClick={() => handleProcess()}>
        Analyse
      </button>
    </div>
  ) : null}


      {
        !loading ? 
        <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            {columns.map(column => (
              <th
                key={column.accessor}
                className="px-6 py-3 bg-gray-50 border text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider"
              >
                {column.Header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="bg-white">
              {columns.map(column => (
                <td
                  key={column.accessor}
                  className="px-6 py-4 border whitespace-no-wrap text-sm leading-5 text-gray-900"
                >
                  {row[column.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
     : (
      <Loading padding={3} />
    )
      }
     
    </div>
  );
}

export default CSVViewer;
