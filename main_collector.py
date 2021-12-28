import collector as cl

def main()-> None:
    domainList = [
        # Tipo: 
        "", "", "", "", "",
        "", "", "", "", "",
        # Tipo: 
        "", "", "", "", "",
        "", "", "", "", "",
        # Tipo: 
        "", "", "", "", "",
        "", "", "", "", "",
        # Tipo: 
        "", "", "", "", "",
        "", "", "", "", "",
        # Tipo: 
        "", "", "", "", "",
        "", "", "", "", "",
    ]
    print(len(domainList))
    # worker = cl.collector(domainList= domainList)
    # worker.collect(save= True)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass