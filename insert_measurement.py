# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 10:09:34 2023

@author: david
"""

import customtkinter
import win_array as WA
#import tkinter as tk

#import global_variables as ST
from global_functions import toggle_mode, toggle_series, set_order 
#, sort_object_list

class insert_measurement:
    def __init__(self, parent, win):
        # set if visible
        self.visible = False
        self.win_num = win
        
        #######################################################################
        # create a frame to hold all contents
        self.classframe = customtkinter.CTkFrame(parent)

        self.classframe.rowconfigure(0, weight = 1)       
       
        self.M1_label = customtkinter.CTkLabel(self.classframe, text = "Left click on the increment you want to add \nnew measurements before")
        self.M1_label.grid(row = 1, column = 0, pady = 5, columnspan = 2)        
                
        self.M1_label2 = customtkinter.CTkLabel(self.classframe, text = "No measurement selected")
        self.M1_label2.grid(row = 2, column = 0, pady = 5, columnspan = 2) 
        
        confirm_Select = customtkinter.CTkButton(self.classframe, text = "Confirm selection", command = self.insert_confirm)
        confirm_Select.grid(row = 3, column = 1, pady = 0, stick="nsew") 
        
        clear_Select = customtkinter.CTkButton(self.classframe, text = "Clear selection", command = self.insert_clear)
        clear_Select.grid(row = 3, column = 0, pady = 0, stick="nsew") 
        
        insert_submit = customtkinter.CTkButton(self.classframe, text = "Insert Measurements", command = self.insert_measurements)
        insert_submit.grid(row = 4, column = 0, columnspan = 2, pady = 5, stick="nsew") 
        
        insert_close = customtkinter.CTkButton(self.classframe, text = "Close", command = self.toggle)
        insert_close.grid(row = 5, column = 1, pady = 5, stick="nsew") 
            
    def insert_confirm(self):
        
        WA.wins[self.win_num].canvas.IDT.IN_CONFIRM == True
        ring_no = WA.wins[self.win_num].canvas.IDT.object_list[WA.wins[self.win_num].canvas.IDT.M1[1]].ind
        self.M1_label2.configure(text = ("Ring confirmed: " + str(WA.wins[self.win_num].canvas.IDT.M1[0]) + " " + str(ring_no) + "\nNow make the measurements"))
        toggle_mode("measure", self.win_num)
        toggle_series("insert", self.win_num)        
             
    def insert_clear(self):
        WA.wins[self.win_num].canvas.IDT.IN_CONFIRM == False
        self.M1_label2.configure(text = "No ring selected")
        WA.wins[self.win_num].canvas.IDT.M1 = [0]
    
    def insert_measurements(self):
        series = WA.wins[self.win_num].canvas.IDT.M1[0] # which series to insert the measurements into    
        ring = WA.wins[self.win_num].canvas.IDT.object_list[WA.wins[self.win_num].canvas.IDT.M1[1]].ind # which ring to insert them before
        n_rings = len(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES) # how rings to insert
        #print("ring num =" + str(ring) + "num of rungs = " + str(n_rings))
        
        #### change the numbers on existing measurements after the insert
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            if WA.wins[self.win_num].canvas.IDT.object_list[i].series == series and WA.wins[self.win_num].canvas.IDT.object_list[i].ind >= ring:
                
                WA.wins[self.win_num].canvas.IDT.object_list[i].ind = WA.wins[self.win_num].canvas.IDT.object_list[i].ind + n_rings
                WA.wins[self.win_num].canvas.IDT.object_list[i].label_text = WA.wins[self.win_num].canvas.IDT.object_list[i].ind + WA.wins[self.win_num].canvas.IDT.start_year
                WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].label,
                                               text = WA.wins[self.win_num].canvas.IDT.object_list[i].label_text)
        
        # update the labels on the insert series
        for i in range(len(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES)):
            #print("i + ring = " + str(i + ring))
            WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].label_text = i + ring + WA.wins[self.win_num].canvas.IDT.start_year          
            #WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].ind = WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].label_text            
            WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].label,
                                            text = WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].label_text)
            #print("new label text = " + str(WA.wins[self.win_num].canvas.IDT.object_list[i].label_text))
            
            # ST.canvas.canvas.itemconfigure(ST.object_list[i].label,
            #                                text = ST.object_list[i].label_text)
        
        ### change the insert measurements to the correct series
        if WA.wins[self.win_num].canvas.IDT.M1[0] == "series_1":            
            for i in range(len(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES)):
                obj = WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].obj_index
                
                WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[obj].object, fill = WA.wins[self.win_num].canvas.IDT.ser_1_col)
                WA.wins[self.win_num].canvas.IDT.object_list[obj].series = "series_1"
                WA.wins[self.win_num].canvas.IDT.object_list[obj].col = WA.wins[self.win_num].canvas.IDT.ser_1_col
                
        if WA.wins[self.win_num].canvas.IDT.M1[0] == "series_2":      
            print("runnnin order series 2g")
            for i in range(len(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES)):
                obj = WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].obj_index
                
                WA.wins[self.win_num].canvas.canvas.itemconfig(WA.wins[self.win_num].canvas.IDT.object_list[obj].object, fill = WA.wins[self.win_num].canvas.IDT.ser_2_col)
                WA.wins[self.win_num].canvas.IDT.object_list[obj].series = "series_2"
                WA.wins[self.win_num].canvas.IDT.object_list[obj].col = WA.wins[self.win_num].canvas.IDT.ser_2_col
                
        if WA.wins[self.win_num].canvas.IDT.M1[0] == "series_3":            
            for i in range(len(WA.wins[self.win_num].canvas.IDT.INSERT_SERIES)):
                obj = WA.wins[self.win_num].canvas.IDT.INSERT_SERIES[i].obj_index
                
                WA.wins[self.win_num].canvas.canvas.itemconfig(WA.wins[self.win_num].canvas.IDT.object_list[obj].object, fill = WA.wins[self.win_num].canvas.IDT.ser_3_col)
                WA.wins[self.win_num].canvas.IDT.object_list[obj].series = "series_3"
                WA.wins[self.win_num].canvas.IDT.object_list[obj].col = WA.wins[self.win_num].canvas.IDT.ser_3_col
        
        WA.wins[self.win_num].canvas.IDT.SERIES_1 = self.update_series("series_1")
        WA.wins[self.win_num].canvas.IDT.SERIES_2 = self.update_series("series_2")
        WA.wins[self.win_num].canvas.IDT.SERIES_3 = self.update_series("series_3")
        
        WA.wins[self.win_num].canvas.IDT.M1 = [0]
        WA.wins[self.win_num].canvas.IDT.IN_CONFIRM == False
        
        WA.wins[self.win_num].canvas.IDT.INSERT_SERIES = []
        toggle_mode("measure", self.win_num)
        toggle_series("series_1", self.win_num)
        WA.wins[self.win_num].canvas.sort_object_list()
        
                
    def update_series(self, series):                
        tmp_series = []
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            if WA.wins[self.win_num].canvas.IDT.object_list[i].series == series:
                tmp_series.append(WA.wins[self.win_num].canvas.IDT.object_list[i])              
        
        if len(tmp_series) != 0:                                  
            return set_order(tmp_series)
        else: return []
 
    def show(self):
        # toggle_mode("insert", self.win_num)
        # toggle_series("insert", self.win_num)            
        WA.wins[self.win_num].canvas.IDT.M1 = [0]
        WA.wins[self.win_num].canvas.IDT.IN_CONFIRM == False
        self.M1_label2.configure(text = "No measurement selected") 
        self.classframe.grid(row = 0, column = 0, pady = 125, sticky = "NW")

    def hide(self):
        toggle_mode("measure", self.win_num)
        tmp_series = WA.wins[self.win_num].canvas.IDT.prev_series
        toggle_series("series_1", self.win_num)
        WA.wins[self.win_num].canvas.IDT.prev_series = tmp_series
        self.classframe.grid_forget()
        WA.wins[self.win_num].canvas.IDT.INSERT_SERIES = []
                         
    def toggle(self):
        #if the frame is not visible, then show it.
        if self.visible == False:
            self.show()
        # iof the frame is currently visible, hide it.
        elif self.visible == True:
            self.hide()
        self.visible = not self.visible
        
        