# DD 2476 Search Engines & Information Retrieval
#
# TODO: ADD SOME MORE INFO HERE
#
#
import tkinter as tk

# Holds 

class Book:
    def __init__(self, bookid, title, author = None):
        self.id = bookid
        self.title = title
        self.author = author


class BookRecommender:

    def __init__(self):
        # Meant to hold contents inside search box and save box. Currently holds placeholders
        self.searchlist = [ Book( i, ("Book " + str(i) ) ) for i in range(100)]
        self.savedlist = []

        # Building windows and running 
        self.window = tk.Tk()
        self.window.geometry("750x500")
        self.build_window()

        
    # Builds main window and all necessary components. Need to run this at startup
    def build_window(self):
        #frame = tk.Frame(self.window, background="blue")
        tk.Label(self.window, text="DD 2476 - Book Recommender Engine").pack()
        leftside = tk.Frame(self.window, bd = 10, background="grey", width=500 )
        leftside.pack(side = tk.LEFT, fill = tk.Y)

        rightside = tk.Frame(self.window, background="grey", width=250 )
        rightside.pack(side = tk.RIGHT, fill = tk.Y)

        tk.Entry(leftside, width = 80).pack()
        but = tk.Button(leftside, command=self.search_clicked, bd=0, relief="groove", compound=tk.CENTER,bg="brown", fg="black", activeforeground="white", activebackground="red", font="arial 10", text="Search")
        but.pack(pady=3)
        searchbox = tk.Listbox(leftside, selectmode=tk.SINGLE, width = 80)
        searchbox.pack(fill = tk.BOTH, pady= 2, expand=True)
        searchbox.bind('<Double-1>', self.save_item)

        savebox = tk.Listbox(rightside, width=100)
        savebox.pack(fill = tk.BOTH, pady = 10, expand = True)
        savebox.bind('<Double-1>', self.remove_item)

        #tk.Button(leftside, text = "Save Selections").pack(side=tk.BOTTOM)

        self.searchbox = searchbox
        self.savebox = savebox

    ### API for filling or removing items from searchbox ##
    # Proc'd when the "Search" button is clicked
    def search_clicked(self):
        self.populate_searchbox(self.searchlist)


    # Clears search box and fills it with items in list of books
    def populate_searchbox(self, results):
        self.clear_searchbox()
        for i, book in enumerate(results):
            self.searchbox.insert( tk.END, str(book.id) + " : " + book.title )

    # Adds book to search box
    def append_to_searchbox(self, result):
        self.searchbox.insert(tk.END, result.title)

    # Clears Search box and searchlist
    def clear_searchbox(self):
        self.searchlist = []
        self.searchbox.delete(0,tk.END)

    # Saves item as book w/ id to savelist and adds it to savebox. Could be more efficient. 
    def save_item(self, event):
        box = event.widget
        selection = box.get(box.curselection())
        split = selection.index(":")
        bk = Book(int(selection[:split - 1]), selection[split + 2:])

        for book in self.savedlist:
            if book.id == bk.id:
                return

        self.savedlist.append(bk)
        self.savebox.insert(tk.END, str(bk.id) + " : " + bk.title)

    # Remove from savedlist. Could make this more efficient w/ dicts but probably not necessary rn
    def remove_item(self, event):
        box = event.widget
        selection = box.curselection() 

        # Remove from saveList
        bk = box.get(selection)
        split = bk.index(":")
        bkid = int(bk[:split - 1])

        for book in self.savedlist:
            if book.id == bkid:
                self.savedlist.remove(book)
                box.delete(selection[0])
                print("removed")
                return

    ## Starts program
    def start_gui(self):
        self.window.mainloop()



if __name__ == '__main__':
    br = BookRecommender()
    br.start_gui()
