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
        leftside = tk.Frame(self.window, bd = 10, background="grey", width=750/3 ).pack(side = tk.LEFT, fill = tk.Y)
        tk.Label(leftside, text="searawf").pack()
        rightside = tk.Frame(self.window, background="blue", width=750/3 ).pack(side = tk.RIGHT, fill = tk.Y)



    def start_gui(self):
        self.window.mainloop()



if __name__ == '__main__':
    br = BookRecommender()
    br.start_gui()
