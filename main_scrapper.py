import scrapper as sc
import pprint

def main()-> None:
    queries = [
        "floristerias zaragoza",
    ]
    scrapper = sc.Scrapper()

    for query in queries:
        url = f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es"
        data = scrapper.scrap(url=url, save=True, filename=query.replace(" ","_"),
                    title=True, score=True, num_reviews=True, tag=True, address=True, coords=True,
                    domain=True, email=True, phone=True, plus_code=True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass