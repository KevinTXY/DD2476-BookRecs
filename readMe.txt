To run first set up an elastic search instance on your computer and run it
Download Goodreads python api 
Download elastic search python extension 
Download rake-nltk

Download  "punkt" and "stopwords" from http://www.nltk.org/nltk_data/ 
To find out where to put these run these commands in python and the error message will say where it looked, place the unzipped versions there 

To find where to put "stopwords"

>from rake_nltk import Rake
>r = Rake()

To find where to put "punkt"
>r.extract_keywords_from_text("asd asd asd")

Now run good_reads_elastic_test.py
It should start indexing, and it is searchable while indexing so if you want to you can search by opening up another python instance 
And run this to search for instance books that are written by j k rowling

>from elasticsearch import Elasticsearch
>es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
>res = es.search(index="good_reads_test", body={"query": {"match": {"authors" :"J K Rowling" }}})
>print("\n ".join([h['_source']['title'] for h in res['hits']['hits']]))

also try to run Searcher.py, it lets you first search for books and and then will look for similar books. 