"""
Chainalysis Graph File Decorator

Because why does it not do this already.

chris@cmcsec.com

"""
import json
import sys
import uuid
import zipfile

from etherscan import Etherscan
from pprint import pprint


""" set thy etherscan api key """

eth = Etherscan(open('etherscan_token').read())

def main():
    print("opening file {}..".format(sys.argv[1]))
    print("checking if it's a ZipFile..")

    if not zipfile.is_zipfile(sys.argv[1]):
        print("not a zip, aborting.")
        sys.exit(-1)

    with zipfile.ZipFile(sys.argv[1], mode="r") as archive:
        print("it's a zipfile. processing files..")
        for file in archive.namelist():
            if file == "graph.json":
                print("Found graph.json")
                graph = json.loads(archive.read("graph.json"))

    #print("{}".format(graph))

    print("There are {} nodes in this graph.".format(len(graph['nodes'])))
    print("There are {} annotations in this graph.".format(len(graph['textBoxes'])))
    print("There are {} arrows in this graph.".format(len(graph['arrows'])))

    print("Pulling data from etherscan and decorating contracts..")
    
    contract_info = []
    for node in graph['nodes']:
        try:
            details = eth.get_token_info_by_contract_address(node['address'])
            print("{} is a contract: {} ({}).".format(node['address'], details[0]['tokenName'], details[0]['tokenType']))
            contract_info.append(details)
        except AssertionError as e:
            print("{} is not a contract. Likely EOA.".format(node['address']))
            continue

    print("done.")
    print("found {} contracts.".format(len(contract_info)))
    for contract in contract_info:
        contract = contract[0]
        print("{}\t{}\t{}".format(contract['contractAddress'], contract['tokenName'], contract['tokenType']))

    print("Creating annotations...")
    """ now create annotation entries for each one using the etherscan data.
        need to find contract in the nodes list, get its coordinates, then create a textbox with a unique uuid and set the x,y coords to above the address location.
     """
    #pprint(graph['nodes'])
    for contract in contract_info:
        contract = contract[0]
        """ match annotation x,y to node x,y for related node """
        for node in graph['nodes']:
            if node['address'].upper() == contract['contractAddress'].upper():
                x = node['x'] + 40
                y = node['y'] - 80

                """ build annotation and coordinates """
                annotation = {
		    'text': contract['tokenName'] + " " + contract['tokenType'], 
		    'x': x, 
		    'y': y, 
		    'id': str(uuid.uuid4()) 
		}
                arrow = {
                    'id': str(uuid.uuid4()),
                    'from': annotation['id'],
                    'to': "ETH:" + node['address']
                }

                print("adding annotation ({}) to the graph...".format(annotation['text']))
                graph['textBoxes'].append(annotation)
                graph['arrows'].append(arrow)
    
    #print("printing graph textboxes update..\n\n") 
    #pprint(graph['textBoxes'], indent=2)
    #pprint(graph, indent=2)

    print("Updated Graph json!")
    print("There are {} nodes in this graph.".format(len(graph['nodes'])))
    print("There are {} annotations in this graph.".format(len(graph['textBoxes'])))
    print("There are {} arrows in this graph.".format(len(graph['arrows'])))
    print("writing out new annotated graph.json..")
    with open("graph.json","w") as fh:
        fh.write(json.dumps(graph))
        fh.close()

    print("zippy the zip...")
    with zipfile.ZipFile(sys.argv[1] + "-annotated.grf", mode="w") as archive:
        archive.write("graph.json")
    if zipfile.is_zipfile(sys.argv[1] + "-annotated.grf"):
        print("zipfile {} created.".format(sys.argv[1] + "-annotared.grf"))
    
    print("ok you may now reimport this decorated grf into reactor. happy hunting.")


if __name__ == "__main__":
    main()
