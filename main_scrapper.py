import scrapper as sc

def main()-> None:
    queries = [
        "bares zaragoza"
    ]
    scrapper = sc.Scrapper()

    for query in queries:
        queries = list(map(lambda x: x.lower(), queries))
        url = f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es"
        scrapper.scrap(
            url=url, 
            save=True, filename=query.replace(" ","_"), format=".csv",
            title=True, score=True, num_reviews=True, 
            tag=True, address=True, coords=True,
            domain=True, phone=True, plus_code=True,
            email=True
        )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass