import time
import re
import random
import mathematics
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

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
        "container": "//div[@class='V0h1Ob-haAclf OPZbO-KE6vqe o0s21d-HiaYvf']", # contenedor del resultado
        "title": "//div[@class='qBF1Pd gm2-subtitle-alt-1']",                    # nombre que identifica al resultado
    }

    def __init__(self) -> None:
        firefox_options = webdriver.FirefoxOptions()
        self.driver = webdriver.Firefox(options=firefox_options)

    def __del__(self) -> None:
        self.driver.quit()

    def acceptCookies(self) -> None:
        cookies_accept_button = self.driver.find_element(By.XPATH, self.__CONSTANT["accept_cookies"])
        cookies_accept_button.click()

    def getTitle(self) -> str:
        try:
            return self.driver.find_element(By.XPATH, self.__FINDER["title"]).text
        except:
            return None

    def getScore(self) -> float:
        try:
            return float(self.driver.find_element(By.XPATH, self.__FINDER["score"]).text.replace(",","."))
        except:
            return None
    
    def getNReviews(self) -> int:
        try:
            x = self.driver.find_element(By.XPATH, self.__FINDER["num_reviews"]).text
            lista = re.findall("\d+", x)
            return int(lista[0])
        except:
            return None

    def getTag(self) -> str:
        try:
            return self.driver.find_element(By.XPATH, self.__FINDER["tag"]).text
        except:
            return None

    def getAddress(self) -> str:
        try:
            return self.driver.find_element(By.XPATH, self.__FINDER["address"]).text
        except:
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
            return self.driver.find_element(By.XPATH, self.__FINDER["domain"]).text
        except:
            return None
    
    def getPhone(self) -> str:
        try:
            return self.driver.find_element(By.XPATH, self.__FINDER["phone"]).text
        except:
            return None

    def getEmail(self) -> None:
        try:
            return None
        except:
            return None

    def getGPCode(self) -> str:
        try:
            return self.driver.find_element(By.XPATH, self.__FINDER["plus_code"]).text
        except:
            return None

    def getRHour(self) -> None:
        try:
            return None
        except:
            return None

    def goTo(self, router) -> None:
        router.click()

    def backTo(self) -> None:
        router = self.driver.find_element(By.XPATH, self.__CONSTANT["back_button"])
        router.click()

    def getData(self) -> dict:
        time.sleep(random.uniform(0.5, 1.5))
        return {
            "title" : self.getTitle(),
            "score" : self.getScore(),
            "num_reviews" : self.getNReviews(),
            "tag" : self.getTag(),
            "address" : self.getAddress(),
            "coords" : self.getCoords(self.driver.current_url),
            "domain" : self.getDomain(),
            "phone" : str(self.getPhone()).replace(" ", ""),
            "plus_code" : self.getGPCode(),
        }

    def scroll(self, current) -> int:
        links = self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])
        cResult = 1 # resultado actual

        while current >= len(links):
            # time.sleep(mathematics.calc(current))
            time.sleep(0.1)
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

        return len(links)

    def scrap(self, url: str) -> list:
        self.driver.get(url)    # buscar resultados para la query
        self.acceptCookies()    

        visitados = {}
        item = 1
        numResults = len(list(self.driver.find_elements(By.XPATH, self.__CONSTANT["title"])))
        while item <= numResults:
            numResults = self.scroll(item)
            result = self.driver.find_element(By.XPATH,  "(" + self.__CONSTANT["container"] + ")" + f"[{item}]")
            key = str(self.driver.find_element(By.XPATH, "(" + self.__CONSTANT["title"] + ")" + f"[{item}]").text).capitalize()

            if key not in list(visitados.keys()):
                self.goTo(result)
                visitados.update({key: self.getData()})
                print(f"{item}\t- Data collected for: {key}")
                self.backTo()
            item += 1

        return list(visitados.values())
