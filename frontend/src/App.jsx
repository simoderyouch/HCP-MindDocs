import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './components/landing';
import './index.css';
import ChatSpace from './components/chatSpace'; 
import ChatDashboard from './components/chatDashboard'; 
import MultiDocumentChatPage from './components/MultiDocumentChatPage';
import RegisterComponents from './components/register';
import Login from './components/login';
import { useFileContext } from './Service/Context'; // Assuming you have an AuthContext

function PrivateRoute({ element, ...rest }) {
  const { token } = useFileContext();
  console.log(token)

  return token ? (
    element
  ) : (
    <Navigate to="/user/login" replace />
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route exact path="/" element={<Landing />} />
        <Route exact path="/user/register" element={<RegisterComponents />} />
        <Route exact path="/user/login" element={<Login />} />
        
        
        <Route path="/chatroom" element={<PrivateRoute element={<ChatDashboard />} />} />
        <Route path="/chatroom/:id" element={<PrivateRoute element={<ChatSpace />} />} />
        <Route path="/multi-chat" element={<PrivateRoute element={<MultiDocumentChatPage />} />} />
      </Routes>
    </Router>
  );
}

export default App;
