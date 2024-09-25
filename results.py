# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 10:45:10 2023

@author: dr454
"""
import pandas as pd
import tkinter as tk
#import global_variables as ST
from pandastable import Table
import customtkinter
#from global_functions import reveerse_order, apply_years
# import matplotlib as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.figure import Figure
import win_array as WA

class results:
    def __init__(self, parent, win_num, sample_id):
        #global ST
        self.parent = parent
        self.win_num = win_num
        self.sample_id = sample_id
        self.visible = False
        self.data = None
        self.table = None
        self.pt = None
        self.window = None
        self.nav_frame = None
        self.res_frame = None   
        self.start_yr = None
        self.plot_frame = None
        
    def show(self):
        if self.visible == True: return
        self.window = tk.Toplevel(self.parent)        
        self.window.title("Measurements")
        self.window.iconbitmap("assets/title_icon.ico")                
        self.gen_res_table()
        self.window.update()
        
        self.nav_frame = tk.Frame(self.window)
        self.res_frame = tk.Frame(self.window)
        self.plot_frame = tk.Frame(self.window)
        self.nav_frame.grid(row= 0, column = 0)
        self.res_frame.grid(row= 1, column = 0)
        self.plot_frame.grid(row= 2, column = 0)
        
        self.show_table()
        self.window.geometry("600x350")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.visible = True

        
    def show_table(self): 
        update_btn = customtkinter.CTkButton(self.nav_frame, text = "Update table", 
                                              command = self.update,
                                              width=50)
        update_btn.grid(row = 0, column = 0, pady = 0, padx = 2) 
        
        invert_btn = customtkinter.CTkButton(self.nav_frame, text = "Reverse order", 
                                              command = self.reverse,
                                              width=50)
        invert_btn.grid(row = 0, column = 1, pady = 0, padx = 2) 
      
        start_label = tk.Label(self.nav_frame, text = "Enter start year")  
        start_label.grid(row=0, column = 2)
        
        self.start_yr =  tk.Entry(self.nav_frame)
        self.start_yr.insert(0, WA.wins[self.win_num].canvas.IDT.start_year)
        self.start_yr.grid(row=0, column = 3)
        
      
        apply_year_btn = customtkinter.CTkButton(self.nav_frame, text = "Toggle years", 
                                              command = self.apply_button,
                                              width=50)
        apply_year_btn.grid(row = 0, column = 4, pady = 0, padx = 2) 
      
 
        self.gen_res_table()
        if len(self.data.index) > 0:      
            self.table = self.pt = Table(self.res_frame, dataframe=self.data,
                                        showtoolbar=False, showstatusbar=False)
            self.pt.show()
        self.visible = True
        
    def gen_res_table(self):
        #Create a Label in New window
        ser_1_widths = []
        ser_2_widths = []
        ser_3_widths = []
        
        SERIES_1 = WA.wins[self.win_num].canvas.IDT.SERIES_1
        SERIES_2 = WA.wins[self.win_num].canvas.IDT.SERIES_2
        SERIES_3 = WA.wins[self.win_num].canvas.IDT.SERIES_3

        if SERIES_1 != None:
            len1 = len(SERIES_1)
        else: 
            len1 = 0
        if SERIES_2 != None:
            len2 = len(SERIES_2)
        else: 
            len2 = 0
        if SERIES_3 != None:
            len3 = len(SERIES_3)
        else: 
            len3 = 0
        
        max_ser = max(len1,len2, len3)               
        
        for i in range(max_ser):
            if i < len1:
                ser_1_widths.append(round(SERIES_1[i].abs_distance,3))
            else:
                ser_1_widths.append("NA")
            if i < len2:
                ser_2_widths.append(round(SERIES_2[i].abs_distance,3))
            else:
                ser_2_widths.append("NA")
            if i < len3:
                ser_3_widths.append(round(SERIES_3[i].abs_distance, 3))
            else:
                ser_3_widths.append("NA")  
      
        ring_index = list(range(int(WA.wins[self.win_num].canvas.IDT.start_year), 
                                max_ser + int(WA.wins[self.win_num].canvas.IDT.start_year)))
        
        self.data = pd.DataFrame({"Ring": ring_index,
                             "series_1": ser_1_widths,
                             "series_2": ser_2_widths,
                             "series_3": ser_3_widths})  
        
    def update(self):  
                  
        self.gen_res_table() 
        if len(self.data.index) > 0:       
            self.table = self.pt = Table(self.res_frame, dataframe=self.data,
                                        showtoolbar=False, showstatusbar=False)
            self.pt.show()
          
    def reverse(self):
        WA.wins[self.win_num].canvas.IDT.object_list.reverse()
        
        WA.wins[self.win_num].canvas.IDT.SERIES_1.reverse()
        WA.wins[self.win_num].canvas.IDT.SERIES_2.reverse()
        WA.wins[self.win_num].canvas.IDT.SERIES_3.reverse()
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_1)):
            WA.wins[self.win_num].canvas.IDT.SERIES_1[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_1[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_1[i].year
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_2)):
            WA.wins[self.win_num].canvas.IDT.SERIES_2[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_2[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_2[i].year

        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_3)):
            WA.wins[self.win_num].canvas.IDT.SERIES_3[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_3[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_3[i].year
     
        ser_1 = 0
        ser_2 = 0
        ser_3 = 0
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
              if WA.wins[self.win_num].canvas.IDT.object_list[i].mode == "measure" and WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_1":
                  WA.wins[self.win_num].canvas.IDT.object_list[i].ind = ser_1
                  ser_1 += 1
              if WA.wins[self.win_num].canvas.IDT.object_list[i].mode == "measure" and WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_2":
                  WA.wins[self.win_num].canvas.IDT.object_list[i].ind = ser_2
                  ser_2 += 1    
              if WA.wins[self.win_num].canvas.IDT.object_list[i].mode == "measure" and WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_3":
                  WA.wins[self.win_num].canvas.IDT.object_list[i].ind = ser_3
                  ser_3 += 1
                  
        #reveerse_order()
        self.update()
        self.update_labels()
    
    def update_labels(self):
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            WA.wins[self.win_num].canvas.IDT.object_list[i].label_text = WA.wins[self.win_num].canvas.IDT.object_list[i].year
            WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].label,
                                                              text = WA.wins[self.win_num].canvas.IDT.object_list[i].label_text)
    
    def close(self):
        self.window.destroy()
        self.visible = False
        
    def apply_button(self):
        
        WA.wins[self.win_num].canvas.IDT.assigned = not WA.wins[self.win_num].canvas.IDT.assigned
        WA.wins[self.win_num].canvas.IDT.start_year = int(self.start_yr.get())
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_1)):
            WA.wins[self.win_num].canvas.IDT.SERIES_1[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_1[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_1[i].year
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_2)):
            WA.wins[self.win_num].canvas.IDT.SERIES_2[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_2[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_2[i].year

        for i in range(len(WA.wins[self.win_num].canvas.IDT.SERIES_3)):
            WA.wins[self.win_num].canvas.IDT.SERIES_3[i].year = i + WA.wins[self.win_num].canvas.IDT.start_year
            WA.wins[self.win_num].canvas.IDT.SERIES_3[i].label_text = WA.wins[self.win_num].canvas.IDT.SERIES_3[i].year
     
        self.update_labels()
    

        
        # if WA.wins[self.win_num].canvas.IDT.assigned:
        #     for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
        #         WA.wins[self.win_num].canvas.IDT.label_text = WA.wins[self.win_num].canvas.IDT.object_list[i].ind + WA.wins[self.win_num].canvas.IDT.start_year 
        #         WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].label,
        #                                                           text = WA.wins[self.win_num].canvas.IDT.object_list[i].label_text)

        self.update()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        