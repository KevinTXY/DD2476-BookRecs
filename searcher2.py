
from elasticsearch import Elasticsearch
from goodreads import client
import numpy as np
import copy
from scipy.stats import norm
import os.path
from os import path
import re

class result:

    def __init__(self,book_list,n,id):
        #inits with the choosen books
        self.choosen_books1 = book_list[:n]
        self.choosen_books2 = book_list[n:]
        self.all_books = [h['_source']['title']+":"+h["_id"]  for h in book_list]
        self.raw_books = book_list
        self.results = {}
        self.id = id
    
    def add_result(self,result,name):
        self.results[name] = copy.deepcopy(result)
    
    def write(self,file_name):
        f = open(file_name+".txt", "w") 
        f.write("books used for choice \n")
        for b in self.choosen_books1:
            f.write(b["_source"]["title"] + " ("+b["_id"]+") \n")
        f.write("notes \n")
        f.write("type means which searchtype, type1 does multiple searches and then combines the scores type 2 combines first words in every description \n")
        f.write("index means which index, the one that says keywords is the one where every description is keyphrase extracted \n")
        f.write("alpha means how much of the original score is used so alpha = 0 gives all shelfvector similarity \n")
        f.write("information comes as: title, id,score, the extra || is if you want to open it in excel and split it by || might make it easier \n ")
        f.write("------results----- \n")
        for key in self.results.keys():
            f.write(str(key) +"\n")
            res = self.results[key]
            for book in res:
                f.write(book['_source']['title'] + "||("+book["_id"]+")| " + str(book["_score"])+" \n")
            f.write("\n")
    
    def calculate_acc(self,path):
        for key in self.results.keys():
            file_name,used = key.split(">")
            file_name = path+file_name
            TP = 1 if int(used) == 2 else 2 
            res = self.results[key]
            res_ids = [h['_id'] for h in res]
            if TP == 1:
                TP_ids = [h['_id'] for h in self.choosen_books1]
            else:
                TP_ids = [h['_id'] for h in self.choosen_books2]  

            tot_correct = len(list(set(res_ids) & set(TP_ids)))
            correct_20 = len(list(set(res_ids[:20]) & set(TP_ids)))
            R_stat = len(list(set(res_ids[:len(TP_ids)]) & set(TP_ids)))
            if os.path.exists(file_name+".txt"):
                result_string = str(self.id) +";" + str(len(self.raw_books)) + ";" + str(R_stat/len(TP_ids)) + ";" + str(correct_20/20)+";" + str(correct_20/len(TP_ids))+";"+ str(tot_correct) +";" + str(len(self.choosen_books1) if TP == 2 else len(self.choosen_books2)) + "\n"
                f = open(file_name+".txt","a")
                f.write(result_string)
                f.close()
            else:
                start_string = "id;length;R_stat;precission@20;recall@20;totalcorrect;querylength \n"
                result_string = str(self.id) +";" + str(len(self.raw_books)) + ";" + str(R_stat/len(TP_ids)) + ";" + str(correct_20/20)+";" + str(correct_20/len(TP_ids))+";"+ str(tot_correct) +";" + str(len(self.choosen_books1) if TP == 2 else len(self.choosen_books2)) + "\n"
                f = open(file_name+".txt","a")
                f.write(start_string)
                f.write(result_string)
                f.close()
            





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


    def __init__(self,index,search_type,rating_weight=1,pages_weight=1,shelf_weight=1,regular_weight = 1,alpha=0,idf = True):
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
        self.alpha = alpha
        self.reg = re.compile("\w+")


    
    def normalize(self,text):
        text = text.replace("and","")
        text = text.replace("/","")
        return "".join(self.reg.findall(text)).lower()

    #gets a choice_list, which is a lsit of ids
    def choose(self, choice_list,id,include_all = False,split = 1/2):
        book_list = list()
        for c in choice_list:
            res = self.es.search(index=self.index,body= {"query": {"match":{"_id":c}}})
            if res['hits']["total"]['value'] > 0:
                book_list.append(res["hits"]["hits"][0])
            #else:
                #print(c)
        #now has all books in returnlist
        if include_all:
            r = result(book_list,len(book_list),id=id)
        else:
            if split > 1:
                n_books = min([int(len(book_list)/2),split])
                r = result(book_list,n_books,id=id)
            else:
                r = result(book_list,int(len(book_list)*split),id=id)
            #test only 5 books or less if that is needed
            #n_books = min([int(len(book_list)/2),5])
            #r = result(book_list,n_books,id=id)
        return r        
    
    def search(self, result, save_plain = True,use_half = 1,n_books = 20):
        #adds all the old id:s, we don't want to recommend the same book again
        if use_half == 1:
            books = result.choosen_books1
        else:
            books = result.choosen_books2
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
                if sum(book_vec >0):
                    book_vec = book_vec / np.linalg.norm(book_vec)
                #add it to total search vec
                search_vec += book_vec
                #if decription is not None
                if(book["_source"]["description"] != None):
                    #gets the 100 best matching books from the books description
                    res = self.es.search(index=self.index, body={"query": {"match": {"description" :book["_source"]["description"]} },"size":"100"})
                    #for every resulting book
                    tot_book_score = 0
                    for res_book in res['hits']['hits']:
                        new_title = self.normalize(res_book["_source"]["title"]) 
                        #if it already is in dictionary
                        if res_book["_id"] in id_to_score.keys() and res_book["_id"] not in ids and new_title not in old_titles:
                            tot_book_score += np.log(res_book["_score"])
                            id_to_book[res_book["_id"]]["_score"] += np.log(res_book["_score"])
                            #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                            id_to_score[res_book["_id"]] += np.log(res_book["_score"])
                        #if not in the dictionary and not a previos book
                        elif res_book["_id"] not in ids and new_title not in old_titles:
                            tot_book_score += np.log(res_book["_score"])
                            #print("score for book " + res_book["_source"]["title"] + ": "+str(res_book["_score"]))
                            id_to_book[res_book["_id"]] = res_book
                            id_to_book[res_book["_id"]]["_score"] = np.log(res_book["_score"])
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
                if sum(book_vec >0):
                    book_vec = book_vec / np.linalg.norm(book_vec)
                #add it to total search vec
                search_vec += book_vec
            #searches with the new long query
            res = self.es.search(index=self.index, body={"query": {"match": {"description" :query} },"size":"500"})

            for res_book in res['hits']['hits']:
                #checks so that its not in the selected books
                new_title = self.normalize(res_book["_source"]["title"]) 
                if res_book["_id"] not in ids and new_title not in old_titles:
                    id_to_book[res_book["_id"]] = res_book
                    id_to_score[res_book["_id"]] = res_book["_score"]
            


        
        recommendation_list = list()

        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        for book_id in sorted_scores.keys():
            book = id_to_book[book_id]
            book["_score"] = sorted_scores[book_id]
            recommendation_list.append(book)
        if save_plain:
            result.add_result(recommendation_list[:n_books],name= "index:"+str(self.index)+" type:"+str(self.type)+" alpha:"+str(1)+">"+str(use_half))

        #normalizes scores so they range from 0 to 1


        
        #print("book recommendations, plain, just tf_idf, id of book in parantheses")
        #print("\n ".join([h['_source']['title'] + "("+h["_id"]+") " + str(id_to_score[h["_id"]]) for h in recommendation_list][0:10]))
        
        
       

        #do tricks with scores

        #assumption, if you read books with low number of ratings you might like abscure books
        n_ratings = np.array([int(book["_source"]["n_ratings"]) for book in books])
        avg_ratings = np.average(n_ratings)
        stdev_ratings = np.std(n_ratings)
        #so it doesnt crash if stdev == 0
        stdev_ratings = avg_ratings/2 if stdev_ratings == 0 else stdev_ratings

        #if you read books of a certain length, then we will give you more of those
        n_pages = np.array([int(book["_source"]["n_pages"]) for book in books])
        avg_pages = np.average(n_pages)
        stdev_pages = np.std(n_pages)
        #so it doesnt crash if stdev == 0
        stdev_pages = avg_pages/2 if stdev_pages == 0 else stdev_pages
        #makes changes to scores
        #print("___________ratings and pages info __________")
        #print(avg_ratings)
        #print(stdev_rating)
        #print(avg_pages)
        #print(stdev_pages)
        #print("_______________")
        scores = []
        for key in id_to_score:
            ratings = int(id_to_book[key]["_source"]["n_ratings"])
            pages = int(id_to_book[key]["_source"]["n_ratings"])

            id_to_score[key] = id_to_score[key] #* norm.pdf(ratings,avg_ratings,stdev_ratings) * norm.pdf(pages,avg_pages,stdev_pages)
            scores.append(id_to_score[key])
        

        max_score = max(scores)
        for key in id_to_score.keys():
            id_to_score[key] /= max_score

        for book_id in id_to_score.keys():
            book = id_to_book[book_id]
            book_vec = np.zeros(len(self.shelf_to_score))
            for s in book["_source"]["shelves"].split(";"):
                name,count = s.split(":")
                if name in self.shelf_to_pos:
                    book_vec[self.shelf_to_pos[name]] = int(count) * self.shelf_to_score[name]
            if np.sum(book_vec) > 0 :
                shelf_sim = np.dot(book_vec,search_vec) / (np.linalg.norm(book_vec) * np.linalg.norm(search_vec))
            else:
                shelf_sim = 0
            id_to_score[book_id] = id_to_score[book_id]*self.alpha + (1-self.alpha)*shelf_sim
            #id_to_score[book_id] *= (1 + norm.pdf(n_ratings,avg_ratings,stdev_ratings)*self.rating_weight + norm.pdf(n_pages,avg_pages,stdev_pages)*self.pages_weight +self.shelf_weight*shelf_sim) 




        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        recommendation_list = []
        for book_id in sorted_scores.keys():
            id_to_book[book_id]["_score"] = sorted_scores[book_id]
            recommendation_list.append(id_to_book[book_id])
        
        

        result.add_result(recommendation_list[:n_books],name= "index:"+str(self.index)+" type:"+str(self.type)+" alpha:"+str(self.alpha)+">"+str(use_half))
        return(result)

    def baseline_tester(self, result, save_plain = True,use_half = 1,n_books = 20):
        id_to_score = {}
        id_to_book = {}
        top = self.es.search(index=self.index,body= {"query": {"match_all":{}},"size":"5000"},sort = "n_ratings:desc")
        for res in top["hits"]["hits"]:
            id_to_score[res["_id"]] = float(res["_source"]["avg_rating"])
            id_to_book[res["_id"]] = res
        sorted_scores = {k: v for k, v in sorted(id_to_score.items(), key=lambda item: item[1],reverse = True)}
        recommendation_list = []
        for book_id in sorted_scores.keys():
            recommendation_list.append(id_to_book[book_id])
        result.add_result(recommendation_list[:n_books],name="baseline"+">"+str(use_half))
        return(result)

                
def main():
    pass

def tester(baseline = False,split = 1/2):
    s1 = searcher("good_reads_keywords",  1, alpha = 0.5 )
    s2 = searcher("good_reads_keywords",  2, alpha = 0.5 )
    s3 = searcher("good_reads",  1, alpha = 0.5 )
    s4 = searcher("good_reads",  2, alpha = 0.5 )
    s5 = searcher("good_reads",  1, alpha = 0)

    f = open("grscraper/users.txt","r")
    lines = f.readlines()
    searchresults = []
    choices = []
    id_counter = 0
    for line in lines:
        line = line.strip("\n")
        if line != "":
            choices.append(line)
        else:
            res = s1.choose(choices,include_all=False,id = id_counter,split = split)
            id_counter +=1
            if len(res.raw_books) > 100:
                for i in [1,2]:
                    n_books = min([len(res.raw_books),200])
                    if baseline:
                        b_res = s1.baseline_tester(res,use_half=i,n_books=n_books)
                    res = s1.search(res,use_half=i,n_books=n_books)
                    res = s2.search(res,use_half=i,n_books=n_books)
                    res = s3.search(res,use_half=i,n_books=n_books)
                    res = s4.search(res,use_half=i,n_books=n_books)
                    res = s5.search(res,save_plain=False,use_half=i,n_books=n_books)
                    if(id_counter == 3 and i ==1):
                        res.write("asdasd")
                        print("\n".join( [h["_source"]["title"] for h in res.raw_books]))
                res.calculate_acc("plain/")

            choices = []
    #print(len(searchresults))
    #for res in searchresults:
        #print(len(res.all_books))
        #print(len(res.chosen_books))
        #print("----------")
        #res = s1.search(res)
        #res = s2.search(res)
        #res = s3.search(res)
        #res = s4.search(res)
        #res = s5.search(res,save_plain=False)
    #for i in range(len(searchresults)):
    #    searchresults[i].write("qualitative_search_res_safecheck"+str(i))
    
if __name__ == "__main__":
    tester()
    tester(split = 5)
