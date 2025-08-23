import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { ContextProvider } from "./Service/Context.jsx";



ReactDOM.createRoot(document.getElementById('root')).render(
<ContextProvider>
      <App />
    </ContextProvider>
  
)
