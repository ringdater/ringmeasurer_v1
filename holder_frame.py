# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 08:18:18 2023

@author: david
"""
import customtkinter
import tkinter as tk

class holder_frame:
    def __init__(self, parent):
        self.visible = False        
        
        self.classframe = customtkinter.CTkFrame(parent)
        self.classframe.rowconfigure(0, weight = 1)
        
        self.label = customtkinter.CTkLabel(self.classframe, 
                                            text = "The menu is only visible\n" +
                                            "once an image has been loaded")
        self.label.grid(row = 0, column = 0, pady = 5, padx = 5)
        
        self.close_btn = customtkinter.CTkButton(self.classframe, text = "Close",
                                                     command = self.toggle,
                                                     width=50)
        self.close_btn.grid(row = 1, column = 0, pady = 5, padx = 5, sticky=tk.EW)       
    
    def show(self):
        self.classframe.grid(row = 0, column = 0, sticky = "NW", pady = 5, padx = 5)

    def hide(self):
        self.classframe.grid_forget()
                         
    def toggle(self):
        #if the frame is not visible, then show it.
        if self.visible == False:
            self.show()
        # iof the frame is currently visible, hide it.
        elif self.visible == True:
            self.hide()
        self.visible = not self.visible