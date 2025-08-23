import logo from "../assets/hcp.svg";
import { Link } from "react-router-dom";
import { useFileContext } from "../Service/Context";
import { FaRegUserCircle } from "react-icons/fa";
import { useState } from "react";

const NavBar = () => {
    const { token, user, logout } = useFileContext();
    const [userDropMenu, setuserDropMenu ] = useState(false)

    const handleLogout = () => {
        logout(); // Call the logout function from the context
        setuserDropMenu(false); // Close the user dropdown menu after logout
    }
    return (
        <div className="bg-white border-b border-gray-200">
 <nav className="flex container justify-between  items-center py-3 w-full  ">
        
        <ul className="flex items-center gap-4 [&>li]:text-sm [&>li]:text-gray-600">
        <Link to="/">  <img className="!w-[9rem] mr-9" src={logo} alt="Logo" /></Link>
      
        <li><Link to="/">Home</Link></li>
            <li><Link to="/chatroom">Documents</Link></li>
            <li><Link to="/multi-chat">Multi-Document Chat</Link></li>
        </ul>
        <ul className="flex items-center [&>li]:ml-9 [&>li]:text-sm [&>li]:text-gray-600">
         
            {token && user ? (
                <li className="relative">
                    <button className="focus:outline-none items-center flex gap-3" onClick={()=> setuserDropMenu(!userDropMenu)}> 
                        {user.user_name} 
                        <FaRegUserCircle  className="text-xl text-primary"/>

                    </button>
                    
                    {
                        userDropMenu && (
                            <ul className="absolute right-0 mt-2 px-4 py-5 z-40 space-y-2 bg-white border min-w-[15rem] border-gray-200 rounded-md shadow-lg ">
                            <li className="flex flex-col gap-2 ">
                                <span className="font-bold">
                                    {user.first_name} {user.last_name}
                                </span>
                                <span className="text-[0.7rem]">
                                    {user.email}
                                </span>
                            </li>
                            <hr className="my-3"></hr>
                            <li><Link to="/">Home</Link></li>
                            <li><Link to="/chatroom">Documents</Link></li>
                            <li><Link to="/multi-chat">Multi-Document Chat</Link></li>
                            <li><button onClick={handleLogout}>Logout</button></li>
                        </ul>
                        )
                    }
                </li>
            ) : (
                    <>
                        <li className="border border-primary !text-primary px-4 py-2 rounded-sm2">
                            <Link to="/user/login">Se connecter</Link>
                        </li>
                        <li className="bg-primary !text-white !ml-2 px-4 py-2 rounded-sm2">
                            <Link to="/user/register">S'inscrire</Link>
                        </li>
                    </>
                )}
        </ul>
    </nav>
        </div>
       
    );
};

export default NavBar;
