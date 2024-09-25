

import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk

from tkinter import filedialog
import os

from global_functions import run_model

import win_array as WA

class summary_thumbnails:
    def __init__(self, parent, sample_id, filename, row_num):
        self.parent = parent
        self.sample_id = sample_id
        self.filename = filename
        
        self.row_num = row_num
        
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid(row = row_num, column = 0, padx = 5, pady =5, sticky = tk.EW)
        
        self.frame.columnconfigure(0, minsize = 100)
        self.frame.columnconfigure(1, minsize = 200)
        self.frame.columnconfigure(2, minsize = 200)
        
        self.MAX_sizE = (100,100)       
        self.img = Image.open(self.filename)
        self.img.thumbnail(self.MAX_sizE)
        self.img = ImageTk.PhotoImage(self.img)
        
        self.thumbnail = tk.Label(self.frame, image = self.img)
        self.thumbnail.image = self.img
        
        # Position image
        
        self.label = ctk.CTkLabel(self.frame, text =self.sample_id)
        self.label.grid(row=0, column = 1, padx = 5)
        self.thumbnail.grid(row = 0, column = 0 , padx = 5)
        
        # self.axis_btn = ctk.CTkButton(self.frame, text = "Load growth axis", command = self.load_axis)
        # self.axis_btn.grid(row = 0, column = 2, padx = 5)

        
    def print_res(self):
        pass
        #print("Series:" + str(self.row_num) + "lenght = " + str(len(WS.DT[self.row_num].object_list)))
        
    def closed_win(self):
        print("this window has closed")
        
    def load_axis(self):
        self.axis_filename = filedialog.askopenfilename(initialdir = os.getcwd() + "/images",
                                            title = "Select a File")
        
        self.axis_img = Image.open(self.axis_filename)
        self.axis_img.thumbnail(self.MAX_sizE)
        self.axis_img = ImageTk.PhotoImage(self.axis_img)
        
        self.axis_thumbnail = tk.Label(self.frame, image = self.axis_img)
        self.axis_thumbnail.image = self.axis_img
        
        self.axis_btn.grid_forget()
        self.axis_btn.grid(row = 0, column = 3, padx = 5)
        
        self.axis_thumbnail.grid(row = 0, column = 2 , padx = 5)
        
        self.AI_data = run_model(self.filename, self.axis_filename, "glycymeris")
        
        WA.wins[self.row_num-1].canvas.show_AI_data(self.AI_data)