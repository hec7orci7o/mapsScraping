import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def sendMail(to: str, subject: str, message: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = os.getenv("USER")
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP_SSL(host= os.getenv("HOST"), port= os.getenv("PORT"))
    server.starttls()

    server.login(msg['From'], os.getenv("PASS"))
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()    

def main() -> None:
    sendMail(to="", subject="", message="")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass