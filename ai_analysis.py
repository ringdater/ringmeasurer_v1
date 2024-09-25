#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 15:06:44 2024

@author: dr454
"""

import customtkinter
import tkinter as tk

from tkinter import filedialog
from PIL import Image, ImageTk
import os

from global_functions import toggle_mode, set_anno_type, toggle_series, analyse_axis, run_model

import win_array as WA

class AI_analysis:
    def __init__(self, win, parent, filename):
        self.visible = False
        self.parent = parent
        self.WN = int(win) # what window is this toolbar in?
        self.filename = filename
        
        self.visible = False
        self.btn_y = 1
        self.btn_x = 1
        
        #######################################################################
        # create a frame to hold all contents
        self.classframe = customtkinter.CTkFrame(self.parent)
        # self.classframe.grid(row = 0, column = 0, 
        #                     pady = 0, padx = 0, 
        #                     sticky = tk.NW)
        self.classframe.rowconfigure(0, weight = 1)
        
        self.sample_label = customtkinter.CTkLabel(self.classframe, text = "AI analysis")
        self.sample_label.grid(row = 0, column = 0,  pady = 5, padx = 5)     
        
        
        self.model_label = customtkinter.CTkLabel(self.classframe, text = "Select AI Model")
        self.model_label.grid(row = 1, column = 0,  pady = 5, padx = 5)   
        
        self.model_selectbox = customtkinter.CTkComboBox(self.classframe,
                                                         values=[],
                                                         command= self.model_select)
        self.model_selectbox.grid(row=2, column = 0, pady = 5, padx = 5)
        # Call get_models to initially populate the ComboBox
        
        
        # close box
        self.close_btn = customtkinter.CTkButton(self.classframe, text = "Load growth axis",
                                                     command = self.load_Axis,
                                                     width=50)
        self.close_btn.grid(row = 3, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        # # close box
        self.draw_btn = customtkinter.CTkButton(self.classframe, text = "Save drawn axis",
                                                      command = self.save_draw_Axis,
                                                      width=50)
        self.draw_btn.grid(row = 3, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        
        
        # run model
        self.close_btn = customtkinter.CTkButton(self.classframe, text = "Run Model",
                                                     command = self.run_ai_model,
                                                     width=50)
        self.close_btn.grid(row = 5, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        
        # close box
        self.close_btn = customtkinter.CTkButton(self.classframe, text = "Close window",
                                                     command = self.toggle,
                                                     width=50)
        self.close_btn.grid(row = 6, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
       
    
    def get_models(self):        
        # Clear existing values
        self.model_selectbox.configure(values = [])
    
        # Get list of files in the specific folder
        folder_path = './models'  # Change this to the path of your folder
        files = os.listdir(folder_path)
                
        # Filter files to only include files (not directories) if needed
        files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
        
        # Update combo box values
        self.model_selectbox.configure(values = files)
        self.model_selectbox.set(files[0])
        
    def save_draw_Axis(self):
        objects = WA.wins[self.WN].canvas.IDT.object_list
        line_points = []        
        for i in range(len(objects)):
            if objects[i].type == "ai_point":
                line_points.append(objects[i])      
        
        points =[]
        for i in range(len(line_points)):
            point = WA.wins[self.WN].canvas.canvas.coords(line_points[i].object)
            x = (point[0] + point[2])/2
            y = (point[1] + point[3])/2
                        
            points.append(WA.wins[self.WN].canvas.absolute(x,y))
        
        self.axis_filename = analyse_axis(points, self.filename)
        print(self.axis_filename)
    
    def load_Axis(self):
        self.axis_filename = filedialog.askopenfilename(initialdir = os.getcwd() + "/images",
                                            title = "Select a File") 
        
        # self.axis_img = Image.open(self.axis_filename)
        # self.axis_img.thumbnail(self.MAX_sizE)
        # self.axis_img = ImageTk.PhotoImage(self.axis_img)
        
        # self.axis_thumbnail = tk.Label(self.frame, image = self.axis_img)
        # self.axis_thumbnail.image = self.axis_img
        
    def run_ai_model(self):
        
        model_choice = self.model_selectbox.get()
        
        
        self.AI_data = run_model(self.filename, self.axis_filename, model_choice)
        
        WA.wins[self.WN].canvas.show_AI_data(self.AI_data)
        
    def model_select(self, event):
        pass
    
    def show(self):
        self.classframe.grid(row = 0, column = 0, pady = 125, sticky = "NW")
        self.get_models()
        
    def hide(self):
        self.classframe.grid_forget()
                         
    def toggle(self):
        #if the frame is not visible, then show it.
        if self.visible == False:
            self.show()
        # iof the frame is currently visible, hide it.
        elif self.visible == True:
            self.hide()
            self.parent.focus_set()
        self.visible = not self.visible