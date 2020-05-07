# DD 2476 Search Engines & Information Retrieval
#
# TODO: ADD SOME MORE INFO HERE
#
#
import tkinter as tk



class BookRecommender:

    def __init__(self):
        self.window = tk.Tk()
        self.window.geometry("750x500")
        self.build_window()

        
    def build_window(self):
        #frame = tk.Frame(self.window, background="blue")
        tk.Label(self.window, text="DD 2476 - Book Recommender Engine").pack()
        leftside = tk.Frame(self.window, bd = 10, background="grey", width=500 )
        leftside.pack(side = tk.LEFT, fill = tk.Y)

        rightside = tk.Frame(self.window, background="black", width=250 )
        rightside.pack(side = tk.RIGHT, fill = tk.Y)

        e1 = tk.Entry(leftside, width = 80).pack()

        listbox = tk.Listbox(leftside, width = 80)
        listbox.pack(fill = tk.BOTH, pady= 5, expand=True)

        savebox = tk.Listbox(rightside, width=100)
        savebox.pack(fill = tk.BOTH, pady = 10, expand = True)




    def start_gui(self):
        self.window.mainloop()



if __name__ == '__main__':
    br = BookRecommender()
    br.start_gui()
