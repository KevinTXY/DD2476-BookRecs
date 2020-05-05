from elasticsearch import Elasticsearch
from goodreads import client
from rake_nltk import Rake

index = "good_reads"
index2 = "good_reads_keywords"
gc = client.GoodreadsClient("NGr7Zl6XG9nTeNClLz9xA", "WILsiGKkWTEoKh4M7z11TF0P2ukSRcJ2OEFJMngDgY")
r = Rake()
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
    es.indices.create(index=index2, ignore=400, body=settings)

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
    es.index(index = index2,id=0, doc_type="book", body = testbody) 
es.indices.refresh(index=index)
es.indices.refresh(index=index2)
highest_index = int(es.search(index=index, body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"])
i = highest_index
while True:
    #this search returns highest id in index
    #will only search for one index, as both indexes updates at the same time
    fields = ["id", "title", "authors", "num_pages","ratings_count","average_rating","language_code"]
    i+=1
    #refresh index first 
    es.indices.refresh(index=index)
    es.indices.refresh(index=index2)
    
    try:
        book = gc.book(i)
        print("indexing: " + book.title)
        form = book._book_dict["format"]
        #checks if it has values on every field we want 
        [book._book_dict[f] for f in fields]
        checker = sum([0 if i != None else 1 for i in  [book._book_dict[f] for f in fields]])
        if checker > 0:
            print("book had empty fields")
            raise Exception(":(")
        #checks so that is is not audio or something like that
        if form != "Paperback" and form != "Hardcover" and form != "Mass Market Paperback" :
            print("non okay format")
            print(form)
            raise Exception(":(")
        #checks so that it is under 1500 pages
        if int(book.num_pages) > 1500:
            print("book was too long")
            raise Exception(":(")
        #checks so that it is in english
        if book.language_code != "eng":
            print("book was non english")
            raise Exception(":(")
        #checks if the book title is in the index already
        get = es.search(index=index, body={"query": {"match_phrase": {"title" : book.title.lower()}}})
        titles = [h["_source"]["title"] for h in get['hits']["hits"]]
        if get['hits']["total"]['value'] > 0 and book.title.lower() in titles :
            old_book = get["hits"]["hits"][titles.index(book.title.lower())]
            
            print("we got a double")
            print("number of matches in double")
            print(get['hits']["total"]['value'])
            #new one has more ratings AND is in the same language and also same authors, IE same book, write over old book
            if old_book["_source"]["n_ratings"] < book.ratings_count and old_book["_source"]["language_code"] == book.language_code and old_book["_source"]["authors"] == book.authors :
                book_body = {
                'title': book.title.lower(),
                'description': book.description.replace("<br />" , ""), 
                'id' : old_book["_id"] ,
                'authors' : ", ".join([n.name for n in  book.authors]),
                'n_pages' : book.num_pages,
                'n_ratings' : book._book_dict["ratings_count"],
                'avg_rating': book._book_dict["average_rating"],
                'language_code':book.language_code,
                'shelves':";".join([book._book_dict["popular_shelves"]["shelf"][i]["@name"]+":"+book._book_dict["popular_shelves"]["shelf"][i]["@count"] for i in range(len(book._book_dict["popular_shelves"]["shelf"]))])
                }
                
                es.index(index = index, id = old_book["_id"], doc_type = "book", body = book_body)
                #update book_body so that description only contains keywords
                r.extract_keywords_from_text(book_body["description"])
                book_body["description"] = " ".join(r.get_ranked_phrases())
                es.index(index = index2, id = old_book["_id"], doc_type = "book", body = book_body)
        else:
            book_body = {
                'title': book.title.lower(),
                'description': book.description.replace("<br />" , ""), 
                'id' : i ,
                'authors' : ", ".join([n.name for n in  book.authors]),
                'n_pages' : book.num_pages,
                'n_ratings' : book._book_dict["ratings_count"],
                'avg_rating': book._book_dict["average_rating"],'language_code':book.language_code,
                'shelves':";".join([book._book_dict["popular_shelves"]["shelf"][i]["@name"]+":"+book._book_dict["popular_shelves"]["shelf"][i]["@count"] for i in range(len(book._book_dict["popular_shelves"]["shelf"]))])
            }
            es.index(index = index, id = i, doc_type = "book", body = book_body)
            #update book_body so that description only contains keywords
            r.extract_keywords_from_text(book_body["description"])
            book_body["description"] = " ".join(r.get_ranked_phrases())
            es.index(index = index2, id = i, doc_type = "book", body = book_body)
    except:
        print("book id " + str(i) +" no good")

    # ", ".join([n.name for n in  book.authors])
    # e = es.search(index="davis_wiki", body={"aggs": {"max_id": {"max" : {"field" : "id" }}},"size":"1"})["aggregations"]["max_id"]["value"]

#if one now wants to serach for like all books written by J K Rowlin one can search like this 
#res = es.search(index="good_reads_test", body={"query": {"match": {"authors" :"J K Rowling" }}})
#res2 = es.search(index =" good_reads_test",body = "aggs" :{"field":"authors" })
#print("\n ".join([h['_source']['title'] for h in res['hits']['hits']]))
