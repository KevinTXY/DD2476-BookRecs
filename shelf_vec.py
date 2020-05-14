from elasticsearch import Elasticsearch
import numpy as np

def read_shelf_file(idf):
    if idf:
         file = "shelves_idf.txt"
    else:
        file = "shelves.txt"
    shelf_to_pos = {}
    shelf_to_score = {}
    f = open(file, "r")
    lines = f.readlines()
    f.close()
    for i in range(len(lines)):
        shelf_to_pos[ lines[i].split(":")[1].strip("\n")[1:] ] = i
        shelf_to_score[ lines[i].split(":")[1].strip("\n")[1:] ] = float(lines[i].split(":")[0])
    return(shelf_to_pos,shelf_to_score)

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
res1 = es.search(index="good_reads", body={"query": {"match": {"_id":874}}})
res2 = es.search(index="good_reads", body={"query": {"match": {"_id":5}}})
shelf_to_pos,shelf_to_score = read_shelf_file(True)
#print(shelf_to_pos.keys())
res1_shelf_vec = [0]*len(shelf_to_pos)
res2_shelf_vec = [0]*len(shelf_to_pos)
for s in res1["hits"]["hits"][0]["_source"]["shelves"].split(";"):
    name,count = s.split(":")
    if name in shelf_to_pos:
        #print(name)
        #print(shelf_to_pos[name])
        res1_shelf_vec[shelf_to_pos[name]] = int(count) * shelf_to_score[name]

for s in res2["hits"]["hits"][0]["_source"]["shelves"].split(";"):
    name,count = s.split(":")
    if name in shelf_to_pos:
        res2_shelf_vec[shelf_to_pos[name]] = int(count) * shelf_to_score[name]
#print(res2_shelf_vec)
#print(res1_shelf_vec)
print(np.inner(np.array(res1_shelf_vec),np.array(res2_shelf_vec))  / (np.linalg.norm(np.array(res1_shelf_vec))*np.linalg.norm(np.array(res2_shelf_vec))))


