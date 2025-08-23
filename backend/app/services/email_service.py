import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
from fastapi import HTTPException

def send_email(email: EmailStr, subject: str, message: str):
    
    """
    Send an email to the provided email address with the given subject and message.
    """

    
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'itsmodesign@gmail.com'
    smtp_password = 'cjjx nhej nylh mczz'
    
    msg = MIMEMultipart('alternative')
    msg['From'] = smtp_username
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(smtp_username, smtp_password)  
        
       
        server.sendmail(smtp_username, email, msg.as_string())
        
       
        server.quit()
    except Exception as e:
        
        print("Error:", e)  
        raise HTTPException(status_code=500, detail="Failed to send email")



def send_verification_email(email: EmailStr, verification_token: str):
    """
    Send a verification email to the provided email address with a verification token.
    """
    # Customize the email content as per your requirements
    subject = "Verify Your Email"
    verification_link = f"http://127.0.0.1:8080/api/auth/verify-email/{verification_token}"
    message = f"""
    <html>
    <body>
        <p>Please click the following link to verify your email:</p>
        <form action="{verification_link}" method="get">
            <button type="submit">Verify Email</button>
        </form>
        <p>If you cannot click the button, copy and paste the following link into your browser:</p>
        <a href="{verification_link}">{verification_link}</a>
    </body>
    </html>
    """    
    try:
       send_email(email, subject, message)
    except Exception as e:
        # Handle email sending errors gracefully
        raise HTTPException(status_code=500, detail=e)