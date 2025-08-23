
import { useEffect, useState } from "react";

export function ModalGeneralComponent({Class,Button,header,body,footer , closeModal }) {
  const [openModal, setOpenModal] = useState( closeModal || false);
  
  

  return (
    <>
    
      <Button onClick={() => setOpenModal(true)} />
    {
        openModal && (
            <div id="static-modal" data-modal-backdrop="static" tabindex="1"   aria-modal="true"  className={'flex   bg-black bg-opacity-30 overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-50 justify-center items-center w-full md:inset-0 h-[calc(100%-0rem)] min-h-full' + Class}>
            <div class="relative p-4 top-0  w-full max-w-2xl">
          
                <div class="relative bg-white rounded-lg shadow dark:bg-gray-700">
                  
                    <div class="flex items-center justify-between p-4 md:p-5 border-b rounded-t dark:border-gray-600">
                       {
                             header && header 
                       }
                        <button type="button" onClick={() => setOpenModal(false)} class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white" data-modal-hide="static-modal">
                            <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
                            </svg>
                            <span class="sr-only">Close modal</span>
                        </button>
                    </div>
                  
                    {
                        body && body 
                   
                    }
                   
                   {
                    footer && footer 
                   }
                </div>
            </div>
        </div>
        )
    }
    </>
  );
}
