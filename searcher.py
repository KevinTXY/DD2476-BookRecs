
from elasticsearch import Elasticsearch
from goodreads import client
import numpy as np
from scipy.stats import norm
import time
import re


class searcher:
    
    def read_shelf_file(self,idf):
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
            if idf:
                shelf_to_score[ lines[i].split(":")[1].strip("\n")[1:] ] = float(lines[i].split(":")[0])
            else:
                shelf_to_score[ lines[i].split(":")[1].strip("\n")[1:] ] = 1
        return(shelf_to_pos,shelf_to_score)


    def __init__(self,index,search_type,rating_weight=1,pages_weight=1,shelf_weight=1,regular_weight = 1,idf = True):
        #sets up good reads client and elastic search,
        #should not really need goodreads client 
        self.gc = client.GoodreadsClient("NGr7Zl6XG9nTeNClLz9xA", "WILsiGKkWTEoKh4M7z11TF0P2ukSRcJ2OEFJMngDgY")
        self.es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        self.index = index
        self.type = search_type
        self.shelf_to_pos,self.shelf_to_score = self.read_shelf_file(idf)
        self.rating_weight = rating_weight
        self.pages_weight = pages_weight
        self.regular_weight = regular_weight
        self.shelf_weight = shelf_weight
        self.reg = re.compile("\w+")
    
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
                authors = [h['_source']['authors'] for h in res['hits']['hits']]
                ids = [h["_id"] for h in res["hits"]["hits"]]
                for i in range(len(hits)):
                    print(str(i) + " " + str(hits[i]) + " " +ids[i] + " " + languages[i] + " " + authors[i])
                
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
    
    def normalize(self,text):
        text = text.replace("and","")
        text = text.replace("/","")
        return "".join(self.reg.findall(text)).lower()
    

    def search(self, books,alpha):
        starttime = time.time()
        #adds all the old id:s, we don't want to recommend the same book again
        ids = [b["_id"] for b in books]
        id_to_book = {}
        id_to_score = {}
        old_titles = [self.normalize(b["_source"]["title"]) for b in books]
        #init search_vec to be all zeros
        #search_vec is the vector that uses shelves to search
        search_vec = np.zeros(len(self.shelf_to_score))
        # type 1 does multiple queries and sums scores
        if self.type == 1:
            for book in books:
                #creates shelves vec
                book_vec = np.zeros(len(self.shelf_to_score))
                for s in book["_source"]["shelves"].split(";"):
                    name,count = s.split(":")
                    if name in self.shelf_to_pos:
                        book_vec[self.shelf_to_pos[name]] = int(count) * self.shelf_to_score[name]
                #divide by euclidian length of vec
                book_vec = book_vec / np.linalg.norm(book_vec)
                #add it to total search vec
                search_vec += book_vec
                #if decription is not None
                if(book["_source"]["description"] != None):
                    #gets the 100 best matching books from the books description
                    res = self.es.search(index=self.index, body={"query": {"match": {"description" :book["_source"]["description"]} },"size":"300"})
                    #for every resulting book
                    tot_book_score = 0
                    for res_book in res['hits']['hits']:
                        new_title = self.normalize(res_book["_source"]["title"])
                        #if it already is in dictionary
                        if res_book["_id"] in id_to_score.keys() and res_book["_id"] not in ids and new_title not in old_titles:
                            tot_book_score += np.log(res_book["_score"])
                            #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                            id_to_score[res_book["_id"]] += np.log(res_book["_score"])
                        #if not in the dictionary and not a previos book
                        elif res_book["_id"] not in ids and new_title not in old_titles:
                            tot_book_score += np.log(res_book["_score"])
                            #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                            id_to_book[res_book["_id"]] = res_book
                            id_to_score[res_book["_id"]] = np.log(res_book["_score"])
                    #print("total score for all book given from book: " + book["_source"]["title"] + " : "+ str(tot_book_score))
        #type 2 combines the first words n words of each description 
        #where n is limited so that the query is under 1024 words 
        if self.type == 2:
            query = ""
            n_words = int(np.floor(1024/len(books)))
            #makes one long query

            # TODO: here one could update so that is makes some kind of sofisticated version of grabbing the words, like idf in the index
            for book in books:
                query += " "+ " ".join(book["_source"]["description"].split(" ")[:n_words])
                book_vec = np.zeros(len(self.shelf_to_score))
                for s in book["_source"]["shelves"].split(";"):
                    name,count = s.split(":")
                    if name in self.shelf_to_pos:
                        book_vec[self.shelf_to_pos[name]] = int(count) * self.shelf_to_score[name]
                #divide by euclidian length of vec
                book_vec = book_vec / np.linalg.norm(book_vec)
                #add it to total search vec
                search_vec += book_vec
            #searches with the new long query
            res = self.es.search(index=self.index, body={"query": {"match": {"description" :query} },"size":"1500"})

            for res_book in res['hits']['hits']:
                #checks so that its not in the selected books
                new_title = self.normalize(res_book["_source"]["title"])
                if res_book["_id"] not in ids and new_title not in old_titles:
                    id_to_book[res_book["_id"]] = res_book
                    id_to_score[res_book["_id"]] = res_book["_score"]
            


        
        recommendation_list = list()

        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        for book_id in sorted_scores.keys():
            recommendation_list.append(id_to_book[book_id])
        print("_____________Recommendations_______________________________________")
        print("book recommendations, plain, just tf_idf, id of book in parantheses")
        
        print("\n ".join([h['_source']['title'] + "("+h["_id"]+") " + str(id_to_score[h["_id"]]) for h in recommendation_list][0:10]))
        max_score = sorted_scores[list(sorted_scores.keys())[0]]
        for key in id_to_score.keys():
            id_to_score[key] /= max_score

        #do tricks with scores

        #assumption, if you read books with low number of ratings you might like abscure books
        #n_ratings = np.array([int(book["_source"]["n_ratings"]) for book in books])
        #avg_ratings = np.log(np.average(n_ratings))
        #stdev_ratings = np.log(np.std(n_ratings))
        #so it doesnt crash if stdev == 0
        #stdev_rating = avg_ratings/2 if stdev_ratings == 0 else stdev_ratings

        #if you read books of a certain length, then we will give you more of those
        #n_pages = np.array([int(book["_source"]["n_pages"]) for book in books])
        #avg_pages = np.log(np.average(n_pages))
        #stdev_pages = np.log(np.std(n_pages))
        #so it doesnt crash if stdev == 0
        #stdev_pages = avg_pages/2 if stdev_pages == 0 else stdev_pages
        #makes changes to scores
        #print("___________ratings and pages info __________")
        #print(avg_ratings)
        #print(stdev_rating)
        #print(avg_pages)
        #print(stdev_pages)
        #print("_______________")
        for book_id in id_to_score.keys():
            book = id_to_book[book_id]
            #n_ratings= np.log(float(book["_source"]["n_ratings"]))
            #n_pages = np.log(float(book["_source"]["n_pages"]))
            book_vec = np.zeros(len(self.shelf_to_score))
            for s in book["_source"]["shelves"].split(";"):
                name,count = s.split(":")
                if name in self.shelf_to_pos:
                    book_vec[self.shelf_to_pos[name]] = int(count) * self.shelf_to_score[name]
            #print(np.linalg.norm(search_vec))
            #print(np.linalg.norm(book_vec))
            #print(book)
            if np.sum(book_vec) > 0 :
                shelf_sim = np.dot(book_vec,search_vec) / (np.linalg.norm(book_vec) * np.linalg.norm(search_vec))
            else:
                #print(book)
                shelf_sim = 0
            #id_to_score[book_id] = shelf_sim
            #print(avg_pages)
            #print(n_pages)
            #print(stdev_pages)
            #id_to_score[book_id] *= (1 + self.shelf_weight*shelf_sim + norm.pdf(n_pages,avg_pages,stdev_pages)*self.pages_weight )
            #id_to_score[book_id] *= (1 + norm.pdf(n_ratings,avg_ratings,stdev_ratings)*self.rating_weight + norm.pdf(n_pages,avg_pages,stdev_pages)*self.pages_weight +self.shelf_weight*shelf_sim) 
            id_to_score[book_id] = id_to_score[book_id]*alpha + (1-alpha)*shelf_sim




        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        recommendation_list = []
        for book_id in sorted_scores.keys():
            recommendation_list.append(id_to_book[book_id])
        
        
        #uncomment below to see how pages and ratings impact

        #for book in recommendation_list[0:10]:
            #n_ratings = int(book["_source"]["n_ratings"])
            #n_pages = int(book["_source"]["n_pages"])
            #print(book["_source"]["title"])
            #print(norm.pdf(n_ratings,avg_ratings,stdev_ratings))
            #print(norm.pdf(n_pages,avg_pages,stdev_pages))
        print("_____________________now with added genre similarity_________________")
        print("book recommendations, id of book in parantheses")
        print("\n ".join([h['_source']['title'] + "("+h["_id"]+") " + str(id_to_score[h["_id"]]) for h in recommendation_list][0:10]))
        endtime = time.time() - starttime
        print("_____________info______________ ")
        print("Time for finding recommendations: " + str(endtime) + "seconds")
        print("Number of books ordered: " + str(len(sorted_scores)))


                
def main():
    np.seterr('raise')
    s = searcher("good_reads_keywords",  2)
    read_books = s.choose(test = False)
    if len(read_books) == 0:
        print("need to choose books")
        return()
    s.search(read_books,alpha = 0.5)


if __name__ == "__main__":
    main()
