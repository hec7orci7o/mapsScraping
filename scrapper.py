import re, json, random, Levenshtein
from time import sleep
from timeit import default_timer
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, MoveTargetOutOfBoundsException
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

PATH = "data/"

class Scrapper:
    __FINDER = {
        "title": "//h1//span[1]",
        "score": "//div[@role='button']//span//span//span[@aria-hidden='true']",
        "num_reviews": "//span[@jsaction='pane.rating.moreReviews']",
        "tag": "//button[@jsaction='pane.rating.category'][1]",
        "address": "//button[contains(@data-item-id,'address')]",
        "domain": "//button[contains(@data-item-id,'authority')]",
        "phone": "//button[contains(@data-item-id,'phone:tel')]",
        "plus_code": "//button[contains(@data-item-id,'oloc')]",
    }

    __CONSTANT = {
        "accept_cookies": "//button[contains(.,'Acepto')]",
        "back_button":"//button[@aria-label='Atrás']",
        "container":"//div[contains(@class, 'V0h1Ob-haAclf') and contains(@class, 'OPZbO-KE6vqe')]", # contenedor generico
        "title": "//div[@class='qBF1Pd gm2-subtitle-alt-1']",                               # nombre que identifica al resultado
    }

    __FILTER_WORDS = [
        "contactanos", "contacto", "contactenos", "contact",
        "condiciones", "devoluciones", "cambios", "refund", 
        "nosotros", "about", "aviso", "terms", "conditions", 
        "legal", "service", "trabajar", "politica", "policy",
        "cookies", "privacidad", "preguntas", "frecuentes", 
        "faq", "garantia", "quienes", "somos", "ayuda"
    ]

    __MAX_INTENTOS = 5  # Maximo numero de paginas que puede intentar visitar hasta conseguir un email
    __MAX_WAIT     = 3  # Maximos segundos que puede esperar antes de tirar un TimeoutException al buscar un elemento

    def __init__(self, myAgent, myProxy, headless=False) -> None:
        # Proxy configuration
        proxy = Proxy() # https://proxyscrape.com/free-proxy-list # https://hidemy.name/en/proxy-list/
        proxy.proxy_type = ProxyType.MANUAL
        proxy.autodetect = False
        proxy.http_proxy = myProxy
        proxy.ssl_proxy = myProxy
        capabilities = webdriver.DesiredCapabilities.FIREFOX
        capabilities["marionette"] = False
        proxy.add_to_capabilities(capabilities)

        # Agent Configuration
        if myAgent == None:
            software_names = [SoftwareName.FIREFOX.value]
            operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
            user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
            # Get Random User Agent String.
            myAgent = user_agent_rotator.get_random_user_agent()

        # Headers configuration
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.set_preference("general.useragent.override", myAgent)   # https://gist.github.com/pzb/b4b6f57144aea7827ae4
        if headless: firefox_options.headless = True
        
        # Profile configuration
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.http", re.search(".*:", myProxy).group()[:-1])
        profile.set_preference("network.proxy.http_port", int(re.search(":.*", myProxy).group()[1:]))
        profile.set_preference("dom.webdriver.enabled", False)
        profile.set_preference('useAutomationExtension', False)
        profile.update_preferences()

        # Driver set-up
        self.driver = webdriver.Firefox(firefox_profile=profile, options=firefox_options, desired_capabilities=capabilities)
        self.chest = {}

    def __del__(self) -> None:
        # self.driver.delete_all_cookies()
        # self.driver.quit()
        pass

    def __loadBar(self, iteration, total, prefix="", suffix="", decimals=1, length=100, fill=">"):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLengh = int(length * iteration // total)
        bar = fill * filledLengh + "-" * (length - filledLengh)
        print(f"\r{prefix} | {bar}| {percent}% {suffix}", end="\r")
        if iteration == total:
            print()

    def __createKey(self, title: str) -> str:
        for v1, v2 in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u")]:
            title = title.replace(v1, v2)
        
        title = re.sub("[^\w]", " ", title)
        title = re.sub("\s+", " ", title)
        
        return title.lower()

    def getWords(self, url: str, domain: str) -> list:
        try:
            words = re.sub(f"^(.+://)?(www.)?{domain}/?", "", url)
            words = re.sub(f"[^\w]", " ", words).rstrip()
            return words.split(" ")
        except:
            return []

    def getWeight(self, url: str, domain: str) -> int:
        peso = 0
        for word in self.getWords(url, domain):
            pesos = [Levenshtein.distance(word.lower(), key.lower()) for key in self.__FILTER_WORDS]
            peso += min(pesos)
        return peso

    def getWlinks(self, links: list, domain: str) -> list:
        weightedUrls = [(str(url), self.getWeight(url, domain)) for url in links]
        weightedUrls.sort(key = lambda x: x[1], reverse=False)
        return weightedUrls

    def getLinks(self, domain) -> list:
        try:
            anchors = WebDriverWait(self.driver, 5).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
            )
        except TimeoutException:
            pass

        def checkLink(a):
            try:    return str(a.get_attribute('href'))
            except: pass

        def checkPool(link):
            try:    return link.find(domain) != -1
            except: pass

        anchors = self.driver.find_elements(By.TAG_NAME, "a")
        links = [checkLink(a) for a in list(anchors)]                           # consigue los enlaces
        links = list(filter(checkPool, links))                                  # se queda con los que navega por el propio sitio web
        links = list(filter(lambda link: re.search("^https", link), links))     # se queda con aquellos que comienzan con http evitando asi otros como: mailto, ...
        links = list(filter(lambda link: not re.search("\?.*=", link), links))  # elimina los que tienen alguna query
        links = list(filter(lambda link: len(link) <= 57, links))
        links = list(set(links))
        links = self.getWlinks(links, domain)                                   # ordena las url usando la distancia de Levenshtein
        return links

    def getEmails(self) -> list:
        EMAIL_REGEX = r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
        page_source = self.driver.page_source
        emails = [re_match.group() for re_match in re.finditer(EMAIL_REGEX, page_source)]
        def check(email):
            EMAIL_REGEX = r"[^\w]+"
            try:
                p1, p2 = email.split("@")
                return not(len(re.findall(EMAIL_REGEX, p1)) >= 1)
            except: 
                return False

        return list(set(filter(check, emails)))

    def acceptCookies(self) -> None:
        cookies_accept_button = WebDriverWait(self.driver, self.__MAX_WAIT).until(
            EC.presence_of_element_located((By.XPATH, self.__CONSTANT["accept_cookies"]))
        )
        cookies_accept_button.click()

    def getTitle(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["title"]))
            )
            return element.text
        except TimeoutException:
            return None

    def getScore(self) -> float:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["score"]))
            )
            return float(element.text.replace(",","."))
        except TimeoutException:
            return None
    
    def getNReviews(self) -> int:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["num_reviews"]))
            )
            lista = re.findall("\d+", element.text)
            return int(lista[0])
        except:
            return None

    def getTag(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["tag"]))
            )
            return element.text
        except TimeoutException:
            return None

    def getAddress(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["address"]))
            )
            return element.text
        except TimeoutException:
            return None

    def getCoords(self, url) -> tuple:
        try:
            coords = re.search(r"!3d-?\d\d?\.\d{4,8}!4d-?\d\d?\.\d{4,8}", url).group()
            coord = coords.split('!3d')[1]
            return tuple(coord.split('!4d'))
        except:
            return None
    
    def getDomain(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["domain"]))
            )
            return element.text
        except TimeoutException:
            return None
    
    def getPhone(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["phone"]))
            )
            return element.text
        except TimeoutException:
            return None

    def getEmail(self, domain) -> list:
        try:
            self.driver.get(url=f"https://{domain}")
            links = self.getLinks(domain)
            intento = 0
            for link, p in links:
                sleep(random.uniform(0.5, 1))
                emails = self.getEmails()
                if len(emails) != 0 or intento == self.__MAX_INTENTOS:
                    break
                intento += 1
                sleep(random.uniform(0.5, 1))
                self.driver.get(url=link)
                
            return emails
        except:
            return None

    def getGPCode(self) -> str:
        try:
            element = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.presence_of_element_located((By.XPATH, self.__FINDER["plus_code"]))
            )
            return element.text
        except TimeoutException:
            return None

    def getRHour(self) -> None:
        try:
            return None
        except:
            return None

    def getData(self, title=False, score=False,
                num_reviews=False, tag=False, address=False, 
                coords=False, domain=False, phone=False,
                plus_code=False) -> dict:
        data = {}
        if title:       data.update({"title" : self.getTitle()})
        if score:       data.update({"score" : self.getScore()})
        if num_reviews: data.update({"num_reviews" : self.getNReviews()})
        if tag:         data.update({"tag" : self.getTag()})
        if address:     data.update({"address" : self.getAddress()})
        if coords:      data.update({"coords" : self.getCoords(self.driver.current_url)})
        if domain:      data.update({"domain" : self.getDomain()})
        if phone:       data.update({"phone" : str(self.getPhone()).replace(" ", "")})
        if plus_code:   data.update({"plus_code" : self.getGPCode()})

        return data

    def goTo(self, router) -> None:
        sleep(random.uniform(0.5, 1))
        router.click()

    def backTo(self) -> None:
        try:
            router = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                EC.element_to_be_clickable((By.XPATH, self.__CONSTANT["back_button"]))
            )
            router.click()
        except TimeoutException:
            pass

    def scroll(self, current: int) -> int:
        links = self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])
        cResult = 1 # resultado actual
        while current >= len(links):
            try:
                sleep(random.uniform(0.2, 0.4))
                result = self.driver.find_element(By.XPATH, "(" + self.__CONSTANT["title"] + ")" + f"[{cResult}]")
                actions = ActionChains(self.driver)
                actions.move_to_element(result)
                actions.perform()
                self.driver.execute_script("arguments[0].scrollIntoView(true);", result)
                # Actualizo la lista de resultados encontrados
                links = self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])
                cResult += 1
            except NoSuchElementException:
                return len(links)
            except MoveTargetOutOfBoundsException:
                return len(links)

        return len(links)

    def __makeHeader(self, fields: list, sep= ";") -> str:
        header = ""
        for field in fields:
            header += field + f"{sep} "
        return header[:-2]

    def saveCollection(self, data: dict, filename="scraped", format=".json", encoding="utf-8") -> None:
        with open(PATH + filename + format, mode="w+", encoding=encoding) as f:
            try:
                if format == ".json":
                    json.dump(data, f, ensure_ascii=False, indent=4)
                elif format == ".csv":
                    header = ["title", "score", "num_reviews", "tag", "address", "coords", "domain", "phone", "plus_code", "email"]
                    sep = ";"

                    f.write(self.__makeHeader(header, sep))
                    f.write("\n")
                    for identifier in data:
                        for key in data[identifier]:
                            f.write( str(data[identifier][key]) + f"{sep}" )
                        f.write("\n")
            except:
                print("El formato debe ser: .json | .csv")
                self.saveCollection(data, filename="scraped", format=".json", encoding="utf-8")
                self.saveCollection(data, filename="scraped", format=".csv", encoding="utf-8")

    def scrap(self, url: str, save=False, filename="scraped", format=".json", encoding="utf-8",
              title=False, score=False, num_reviews=False, tag=False, address=False, coords=False,
              domain=False, email=False, phone=False, plus_code=False, group=False) -> list:
        sleep(random.uniform(30, 60))
        print("Searching results for: " + "\33[0;35;40m" + filename.replace("_", " ") + "\33[0m")
        inicioScrap = default_timer()
        self.driver.get(url=url)    # buscar resultados para la query
        sleep(random.uniform(0.5, 1))
        self.driver.maximize_window()
        try:    self.acceptCookies()
        except: pass
        if not group: self.chest = {}
        item = 1
        numResults = len(list(self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])))
        while item <= numResults:
            sleep(random.uniform(0.5, 1))
            inicio = default_timer()
            numResults = self.scroll(item)
            try:
                # Busca los elementos para poder desplazarse
                result = WebDriverWait(self.driver, self.__MAX_WAIT).until(
                    EC.presence_of_element_located((By.XPATH, "(" + self.__CONSTANT["container"] + ")" + f"[{item}]"))
                )
            except TimeoutException:
                break
            
            # Busca el titulo del elemento para evitar busquedas repetidas en el futuro
            key = self.__createKey(self.driver.find_element(By.XPATH, "(" + self.__CONSTANT["title"] + ")" + f"[{item}]").text)
            # key = str(self.__createKey(self.driver.find_element(By.XPATH, "(" + self.__CONSTANT["title"] + ")" + f"[{item}]").text)).encode()
            # key = sha1(key).hexdigest()
            if key not in list(self.chest.keys()):
                self.goTo(result)
                self.chest.update({key: self.getData(title=title, score=score, num_reviews=num_reviews, tag=tag, address=address, coords=coords, domain=domain, phone=phone, plus_code=plus_code)})
                fin = default_timer()
                print(f"{item}".rjust(4), "- ✅ data successfully collected.", "\33[0;36;40m" + "KEY: " + "\33[0m" + "\33[0;32;40m" + f"{key[:40]}".ljust(40) + "\33[0m" + "\33[0;32;40m" + "\33[0;36;40m" + " TIME: " + "\33[0m" + F"{fin - inicio:.2f}s".rjust(5))
                self.backTo()
            else:
                print(f"{item}".rjust(4), "- ❌ data already collected.     ", "\33[0;36;40m" + "KEY: " + "\33[0m" + "\33[0;31;40m" + f"{key}" + "\33[0m")
            item += 1

        if email:
            print("Seeking emails...")
            length = len(list(self.chest.keys()))
            self.__loadBar(0, length, prefix="Progress:", suffix="Complete", length=length)
            for i, key in enumerate(self.chest):
                if self.chest[key]["domain"] != None:
                    self.chest[key].update({"email": self.getEmail(self.chest[key]["domain"])})
                self.__loadBar(i + 1, length, prefix="Progress:", suffix="Complete", length=length)

        # Guarda los datos encontrados en un json o csv
        if save: self.saveCollection(self.chest, filename, format, encoding)

        finScrap = default_timer()
        print(f"Total results achieved: {len(self.chest)}")
        print(f"Total elapsed time: {(finScrap - inicioScrap) / 60:.2f}m", end="\n\n")

        return list(self.chest.values())
