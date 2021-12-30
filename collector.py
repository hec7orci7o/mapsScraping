import re, json
import scrapper as sc
from selenium.common.exceptions import WebDriverException
# import nltk
# from nltk.corpus import stopwords

class collector:
    def __init__(self, domainList: list, language= "spanish") -> None:
        self.domainList = domainList    # Lista de dominios sobre la que se realizara la busqueda
        self.wordList   = set()         # Lista de palabras obtenidas para una busqueda de varios dominios
        self.resultados = dict()        # Diccionario que alamacena si una url tiene emails o no
        # nltk.download()
        # stopWords = set(nltk.corpus.stopwords.words(language))

    def __del__(self) -> None:
        pass

    def getWords(self, url: str, domain: str) -> list:
        try:
            words = re.sub(f"^(.+://)?(www.)?{domain}/?", "", url)
            words = re.sub(f"[^\w]", " ", words).rstrip()
            return words.split(" ")
        except:
            return []

    def makeBag(self, links: list, domain: str) -> set:
        bag = set()
        bag = [word for url in links for word in self.getWords(url, domain)]
        return set(bag)

    def updateResultados(self, url: str, value: bool) -> None:
        # Asocia a una url una salida: true / false 
        self.resultados.update({url : value})

    def saveCollection(self, filename="collected", format=".json", encoding="utf-8") -> None:
        with open(filename + format, mode="w+", encoding=encoding) as f:
            data = {
                "word_list": list(self.wordList),
                "datos": self.resultados
            }
            json.dump(data, f, ensure_ascii=False, indent=4)

    def collect(self, save= False, filename="collected", format=".json", encoding="utf-8") -> None:
        scrapper = sc.Scrapper()

        for i, domain in enumerate(self.domainList):
            print(f"{i + 1} - recogiendo datos de: https://{domain}")
            # Visita una nueva pagina
            scrapper.driver.get(url= f"https://{domain}")
            linkLinks = scrapper.getLinks(domain)                   # Recoge los links internos del dominio
            print(f"{len(linkLinks)} enlaces encontrados.")
            self.wordList.union(self.makeBag(linkLinks, domain))    # Actualiza la lista de palabras

            # Recorre toda la web para actualizar los pares del diccionario "resultados"
            for url in linkLinks:
                try:
                    scrapper.driver.get(url= url)
                    emailList = scrapper.getEmails()
                    self.updateResultados(url, len(emailList) >= 1)
                except WebDriverException:
                    pass

        # Elimina stop-words
        # self.wordList.difference_update( self.stopWords) )

        if save:
            print(f"Guardando los datos en: {filename + format}\n\t - codificacion utilizada: {encoding}")
            self.saveCollection(filename, format, encoding)