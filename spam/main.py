import pprint
import re
import smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import scandir, getcwd, getenv
from os.path import abspath
from dotenv import load_dotenv
import psycopg2
import cuid


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

def loadData(path = getcwd()) -> list():
    data = []
    for arch in scandir(path):
        if arch.is_file():
            try:
                x = re.search("floristerias(.)*.json", abspath(arch.path))
                key = x.group()[13:-5]
                fd = open(abspath(arch.path), "r", encoding="utf-8")
                value = json.load(fd)
                fd.close()
                data.append({key : value})
            except: 
                pass

    return data

def createQueries(data: list, tableName="public.\"ShopDB\"") -> list():
    unique = []
    queries = []
    for dictionary in data:
        for city in dictionary:
            for floristeria in dictionary[city]:
                try:
                    if dictionary[city][floristeria]["email"][0] not in unique:
                        columns = "("
                        values = "("
                        columns += "id, "
                        values += "\'" + cuid.cuid() + "\', "
                        try:   
                            if  dictionary[city][floristeria]["title"] != None:
                                values  += "'{}', ".format(dictionary[city][floristeria]["title"].lower())
                                columns += "shop, "
                        except: pass
                        try:    
                            values  += "'{}', ".format(city.replace("_", " "))
                            columns += "city, "
                        except: pass
                        try:    
                            if  dictionary[city][floristeria]["domain"] != None:
                                values  += "'{}', ".format(dictionary[city][floristeria]["domain"])
                                columns += "web, "
                        except: pass
                        try:    
                            if  dictionary[city][floristeria]["email"] != None:
                                unique.append(dictionary[city][floristeria]["email"][0])
                                values  += "'{}', ".format(dictionary[city][floristeria]["email"][0])
                                columns += "email, "
                        except: pass
                        try:
                            if  dictionary[city][floristeria]["phone"] != None:
                                values  += "'{}', ".format(dictionary[city][floristeria]["phone"][3:])
                                columns += "tel, "
                        except: pass
                        try:
                            if  dictionary[city][floristeria]["score"] != None:
                                values  += "{}, ".format(dictionary[city][floristeria]["score"])
                                columns += "score, "
                        except: pass
                        try:
                            if  dictionary[city][floristeria]["num_reviews"] != None:
                                values  += "{}, ".format(dictionary[city][floristeria]["num_reviews"])
                                columns += "reviews, "
                        except: pass
                        try:  
                            if  dictionary[city][floristeria]["coords"] != None:
                                values  += "{}, {}, ".format(dictionary[city][floristeria]["coords"][0], dictionary[city][floristeria]["coords"][1])
                                columns += "lat, long, "
                        except: pass
                        try:
                            if  dictionary[city][floristeria]["plus_code"] != None:
                                values  += "'{}', ".format(dictionary[city][floristeria]["plus_code"])
                                columns += "\"plusCode\", "
                        except: pass

                        columns += "\"createdAt\", \"updatedAt\""
                        values += "now(), now()"

                        values += ")"
                        columns += ")"
                        query = "INSERT INTO {} {} VALUES {};".format(tableName, columns, values)
                        queries.append(query)
                except: pass
    return queries

def insertFile(queries: list) -> None:
    with open("spam/insert.sql", "w", encoding="utf-8") as fd:
        for query in queries:
            fd.write(query + "\n")

def insertDB(queries: list()) -> None:
    conn = psycopg2.connect(database = "testdb", user = "postgres", password = "pass123", host = "127.0.0.1", port = "5432")
    print("Opened database successfully")

    cur = conn.cursor()
    
    for query in queries:
        cur.execute(query)
    conn.commit()

    print("Table loaded successfully")
    conn.close()

def main() -> None:
    # files = ls(path="data")
    # keys = readKeys(files, key="domain", format="unique")
    # print(keys)
    # sendMail(to="", subject="", message="")

    data = loadData(path="data")
    queries = createQueries(data)
    insertFile(queries)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass