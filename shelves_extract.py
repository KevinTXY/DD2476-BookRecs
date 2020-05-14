from elasticsearch import Elasticsearch
import numpy as np 

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
es.indices.put_settings(index="good_reads",
                        body= {"index" : {
                                "max_result_window" : 16000
                              }})
res = es.search(index="good_reads", body={"query": {"match_all": {}},"stored_fields":[],"size":"15000"})
es.indices
shelves_dict = {}
# goes from 0 to 15000, 
tot_count = 0
for i in range(15000):
    id = int(res["hits"]["hits"][i]["_id"])
    if id != 0:
        book = es.search(index="good_reads", body={"query": {"match": {"_id":id}}})
        shelves = book["hits"]["hits"][0]["_source"]["shelves"].split(";")
        for s in shelves:
            name,count = s.split(":")
            if name in shelves_dict:
                shelves_dict[name] += int(count)
                tot_count += int(count)
            else:
                shelves_dict[name] = int(count)
                tot_count += int(count)
print(len(shelves_dict))
sorted_dict = {k: v for k, v in sorted(shelves_dict.items(), key=lambda item: item[1],reverse = True)}
for i in range(50):
    key = list(sorted_dict.keys())[i]
    print(str(sorted_dict[key]) + " : " + key)

f = open("shelves.txt", "a")
for k in sorted_dict.keys():
    if int(sorted_dict[k]) > 1000:
        f.write(str( sorted_dict[k] )  + " : " + k +"\n")
        #f.write(str( np.log(tot_count / (sorted_dict[k] + 1) ) +1 ) + " : " + k +"\n")
f.close()
    