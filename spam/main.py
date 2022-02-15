from re import sub
import smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import scandir, getcwd, getenv
from os.path import abspath
from dotenv import load_dotenv

load_dotenv()

def ls(path = getcwd()) -> list:
    return [abspath(arch.path) for arch in scandir(path) if arch.is_file()]

def readKeysAux(filename: str, key: str, format= "unique") -> list:
    with open(filename, "r", encoding="utf-8") as fd:
        data = json.load(fd)

    if format == "unique": return [data[i][key] for i in data if data[i][key] != None and data[i][key] != []]
    else: 
        keys = []
        for i in data:
            try:
                if data[i][key] != None and data[i][key] != []:
                    for subkey in data[i][key]:
                        if subkey != None:
                            keys.append(subkey)
            except: pass
        return keys

def readKeys(listNames: list, key: str, format= "unique") -> list:
    keys = []
    for filename in listNames:
        for iter in readKeysAux(filename, key, format):
            keys.append(iter)
    print(f"{len(keys)} queries <{key}> cargadas...")
    return keys

def sendMail(to: str, subject: str, message: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = getenv("USER")
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP_SSL(host= getenv("HOST"), port= getenv("PORT"))
    server.starttls()

    server.login(msg['From'], getenv("PASS"))
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()    

def main() -> None:
    files = ls(path="data")
    keys = readKeys(files, key="email", format="list")
    # sendMail(to="", subject="", message="")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass