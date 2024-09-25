# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 15:38:15 2023

@author: david
"""
import tkinter as tk
import customtkinter
from tkinter import colorchooser

import win_array as WA

#import global_variables as ST

class settings_window:
    def __init__(self, parent, win_num):        
        
        self.visible = False
        self.win_num = win_num
        
        self.vertical_offset = 125
        
        self.settings_frame = customtkinter.CTkScrollableFrame(parent, width = 400, height = 300)
        #self.settings_frame.grid(row = 0, column = 0, pady = self.vertical_offset, padx = 5)
        self.settings_frame.columnconfigure(0, minsize = 150)
        
       
    def choose_color(self, prev_colour): 
        # variable to store hexadecimal code of color
        color_code = colorchooser.askcolor(title ="Choose color")
        
        if color_code[1] != None:
            return color_code[1]
        else: return prev_colour
    
    def show(self):
        self.settings_frame.grid(row = 0, column = 0, pady = self.vertical_offset, sticky = "NW")
        series_col_label = customtkinter.CTkLabel(self.settings_frame, text = "Measurement colours")
        series_col_label.grid(row = 1, column = 0, pady = 5, columnspan = 2)
              
        self.ser1_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.ser1_col_entry.grid(row = 2, column = 1, pady = 5)
        self.ser1_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.ser_1_col) 
        
        ser1_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Series 1 colour", 
                                                command= lambda: [self.ser1_col_entry.delete(0, tk.END), self.ser1_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.ser_1_col))])
        ser1_col_btn.grid(row = 2, column = 0, pady = 5)
     
        self.ser2_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.ser2_col_entry.grid(row = 3, column = 1, pady = 5)
        self.ser2_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.ser_2_col)
        
        ser2_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Series 2 colour", 
                                                command= lambda: [self.ser2_col_entry.delete(0, tk.END), 
                                                                  self.ser2_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.ser_2_col))])
        ser2_col_btn.grid(row = 3, column = 0, pady = 5)
        
        self.ser3_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.ser3_col_entry.grid(row = 4, column = 1, pady = 5)
        self.ser3_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.ser_3_col) 
        
        ser3_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Series 3 colour", 
                                                command= lambda: [self.ser3_col_entry.delete(0, tk.END), 
                                                                  self.ser3_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.ser_3_col))])
        ser3_col_btn.grid(row = 4, column = 0, pady = 5)
        
        self.insert_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.insert_col_entry.grid(row = 5, column = 1, pady = 5)
        self.insert_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.insert_col)
        
        insert_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Insert measurements colour", 
                                                command= lambda: [self.insert_col_entry.delete(0, tk.END), 
                                                                  self.insert_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.insert_col))])
        insert_col_btn.grid(row = 5, column = 0, pady = 5)
        
        self.active_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.active_col_entry.grid(row = 6, column = 1, pady = 5)
        self.active_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.active_col)
        
        active_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Active measurement colour", 
                                                command= lambda: [self.active_col_entry.delete(0, tk.END), 
                                                                  self.active_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.active_col))])
        active_col_btn.grid(row = 6, column = 0, pady = 5)
               
        self.anno_col_entry = customtkinter.CTkEntry(self.settings_frame)
        self.anno_col_entry.grid(row = 7, column = 1, pady = 5)
        self.anno_col_entry.insert(0, WA.wins[self.win_num].canvas.IDT.ANNOTE_COL)
        
        anno_col_btn = customtkinter.CTkButton(master=self.settings_frame, text="Annotation colour", 
                                                command= lambda: [self.anno_col_entry.delete(0, tk.END), 
                                                                  self.anno_col_entry.insert(0, self.choose_color(WA.wins[self.win_num].canvas.IDT.ANNOTE_COL))])
        anno_col_btn.grid(row = 7, column = 0, pady = 5)
               
        
        
        
        
        line_thick_label = customtkinter.CTkLabel(self.settings_frame, text = "Line width")
        line_thick_label.grid(row = 8, column = 0, pady = 5) 
        
        self.line_thick_value = customtkinter.CTkSlider(self.settings_frame, from_=1, to=15)
        self.line_thick_value.grid(row = 8, column = 1, pady = 5) 
        self.line_thick_value.set(WA.wins[self.win_num].canvas.IDT.L_WIDTH)
        
        line_end_cap_label = customtkinter.CTkLabel(self.settings_frame, text = "Line end cap size")
        line_end_cap_label.grid(row = 9, column = 0, pady = 5) 
        
        self.line_end_cap_value = customtkinter.CTkSlider(self.settings_frame, from_=1, to=100)
        self.line_end_cap_value.grid(row = 9, column = 1, pady = 5) 
        self.line_end_cap_value.set(WA.wins[self.win_num].canvas.IDT.line_cap_len)
        
        line_cap_thick_label = customtkinter.CTkLabel(self.settings_frame, text = "Line end cap tickness")
        line_cap_thick_label.grid(row = 10, column = 0, pady = 5) 
        
        self.line_cap_thick_value = customtkinter.CTkSlider(self.settings_frame, from_=1, to=100)
        self.line_cap_thick_value.grid(row = 10, column = 1, pady = 5) 
        self.line_cap_thick_value.set(WA.wins[self.win_num].canvas.IDT.line_cap_thickness)      
                
        show_label_label = customtkinter.CTkLabel(self.settings_frame, text = "Show/Hide measurement labels")
        show_label_label.grid(row = 11, column = 0, pady = 5)
        
        label_btn = customtkinter.CTkButton(self.settings_frame, text = "Toggle labels",
                                                command = self.show_labels,
                                                width = 100)
        label_btn.grid(row = 11, column = 1, padx = 5, sticky=tk.EW) 
                
        x_off_label = customtkinter.CTkLabel(self.settings_frame, text = "Labels X position")
        x_off_label.grid(row = 12, column = 0, pady = 5) 
        
        self.lab_x_off_value = customtkinter.CTkSlider(self.settings_frame, from_=-50, to=50)
        self.lab_x_off_value.grid(row = 12, column = 1, pady = 5) 
        self.lab_x_off_value.set(WA.wins[self.win_num].canvas.IDT.lab_x_off)
        
        y_off_label = customtkinter.CTkLabel(self.settings_frame, text = "Labels Y position")
        y_off_label.grid(row = 13, column = 0, pady = 5) 
        
        self.lab_y_off_value = customtkinter.CTkSlider(self.settings_frame, from_=-50, to=50)
        self.lab_y_off_value.grid(row = 13, column = 1, pady = 5) 
        self.lab_y_off_value.set(WA.wins[self.win_num].canvas.IDT.lab_y_off)
        
        proximity_label = customtkinter.CTkLabel(self.settings_frame, text = "Proximity")
        proximity_label.grid(row = 14, column = 0, pady = 5) 
        
        self.proximity_value = customtkinter.CTkSlider(self.settings_frame, from_=1, to=40)
        self.proximity_value.grid(row = 14, column = 1, pady = 5) 
        self.proximity_value.set(WA.wins[self.win_num].canvas.IDT.PROXIMITY)
                      
        insert_submit = customtkinter.CTkButton(self.settings_frame, text = "Apply",
                                                command = self.apply_settings,
                                                width = 100)
        insert_submit.grid(row = 19, column = 0, padx = 5, sticky=tk.EW) 
        
        calib_submit = customtkinter.CTkButton(self.settings_frame, text = "Close", 
                                                command = self.toggle,
                                                width = 100)
        calib_submit.grid(row = 19, column = 1, padx = 5, sticky=tk.EW)  
        

    def hide(self):
        self.settings_frame.grid_forget()
                         
    def toggle(self):
        #if the frame is not visible, then show it.
        if self.visible == False:
            self.show()
        # iof the frame is currently visible, hide it.
        elif self.visible == True:
            self.hide()
        self.visible = not self.visible
        
        
    def show_labels(self):        
        WA.wins[self.win_num].canvas.IDT.toggle_labels = -WA.wins[self.win_num].canvas.IDT.toggle_labels

        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            if WA.wins[self.win_num].canvas.IDT.toggle_labels == -1:
                WA.wins[self.win_num].canvas.canvas.delete(WA.wins[self.win_num].canvas.IDT.object_list[i].label)    
            
            if WA.wins[self.win_num].canvas.IDT.toggle_labels == 1: 
                
                pos = WA.wins[self.win_num].canvas.canvas.coords(WA.wins[self.win_num].canvas.IDT.object_list[i].object)
                
                posx = (pos[0]+pos[2])/2
                posy = (pos[1]+pos[3])/2
                
                label_x = posx + WA.wins[self.win_num].canvas.IDT.lab_x_off
                label_y = posy + WA.wins[self.win_num].canvas.IDT.lab_y_off
              
                WA.wins[self.win_num].canvas.IDT.object_list[i].label = WA.wins[self.win_num].canvas.canvas.create_text(label_x, label_y,
                                                                        text = WA.wins[self.win_num].canvas.IDT.object_list[i].label_text, 
                                                                        fill = "black", 
                                                                        font = ('Helvetica 15 bold'))
                

    
    def apply_settings(self):             
        
        WA.wins[self.win_num].canvas.IDT.ser_1_col = self.ser1_col_entry.get()
        WA.wins[self.win_num].canvas.IDT.ser_2_col = self.ser2_col_entry.get()
        WA.wins[self.win_num].canvas.IDT.ser_3_col = self.ser3_col_entry.get()
        WA.wins[self.win_num].canvas.IDT.active_col = self.active_col_entry.get()
        WA.wins[self.win_num].canvas.IDT.insert_col = self.insert_col_entry.get()
        
        WA.wins[self.win_num].canvas.IDT.ANNOTE_COL = self.anno_col_entry.get()

        WA.wins[self.win_num].canvas.IDT.L_WIDTH = self.line_thick_value.get()
        
        WA.wins[self.win_num].canvas.IDT.line_cap_len = self.line_end_cap_value.get()
        WA.wins[self.win_num].canvas.IDT.line_cap_thickness = self.line_cap_thick_value.get()
        
        WA.wins[self.win_num].canvas.IDT.line_cap = (WA.wins[self.win_num].canvas.IDT.line_cap_thickness, 
                                                     0, 
                                                     WA.wins[self.win_num].canvas.IDT.line_cap_len)
        
        WA.wins[self.win_num].canvas.IDT.lab_x_off = self.lab_x_off_value.get()
        WA.wins[self.win_num].canvas.IDT.lab_y_off = self.lab_y_off_value.get()

        WA.wins[self.win_num].canvas.IDT.PROXIMITY = self.proximity_value.get()
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            if WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_1":
                WA.wins[self.win_num].canvas.IDT.object_list[i].col = WA.wins[self.win_num].canvas.IDT.ser_1_col
                WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].object,
                                                          fill =  WA.wins[self.win_num].canvas.IDT.ser_1_col,
                                                          width= WA.wins[self.win_num].canvas.IDT.L_WIDTH,                                                          
                                                          arrowshape = WA.wins[self.win_num].canvas.IDT.line_cap)
        
            if WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_2":
                WA.wins[self.win_num].canvas.IDT.object_list[i].col = WA.wins[self.win_num].canvas.IDT.ser_2_col
                WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].object,
                                                          fill =  WA.wins[self.win_num].canvas.IDT.ser_2_col,
                                                          width= WA.wins[self.win_num].canvas.IDT.L_WIDTH,                                                          
                                                          arrowshape = WA.wins[self.win_num].canvas.IDT.line_cap)       
            
            if WA.wins[self.win_num].canvas.IDT.object_list[i].series == "series_3":
                WA.wins[self.win_num].canvas.IDT.object_list[i].col = WA.wins[self.win_num].canvas.IDT.ser_3_col
                WA.wins[self.win_num].canvas.canvas.itemconfigure(WA.wins[self.win_num].canvas.IDT.object_list[i].object,
                                                          fill =  WA.wins[self.win_num].canvas.IDT.ser_3_col,
                                                          width= WA.wins[self.win_num].canvas.IDT.L_WIDTH,                                                          
                                                          arrowshape = WA.wins[self.win_num].canvas.IDT.line_cap)     
        WA.wins[self.win_num].window.attributes('-topmost',True)        
                
                
                
                