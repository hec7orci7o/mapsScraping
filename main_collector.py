import json
import collector as cl

def getDomains() -> list:
    path = "data/"
    c = []
    for filename in ["floristerias_huesca"]:
        f = open(path + filename + ".json", "r", encoding="utf-8")
        x = json.load(f)
        listaDominios = [x[key]["domain"] for key in x.keys()]
    
    listaDominios = list(filter(lambda x: x != None, listaDominios))
    return listaDominios

def main()-> None:
    domainList = getDomains()
    print(f"emepzando el analisis para: {len(domainList)} dominios")
    worker = cl.collector(domainList= domainList)
    worker.collect(save= True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass