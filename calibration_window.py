# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 16:10:25 2023

@author: david
"""

import tkinter as tk
import customtkinter

#import global_variables as ST
from global_functions import toggle_mode

import win_array as WA

class calibration_window:
    def __init__(self, parent, win_num):
        
        self.visible = False
                        
        self.win_num = win_num
        
        self.calib_frame = customtkinter.CTkFrame(parent, width = 200, height = 200)
        #self.calib_frame.grid(row = 0, column = 0, pady = 115)
        
        self.calib_label = customtkinter.CTkLabel(self.calib_frame, text = "Use the mouse (left click) to measure \nthe scale bar ")
        self.calib_label.grid(row = 0, column = 0, pady = 5, columnspan = 2)
        
        self.calib_label = customtkinter.CTkLabel(self.calib_frame, text = "Enter distance measured (um)")
        self.calib_label.grid(row = 1, column = 0, pady = 5, columnspan = 2)        
                
        self.calib_dist = tk.Entry(self.calib_frame)
        self.calib_dist.grid(row = 2, column = 0, pady = 5, columnspan = 2)  
        
        self.calib_submit = customtkinter.CTkButton(self.calib_frame, text = "Submit", command = lambda: self.set_calibration(self.calib_dist.get()))
        self.calib_submit.grid(row = 3, column = 0, pady = 0, sticky = tk.EW) 
        
        self.calib_close = customtkinter.CTkButton(self.calib_frame, text = "Close", command = self.toggle)
        self.calib_close.grid(row = 3, column = 1, pady = 0, sticky = tk.EW)  
        
        self.cal_set_label = customtkinter.CTkLabel(self.calib_frame, text = "No Calibration set:" )
        self.cal_set_label.grid(row = 4, column = 0, pady = 5, columnspan = 2)
        
        #print(WA.wins[self.win_num].canvas.IDT.CALIBRATED)
        # if WA.wins[self.win_num].canvas.IDT.CALIBRATED == True:
        #     cal_set_label = tk.Label(self.calib_frame, text = "Calibration set: " + str(round(WA.wins[self.win_num].canvas.IDT.CALIBRATION.sf, 3)))
        #     cal_set_label.grid(row = 4, column = 0, pady = 5)
            
            
    def show(self):
        self.calib_frame.grid(row = 0, column = 0, pady = 125, padx = 5, sticky = "NW")

    def hide(self):
        self.calib_frame.grid_forget()
        
                         
    def toggle(self):
        #if the frame is not visible, then show it.
        if self.visible == False:
            self.show()
        # if the frame is currently visible, hide it.
        elif self.visible == True:
            self.hide()
            toggle_mode("measure", self.win_num)
            WA.wins[self.win_num].canvas.IDT.toolbar.active_mode_label.configure(text = str("Measure"))
        self.visible = not self.visible   
        
    def set_calibration(self, value):          
        if WA.wins[self.win_num].canvas.IDT.CALIBRATED == False:
            WA.wins[self.win_num].canvas.IDT.object_list[len(WA.wins[self.win_num].canvas.IDT.object_list)-1].abs_distance = float(value)
            
            WA.wins[self.win_num].canvas.IDT.calibration_SF = 1/ (float(WA.wins[self.win_num].canvas.IDT.object_list[len(WA.wins[self.win_num].canvas.IDT.object_list)-1].px_distance)/ WA.wins[self.win_num].canvas.IDT.object_list[len(WA.wins[self.win_num].canvas.IDT.object_list)-1].abs_distance)
            WA.wins[self.win_num].canvas.IDT.object_list[len(WA.wins[self.win_num].canvas.IDT.object_list)-1].calibration = WA.wins[self.win_num].canvas.IDT.calibration_SF
            self.cal_set_label = customtkinter.CTkLabel(self.calib_frame, text = "Calibration set:" + str(round(WA.wins[self.win_num].canvas.IDT.object_list[len(WA.wins[self.win_num].canvas.IDT.object_list)-1].calibration, 3)))
            self.cal_set_label.grid(row = 4, column = 0, pady = 5)
            WA.wins[self.win_num].canvas.IDT.CALIBRATED = True        
        self.calibrate_series()
            
    def calibrate_series(self):        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):        
            WA.wins[self.win_num].canvas.IDT.object_list[i].calibration = WA.wins[self.win_num].canvas.IDT.calibration_SF
            print(WA.wins[self.win_num].canvas.IDT.object_list[i].mode)
            if WA.wins[self.win_num].canvas.IDT.object_list[i].mode == "measure":
                WA.wins[self.win_num].canvas.IDT.object_list[i].abs_distance = WA.wins[self.win_num].canvas.IDT.object_list[i].px_distance * WA.wins[self.win_num].canvas.IDT.object_list[i].calibration
                WA.wins[self.win_num].canvas.IDT.object_list[i].calibrated = True  
        
        
        
        
        
        
        
        
        
        