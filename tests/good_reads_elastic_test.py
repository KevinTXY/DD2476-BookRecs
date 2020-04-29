from elasticsearch import Elasticsearch
from goodreads import client

index = "good_reads_test_2"
gc = client.GoodreadsClient("NGr7Zl6XG9nTeNClLz9xA", "WILsiGKkWTEoKh4M7z11TF0P2ukSRcJ2OEFJMngDgY")

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
#check if index exists and if it's empty
if( not es.indices.exists(index)):
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
                    },
                    "n_ratings" :{
                        "type" : "integer"
                    },
                    "avg_rating" : {
                        "type" : "float"
                    },
                    "rating_dist":{
                        "type" : "test"
                    },
                    "language_code":{
                        "type":"text"
                    },
                    "shelves":{
                        "type":"text"
                    }
                    
                }
            }
        }
    }
    # put in a document to so next line doesn't fail, can most likely be done in a better way 
    es.indices.create(index=index, ignore=400, body=settings)
    testbody = {
        'title': 'test',
        'description': 'test_document, for testing', 
        'id' : 0 ,
        'authors' : 'john doe',
        'n_pages' : '666',
        'n_ratings': 123,
        'avg_rating': 69.420,
        "language_code":"eng",
        "shelves":"s;s",
    }
    es.index(index = index,id=0, doc_type="book", body = testbody)

es.indices.refresh(index=index)

while True:
    #this search returns highest id in index
    highest_index = int(es.search(index=index, body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"])
    for i in range(highest_index+1,highest_index + 100):
        try:
            book = gc.book(i)
            print("indexing: " + book.title)
            form = book._book_dict["format"]
            if form != "Paperback" and form != "Hardcover" and form != "Mass Market Paperback":
                print("non okay format")
                print(form)
                raise Exception(":(")
            #checks if the book title is in the index already
            get = es.search(index=index, body={"query": {"match_phrase": {"title" : book.title.lower()}}})
            titles = [h["_source"]["title"] for h in get['hits']["hits"]]
            if get['hits']["total"]['value'] > 0 and book.title.lower() in titles :
                old_book = get["hits"]["hits"][titles.index(book.title.lower())]
                print("we got a double")
                print("number of matches in double")
                print(get['hits']["total"]['value'])
                #new one has more ratings AND is in the same language, write over old id
                if old_book["_source"]["n_ratings"] < book.ratings_count and old_book["_source"]["language_code"] == book.language_code:
                    book_body = {
                    'title': book.title.lower(),
                    'description': book.description, 
                    'id' : old_book["_id"] ,
                    'authors' : ", ".join([n.name for n in  book.authors]),
                    'n_pages' : book.num_pages,
                    'n_ratings' : book._book_dict["ratings_count"],
                    'avg_rating': book._book_dict["average_rating"],
                    'language_code':book.language_code,
                    'shelves':";".join([book._book_dict["popular_shelves"]["shelf"][i]["@name"] for i in range(len(book._book_dict["popular_shelves"]["shelf"]))])
                    }
                    es.index(index = index, id = old_book["_id"], doc_type = "book", body = book_body)
            else:
                book_body = {
                    'title': book.title.lower(),
                    'description': book.description, 
                    'id' : i ,
                    'authors' : ", ".join([n.name for n in  book.authors]),
                    'n_pages' : book.num_pages,
                    'n_ratings' : book._book_dict["ratings_count"],
                    'avg_rating': book._book_dict["average_rating"],'language_code':book.language_code,
                    'shelves':";".join([book._book_dict["popular_shelves"]["shelf"][i]["@name"] for i in range(len(book._book_dict["popular_shelves"]["shelf"]))])
                }
                es.index(index = index, id = i, doc_type = "book", body = book_body)
        except:
            print("book id " + str(i) +" no good")

    # ", ".join([n.name for n in  book.authors])
    # e = es.search(index="davis_wiki", body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"]

#if one now wants to serach for like all books written by J K Rowlin one can search like this 
#res = es.search(index="good_reads_test", body={"query": {"match": {"authors" :"J K Rowling" }}})
#res2 = es.search(index =" good_reads_test",body = "aggs" :{"field":"authors" })
#print("\n ".join([h['_source']['title'] for h in res['hits']['hits']]))
