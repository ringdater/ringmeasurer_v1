# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 11:07:01 2023

@author: david
"""

#import global_variables as ST
from CVI import CanvasImage

#import tkinter as tk
import customtkinter
#from tkinter import filedialog
import os
import platform
import tkinter as tk
import customtkinter as ctk

from menubar import MenuBar

#import master_array as WS

class img_win():
    def __init__(self, parent, filename,  win_num, sample_id):
        self.window = tk.Toplevel(parent)
        self.win_num = int(win_num) 
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.system = platform.system() 
        if self.system == "Ddrwin":
            self.window.iconbitmap("assets/title_icon.icns")
        else:
            self.window.iconbitmap("assets/title_icon.ico")
        self.window.title(str(sample_id))
        self.window.geometry('800x600')
        # size of the main window
        self.window.rowconfigure(0, weight=1)  # make the CanvasImage widget expandable
        self.window.columnconfigure(0, weight=1)
        
        self.window.focus_force()
        self.window.lift()
        
        self.menu = MenuBar(self.window, self.win_num)
        
        self.classframe = tk.Frame(self.window)
        self.classframe.grid(row = 0, column = 0, pady = 0, sticky = "NSEW")
        
        self.classframe.rowconfigure(0, weight = 1)       
        
        self.title_label = ctk.CTkLabel(self.classframe, text = str("this is window") + str(self.win_num))
        self.title_label.grid(row = 0, column = 0, sticky = "NW", pady = 5, padx = 5, columnspan = 1)  

        self.filename = filename
        
        self.sample = sample_id
        self.data_path = "" # path for where the data has been stored
    
        self.open_image(self.window, self.filename, self.win_num)
    
    def close(self): 
        #print(self.win_num)
        close = tk.messagebox.askokcancel("Close", "Would you like to close the image? \nUnsaved data will be lost.")
        if close:
             #thumbs[self.win_num]
             self.window.destroy()    
    
    def open_image(self, parent, filename, win_num):   
    
        # open the file dialog box
        self.filename = filename
        if self.filename :    
            #close the opening menu
            #ST.starting_menu.toggle() 
            
            # show a temporary message while the image is loading            
            tmp_frame = ctk.CTkFrame(master=parent, width=400, height=500)            
            tmp_frame.grid(row = 0, column = 0, pady = 5, padx = 5)
            tmp_label = ctk.CTkLabel(tmp_frame, text = "Loading Image")                       
            tmp_label.grid(row = 0, column = 0, padx= 5, pady = 5) 
            tmp_label.configure(font=('Helvetica bold', 12))                 
            parent.update()
            
            full_name = os.path.basename(self.filename)
            self.sample = os.path.splitext(full_name)[0]               
            
            # Display the image in the app as a CanvasImage object
            # WS.DT[self.win_num].canvas = CanvasImage(parent, self.filename, self.sample, self.win_num)  # create widget
            # WS.DT[self.win_num].canvas.grid(row=0, column=0)  # show widget
            self.canvas = CanvasImage(parent, self.filename, self.sample, self.win_num)  # create widget
            self.canvas.grid(row=0, column=0)  # show widget
            
            #close the temporary message
            tmp_frame.grid_forget()            

        else:
            # if no file is selected do nothing
            return