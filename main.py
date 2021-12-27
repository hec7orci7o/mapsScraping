import scrapper as sc
import pprint

def showResults(data) -> None:
    print(f"Data collected from: {len(data)} results.")
    x = input("Do you want to see the data? y/n: ")
    if "y" == x.lower():
        pprint.pprint(data)

def main()-> None:
    query = input("query para google maps: ")
    scrapper = sc.Scrapper()
    data = scrapper.scrap(f"https://www.google.com/maps?q="+query.replace(" ", "+")+"&hl=es")
    del scrapper
    showResults(data)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass