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


### Web Scraper ###
A web scraper was included that crawls looking for users with many books read and records their favorite book id's in order sorted by rank. To run this script, the following needs to be done:
* Install Selenium, the line below should do this
  > pip install selenium
* Download the webdriver from a browser you'd like to use, these are small ~4mb files. The link for the chrome driver is https://chromedriver.chromium.org/downloads
* Edit line 14 to instantiate the correct browser driver. If not using chromium edge, replace "Edge" with "Chrome" or "Firefox", and then replace 'msedgedriver.exe' with a path to the web driver file you instantiated above.
* The code should now run. If needed, change the parameters such as userid, minbooks, usersleft.
