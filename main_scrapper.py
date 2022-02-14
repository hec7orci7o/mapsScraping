import scrapper as sc

def main(query)-> None:
    scrapper = sc.Scrapper(myAgent=None, myProxy="98.12.195.129:443", headless=False)

    query = query.lower()
    url = f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es"
    scrapper.scrap(
        url=url, 
        save=True, filename=query.replace(" ","_"), format=".json",
        title=True, score=True, num_reviews=True, 
        tag=True, address=True, coords=True,
        domain=True, phone=True, plus_code=True,
        email=True
    )
    del scrapper

if __name__ == "__main__":
    try:
        query = input("introduzca la query a scrapear: ")
        main(query)
    except KeyboardInterrupt:
        pass