
from elasticsearch import Elasticsearch
from goodreads import client
import numpy as np
from scipy.stats import norm


class searcher:
    
    def __init__(self,index):
        #sets up good reads client and elastic search,
        #should not really need goodreads client 
        self.gc = client.GoodreadsClient("NGr7Zl6XG9nTeNClLz9xA", "WILsiGKkWTEoKh4M7z11TF0P2ukSRcJ2OEFJMngDgY")
        self.es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        self.index = index
    
    def dummy(self):
        res = self.es.search(index="good_reads_test", body={"query": {"match": {"authors" :"J K Rowling" }}})
        #res2 = es.search(index =" good_reads_test",body = "aggs" :{"field":"authors" })
        print("\n ".join([h['_source']['title'] for h in res['hits']['hits']]))

    #function to choose books to search through
    def choose(self,test):
        if(not test):
            search_term = input("search for a title, to exit write done()")
        else:
            search_term = "harry potter"
        choice_list = list()
        while search_term != "done()":
            res = self.es.search(index=self.index, body={"query": {"match": {"title" :search_term } },"size":"15"})
            #if any hits
            if res['hits']["total"]['value'] > 0:
                
                hits = [h['_source']['title'] for h in res['hits']['hits']]
                languages =  [h['_source']["language_code"] for h in res['hits']['hits']]
                languages = ["NA" if l == None else l for l in languages]
                ids = [h["_id"] for h in res["hits"]["hits"]]
                for i in range(len(hits)):
                    print(str(i) + " " + str(hits[i]) + " " +ids[i] + " " + languages[i])
                
                if(not test):
                    choice = input("choose book(s) you have read by number, seperate by ,")
                else:
                    choice = "5,6,7,8"
                try:
                    #makes the choice vector to a vector of integers
                    choice = choice.split(",")
                    
                    choice = [int(c) for c in choice if c != ""]
                    
                    #puts all the choices into the list
                    for i in choice:
                        choice_list.append(res["hits"]["hits"][i])
                    if(not test):    
                        search_term = input("search for a title, to exit write done() ")
                    else:
                        search_term = "done()"
                except:
                    print("error in input")
                    search_term = input("search for a title, to exit write done() ")
                
                
            else:
                print("got no hits :(")
                search_term = input("search for a title, to exit write done() ")
        ids = list()
        return_list = list()
        #cleans out so no double ids
        for book in choice_list :

            if book["_id"] not in ids:
                ids.append(book["_id"])
                return_list.append(book)
            
        
        print("choosen books are the following")
        print("\n ".join([h['_source']['title'] + "("+h["_id"]+")"  for h in return_list]))
        return return_list
    
    def search(self, books):
        #adds all the old id:s, we don't want to recommend the same book again
        ids = [b["_id"] for b in books]
        id_to_book = {}
        id_to_score = {}
        for book in books:
            
            #if decription is not None
            if(book["_source"]["description"] != None):
                #gets the 100 best matching books from the books description
                res = self.es.search(index=self.index, body={"query": {"match": {"description" :book["_source"]["description"]} },"size":"100"})
                #for every resulting book
                tot_book_score = 0
                for res_book in res['hits']['hits']:
                    
                    #if it already is in dictionary
                    if res_book["_id"] in id_to_score.keys() and res_book["_id"] not in ids:
                        tot_book_score += np.log(res_book["_score"])
                        #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                        id_to_score[res_book["_id"]] += np.log(res_book["_score"])
                    #if not in the dictionary and not a previos book
                    elif res_book["_id"] not in ids:
                        tot_book_score += np.log(res_book["_score"])
                        #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                        id_to_book[res_book["_id"]] = res_book
                        id_to_score[res_book["_id"]] = np.log(res_book["_score"])
                print("total score for all book given from book: " + book["_source"]["title"] + " : "+ str(tot_book_score))
                    

        
        recommendation_list = list()

        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        for book_id in sorted_scores.keys():
            recommendation_list.append(id_to_book[book_id])

        print("book recommendations, id of book in parantheses")
        print("\n ".join([h['_source']['title'] + "("+h["_id"]+")"for h in recommendation_list][0:10]))


        #do tricks with scores

        #assumption, if you read books with low number of ratings you might like abscure books
        n_ratings = np.array([int(book["_source"]["n_ratings"]) for book in books])
        avg_ratings = np.average(n_ratings)
        stdev_ratings = np.std(n_ratings)
        #so it doesnt crash if stdev == 0
        stdev_rating = avg_ratings/2 if stdev_ratings == 0 else stdev_ratings

        #remove books with no n_pages
        books = [book for book in books if book["_source"]["n_pages"] != None]

        #if you read books of a certain length, then we will give you more of those
        n_pages = np.array([int(book["_source"]["n_pages"]) for book in books])
        avg_pages = np.average(n_pages)
        stdev_pages = np.std(n_pages)
        #so it doesnt crash if stdev == 0
        stdev_pages = avg_pages/2 if stdev_pages == 0 else stdev_pages
        #makes changes to scores
        print("___________ratings and pages info __________")
        print(avg_ratings)
        print(stdev_rating)
        print(avg_pages)
        print(stdev_pages)
        print("_______________")
        for book_id in id_to_score.keys():
            book = id_to_book[book_id]
            n_ratings= int(book["_source"]["n_ratings"])
            #print(book)
            #for now, no pages, it is a collection, should be handeled when indexing instead probably
            if book["_source"]["n_pages"] == None:
                id_to_score[book_id] = 0
            else:
                n_pages = int(book["_source"]["n_pages"])
                id_to_score[book_id] = id_to_score[book_id]
                id_to_score[book_id] *= (1 + norm.pdf(n_ratings,avg_ratings,stdev_ratings) + norm.pdf(n_pages,avg_pages,stdev_pages)) 





        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        for book_id in sorted_scores.keys():
            recommendation_list.append(id_to_book[book_id])
        
        
        #uncomment below to see how pages and ratings impact

        #for book in recommendation_list[0:10]:
            #n_ratings = int(book["_source"]["n_ratings"])
            #n_pages = int(book["_source"]["n_pages"])
            #print(book["_source"]["title"])
            #print(norm.pdf(n_ratings,avg_ratings,stdev_ratings))
            #print(norm.pdf(n_pages,avg_pages,stdev_pages))

        print("book recommendations, id of book in parantheses")
        print("\n ".join([h['_source']['title'] + "("+h["_id"]+")"for h in recommendation_list][0:10]))



                
def main():
    s = searcher("good_reads")
    read_books = s.choose(test = False)
    s.search(read_books)


if __name__ == "__main__":
    main()
