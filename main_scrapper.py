import scrapper as sc
import pprint

def main()-> None:
    queries = [
        # "floristerias zaragoza",
        # "tiendas de ropa zaragoza",
        # "tiendas de comida zaragoza",
        # "cines cerca de Zaragoza",
        "scape rooms zaragoza"
    ]
    scrapper = sc.Scrapper()

    for query in queries:
        url = f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es"
        data = scrapper.scrap(url=url, save=True, domain=True, filename=query.replace(" ","_"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass