import scrapper as sc

def main(query)-> None:
    scrapper = sc.Scrapper(myAgent=None, myProxy="103.92.114.2:80", headless=False)

    query = query.lower()
    url = f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es"
    scrapper.scrap(
        url=url, 
        save=True, filename=query.replace(" ","_"), format=".csv",
        title=True, score=True, num_reviews=True, 
        tag=True, address=True, coords=True,
        domain=True, phone=True, plus_code=True,
        email=True
    )
    del scrapper

if __name__ == "__main__":
    try:
        main("floristerias zaragoza")
    except KeyboardInterrupt:
        pass