from elasticsearch import Elasticsearch
from goodreads import client
gc = client.GoodreadsClient("NGr7Zl6XG9nTeNClLz9xA", "WILsiGKkWTEoKh4M7z11TF0P2ukSRcJ2OEFJMngDgY")
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
index = False
#check if index exists and if it's empty
if( not es.indices.exists("good_reads_test")):
    settings = {
        #this first thing I have no idea about yet 
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        #here we set mappings, like what elements we want our index to contain
        "mappings": {
            "book": {
                # dynamic strict forces all documents to contain the things we want, I think
                "dynamic": "strict",
                "properties": {
                    "title": {
                        "type": "text"
                    },
                    "description": {
                        "type": "text"
                    },
                    "id": {
                        "type": "integer"
                    },
                    "authors" :{
                        "type" : "text"
                    }, 
                    "n_pages" : {
                        "type" : "integer"
                    }
                }
            }
        }
    }
    # put in a document to so next line doesn't fail, can most likely be done in a better way 
    es.indices.create(index="good_reads_test", ignore=400, body=settings)
    testbody = {
        'title': 'test',
        'description': 'test_document, for testing', 
        'id' : 0 ,
        'authors' : 'john doe',
        'n_pages' : '666'
    }
    es.index(index = "good_reads_test",id=id, doc_type="book", body = testbody)
index = True
es.indices.refresh(index="good_reads_test")
#if it should index, start loading up the index with books
if(index):
    #this search returns highest index
    highest_index = int(es.search(index="good_reads_test", body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"])
    for i in range(highest_index+1,highest_index + 100):
        try:
            book = gc.book(i)
            print("indexing: " + book.title)
            book_body = {
                'title': book.title,
                'description': book.description, 
                'id' : i ,
                'authors' : ", ".join([n.name for n in  book.authors]),
                'n_pages' : book.num_pages
            }
            es.index(index = "good_reads_test", id = i, doc_type = "book", body = book_body)
        except:
            print("book id " + str(i) +" no good")

    # ", ".join([n.name for n in  book.authors])
    # e = es.search(index="davis_wiki", body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"]

#if one now wants to serach for like all books written by J K Rowlin one can search like this 
res = es.search(index="good_reads_test", body={"query": {"match": {"authors" :"J K Rowling" }}})
print(", ".join([h['_source']['title'] for h in res['hits']['hits']])
