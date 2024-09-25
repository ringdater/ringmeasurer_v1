# -*- coding: utf-8 -*-
"""
@Title: Ring Measurer AI 

@author: David Reynolds
@Co-authors: George De Ath, Richard Everson
@Contact: d.reynolds2@exeter.ac.uk

 Ring Measurer AI is a proof of concept tool for the application of
 machine learning in growth ring and line detection and analysis. 
 Principally designed  for use in dendrochronology and sclerochronology
 applications.
 
Source code for the AI training and validation are available from:
    https://github.com/georgedeath/shellai
    
Source code for the Ring Measurer App are available at:
### insert github URL here.    

#############################################################################
Citation information:
    Reynolds, D.J, De Ath, G., Everson, R., The application of machine 
    learning in growth ring identification and analysis. In prep.
    
#############################################################################

This file contains the main function for running the app.
All dependencies will be automatically loaded

"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from tkinter import PhotoImage, filedialog
import os

from img_window import img_win
from summary_thumbnails import summary_thumbnails
import win_array as WA




class MainWindow(ttk.Frame):
    def __init__(self, mainframe):
        ttk.Frame.__init__(self, master=mainframe)
        self.master.title('Ring Measurer AI')
        self.master.geometry('800x600')  # size of the main window
        self.master.rowconfigure(0, weight=1)  # make the CanvasImage widget expandable
        self.master.columnconfigure(0, weight=1)
        self.master.protocol("WM_DELETE_WINDOW", self.close)
        
        icon_path = "assets/title_icon.png"
        icon = PhotoImage(file=icon_path)
        self.master.iconphoto(True, icon)

        self.mainframe = ctk.CTkFrame(self.master)
        self.mainframe.grid(row=0, column=0, pady=0, sticky="NSEW")
        self.mainframe.columnconfigure(0, weight=1)
        
        titleframe = ctk.CTkFrame(self.mainframe)
        titleframe.grid(row=0, column=0, pady=0, sticky="NEW")
        titleframe.rowconfigure(0, weight=1)       
        titleframe.columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(titleframe, text="Starting Point")
        title_label.grid(row=0, column=0, sticky="NW", pady=5, padx=5, columnspan=1)  
        
        btn = ctk.CTkButton(titleframe, text="Open image", command=self.open_new_win)
        btn.grid(row=1, column=0, sticky="NW", pady=5, padx=5, columnspan=1)  
                
        self.bodyframe = ctk.CTkScrollableFrame(self.mainframe, height=490)
        self.bodyframe.grid(row=1, column=0, padx=5, pady=5, sticky="EW")
        self.bodyframe.columnconfigure(0, weight=1)     
               
        self.master.bind("<Map>", self.check_focus2)
        
    def open_new_win(self):
        filename = filedialog.askopenfilename(initialdir=os.getcwd() + "/images", title="Select a File")
        if filename:
            full_name = os.path.basename(filename)
            sample_id = os.path.splitext(full_name)[0]
            WA.wins.append(img_win(self.master, filename, len(WA.wins), sample_id))
            summary_thumbnails(self.bodyframe, sample_id, filename, len(WA.wins))
        else:
            return

    def check_focus2(self, event=None):
        self.master.lift()
        self.master.focus_force()
    
    def close(self):      
        close = messagebox.askokcancel("Close", "Would you like to close the program? \nUnsaved data will be lost.")
        if close:
            self.master.destroy()    
        
if __name__ == "__main__":
    WA.init()
    app = MainWindow(tk.Tk())
    app.mainloop()
