import { useParams } from 'react-router-dom';
import NavBar from './navBar';
import useFetch from '../hook/useFetch';
import PdfViewer from './pdf_viewer';
import Chats from './chats';
import Loading from './Loading';
import CSVViewer from './csv_viewer';
import Viewer from './test';


function ChatSpace() {
  const { id } = useParams();
  const { data: fileData, error: fileError, isLoading: fileIsLoading , fetchData} = useFetch(`/api/document/file/${id}`);
  
  return (
    <div className="flex flex-col relative bg-gray-100  h-[100vh]   ">
      <NavBar />

      <div className='flex flex-col !h-[100%] flex-1 md:flex-row relative gap-2 w-full  p-3'>
        {fileIsLoading ? (
          <div className="flex  items-center justify-center w-full h-[87vh]">
            <Loading padding={3} />
          </div>
        ) : (
          <> 
        {(fileData.file_type === 'PDF' || fileData.file_type === 'DOCX' ) && (
              <PdfViewer url={fileData ?  fileData.file_path : '' } fetchData={fetchData} fileData={fileData} loading={fileIsLoading} />
            )} 
            {( fileData.file_type === 'TXT') && (
              <PdfViewer url={fileData ?  fileData.file_path : '' } fetchData={fetchData} fileData={fileData} loading={fileIsLoading} />
            )} 
            {(fileData.file_type === 'CSV' || fileData.file_type === 'XLSX') && (
              <CSVViewer url={fileData ? 'http://127.0.0.1:8080/' + fileData.file_path : '' } fetchData={fetchData} fileData={fileData} loading={fileIsLoading} />
            )} 
          </>
        )}

        <div className='!w-full  '>
          <Chats fileData={fileData} />
        </div>
      </div>
    </div>
  );
}

export default ChatSpace;
