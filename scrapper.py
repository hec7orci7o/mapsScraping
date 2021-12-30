import time, re, random, json, Levenshtein, sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, MoveTargetOutOfBoundsException

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

    def __init__(self, headless= False) -> None:
        firefox_options = webdriver.FirefoxOptions()
        if headless: firefox_options.headless = True
        self.driver = webdriver.Firefox(options=firefox_options)

    def __del__(self) -> None:
        self.driver.quit()

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
            for link in links:
                emails = self.getEmails()
                if len(emails) != 0 or intento == self.__MAX_INTENTOS:
                    break
                intento += 1
                time.sleep(2)
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

        time.sleep(random.uniform(0.2, 5))
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
        time.sleep(random.uniform(0.75, 1.5))
        router.click()

    def backTo(self) -> None:
        try:
            router = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, self.__CONSTANT["back_button"]))
            )
            router.click()
        except TimeoutException:
            pass

    def scroll(self, current) -> int:
        links = self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])
        cResult = 1 # resultado actual
        time.sleep(0.1)
        while current >= len(links):
            try:
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

    def saveCollection(self, data: dict, filename="scraped", format=".json", encoding="utf-8") -> None:
        with open(filename + format, mode="w+", encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def scrap(self, url: str, save=False, filename="scraped", format=".json", encoding="utf-8",
              title=False, score=False, num_reviews=False, tag=False, address=False, coords=False,
              domain=False, email=False, phone=False, plus_code=False) -> list:
        self.driver.get(url=url)    # buscar resultados para la query
        try:
            self.acceptCookies()
        except:
            pass
        visitados = {}
        item = 1
        numResults = len(list(self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])))
        while item <= numResults:
            numResults = self.scroll(item)
            try:
                # Busca los elementos para poder desplazarse
                result = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "(" + self.__CONSTANT["container"] + ")" + f"[{item}]"))
                )
            except TimeoutException:
                break
            
            # Busca el titulo del elemento para evitar busquedas repetidas en el futuro
            key = self.__createKey(self.driver.find_element(By.XPATH, "(" + self.__CONSTANT["title"] + ")" + f"[{item}]").text)
            if key not in list(visitados.keys()):
                self.goTo(result)
                visitados.update({
                    key: self.getData(title=title, score=score, num_reviews=num_reviews, tag=tag, address=address, coords=coords, domain=domain, phone=phone, plus_code=plus_code)})
                print(f"{item}".rjust(4), "- ✅ data successfully collected.", "KEY: " + "\33[0;32;40m" + f"{key}" + "\33[0m")
                self.backTo()
            else:
                print(f"{item}".rjust(4), "- ❌ data already collected.     ", "KEY: " + "\33[0;31;40m" + f"{key}" + "\33[0m")
            item += 1

        if email:
            for key in visitados:
                if visitados[key]["domain"] != None:
                    visitados[key].update({"email": self.getEmail(visitados[key]["domain"])})

        if save:
            self.saveCollection(visitados, filename, format, encoding)

        return list(visitados.values())
