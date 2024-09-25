# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 14:02:42 2023

@author: david
"""
import customtkinter
import tkinter as tk

from global_functions import toggle_mode, set_anno_type, toggle_series, analyse_axis

import win_array as WA

class toolbar:
    def __init__(self, parent, win_num):
        # set if visible
        self.visible = False
        self.parent = parent
        self.WN = int(win_num) # what window is this toolbar in?
        
        self.btn_x = 1
        self.btn_y = 2 # padding between buttons
        self.frm_x = 2
        self.btn_off = 0 # shift the buttons down by this number of pixels
        
        self.txt_bx_vis = False
        
        #######################################################################
        ### set postion of main frames
        mode_col = 0
        series_col = 1
        series_select_col = 2
        mode_select_col = 3
        anno_mode_col = 4
        growth_axis_col = 5
        micromill_col = 6
        sample_ID_col = 7
        
        
        #######################################################################
        # create a frame to hold all contents
        self.classframe = customtkinter.CTkFrame(self.parent)
        # self.classframe.grid(row = 0, column = 0, 
        #                     pady = 0, padx = 0, 
        #                     sticky = tk.NW)
        self.classframe.rowconfigure(0, weight = 1)
        
        
        #######################################################################
        #### create the contents
        #######################################################################
       
        ### Current sample
        
        self.current_sample_frame = customtkinter.CTkFrame(self.classframe)
        self.current_sample_frame.grid(row = 0, column = 0, 
                                    pady = 5, padx = self.frm_x, 
                                    sticky = tk.EW,
                                    columnspan = 5)
        
        self.sample_label = customtkinter.CTkLabel(self.current_sample_frame, text = "sample")
        self.sample_label.grid(row = 0, column = 0,  pady = 5, padx = 5)     
        
        #######################################################################
        ### current mode
        
        self.current_mode_frame = customtkinter.CTkFrame(self.classframe)
        self.current_mode_frame.grid(row = 1, column = mode_col, 
                                    pady = 0, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.mode_label = customtkinter.CTkLabel(self.current_mode_frame, text = "Mode")
        self.mode_label.grid(row = 0, column = 0, pady = 5, padx = 5)  
        
        self.active_mode_label = customtkinter.CTkLabel(self.current_mode_frame, text = "active")
        self.active_mode_label.grid(row = 1, column = 0, pady = 0, padx = 5) 
        
        #######################################################################
        ### current series
        
        self.current_series_frame = customtkinter.CTkFrame(self.classframe)
        self.current_series_frame.grid(row = 1, column = series_col, 
                                    pady = 0, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.series_label = customtkinter.CTkLabel(self.current_series_frame, text = "sample")
        self.series_label.grid(row = 0, column = 0, pady = 5, padx = 5)  
        
        self.current_series_label = customtkinter.CTkLabel(self.current_series_frame, text = "Series_1")
        self.current_series_label.grid(row = 1, column = 0, pady = 0, padx = 5) 
        
        
        #######################################################################
        
        self.series_select_frame = customtkinter.CTkFrame(self.classframe)
        self.series_select_frame.grid(row = 1, column = series_select_col, 
                                    pady = 0, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.series_select_label = customtkinter.CTkLabel(self.series_select_frame, text = "Select series")
        self.series_select_label.grid(row = 0, column = 0, pady = 5, padx = 5)  
      
        self.series_selectbox = customtkinter.CTkComboBox(self.series_select_frame,
                                                         values=["series_1", "series_2", "series_3"],
                                                         command= self.series_select)
        self.series_selectbox.grid(row=1, column = 0, pady = 5, padx = 5)
        
        #######################################################################
        ### mode select
        
        self.mode_select_frame = customtkinter.CTkFrame(self.classframe)
        self.mode_select_frame.grid(row = 1, column = mode_select_col, 
                                    pady = self.btn_off, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.mode_select_label = customtkinter.CTkLabel(self.mode_select_frame, text = "Select Measurement Mode")
        self.mode_select_label.grid(row = 0, column = 0, columnspan = 5, pady = 0, padx = 5)  
        
        ### measure        
        self.measure_btn = customtkinter.CTkButton(self.mode_select_frame, text = "Measure",
                                                     command = lambda: self.tools_toggle_mode("measure"),
                                                     width=50)
        self.measure_btn.grid(row = 1, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### adjust
        # self.adjust_btn = customtkinter.CTkButton(self.mode_select_frame, text = "Adjust",
        #                                              command = lambda: self.tools_toggle_mode("adjust"),
        #                                              width=50)
        # self.adjust_btn.grid(row = 1, column = 1, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### insert
        self.insert_btn = customtkinter.CTkButton(self.mode_select_frame, text = "insert",
                                                     command = lambda: self.tools_toggle_mode("insert"),
                                                     width=50)
        self.insert_btn.grid(row = 1, column = 1, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### delete        
        # self.delete_btn = customtkinter.CTkButton(self.mode_select_frame, text = "Delete",
        #                                              command = lambda: self.tools_toggle_mode("delete"),
        #                                              width=50)
        # self.delete_btn.grid(row = 1, column = 3, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### calibrate
        self.calibrate_btn = customtkinter.CTkButton(self.mode_select_frame, text = "Calibrate",
                                                     command = lambda: self.tools_toggle_mode("calibrate"),
                                                     width=50)
        self.calibrate_btn.grid(row = 1, column = 2, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)     
        
        ### AI
        self.ai_btn = customtkinter.CTkButton(self.mode_select_frame, text = "AI Mode",
                                                     command = lambda: self.tools_toggle_mode("ai"),
                                                     width=50)
        self.ai_btn.grid(row = 1, column = 3, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW) 
        
        
        #######################################################################     
        ### annotation mode
        
        self.anno_mode_frame = customtkinter.CTkFrame(self.classframe)
        self.anno_mode_frame.grid(row = 1, column = anno_mode_col, 
                                    pady = self.btn_off, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.anno_select_label = customtkinter.CTkLabel(self.anno_mode_frame, text = "Select Annottion Mode TEST")
        self.anno_select_label.grid(row = 0, column = 0, columnspan = 3, pady = 0, padx = self.frm_x)  
        
        ### line        
        self.line_btn = customtkinter.CTkButton(self.anno_mode_frame, text = "Line",
                                                     command = lambda: self.tools_anno_mode("line"),
                                                     width=50)
        self.line_btn.grid(row = 1, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### dot
        self.dot_btn = customtkinter.CTkButton(self.anno_mode_frame, text = "Dot",
                                                     command = lambda: self.tools_anno_mode("dot"),
                                                     width=50)
        self.dot_btn.grid(row = 1, column = 1, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        ### text
        self.text_btn = customtkinter.CTkButton(self.anno_mode_frame, text = "Text",
                                                     command = lambda: self.tools_anno_mode("text"),
                                                     width=50)
        self.text_btn.grid(row = 1, column = 2, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
    
        # self.test_btn = customtkinter.CTkButton(self.anno_mode_frame, text = "Text",
        #                                              command = self.test,
        #                                              width=50)
        # self.test_btn.grid(row = 1, column = 3, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
    
    ###########################################################################
     
    #######################################################################     
    ### edit sample ID
    
        self.sample_ID_frame = customtkinter.CTkFrame(self.classframe)
        self.sample_ID_frame.grid(row = 1, column = sample_ID_col, 
                                    pady = self.btn_off, padx = self.frm_x, 
                                    sticky = tk.NW)
        
        self.sample_ID_label = customtkinter.CTkLabel(self.sample_ID_frame, text = "Set sample ID")
        self.sample_ID_label.grid(row = 0, column = 0, columnspan = 3, pady = 0, padx = self.frm_x)  
        
        self.set_sample_ID = customtkinter.CTkEntry(self.sample_ID_frame)
        self.set_sample_ID.grid(row = 1, column = 0, pady = 5)
        #self.set_sample_ID.insert(0, "test") 
    
    
    
    # self.growth_axis_frame = customtkinter.CTkFrame(self.classframe)
        # self.growth_axis_frame.grid(row = 1, column = growth_axis_col, 
        #                             pady = self.btn_off, padx = self.frm_x, 
        #                             sticky = tk.NW)
        
        # self.anno_select_label = customtkinter.CTkLabel(self.growth_axis_frame, text = "Automated Analysis")
        # self.anno_select_label.grid(row = 0, column = 0, columnspan = 3, pady = 0, padx = self.frm_x)  
        
    
        # self.growth_axis_btn = customtkinter.CTkButton(self.growth_axis_frame, text = "Draw axis",
        #                                              command = lambda: self.tools_anno_mode("growth_Axis"),
        #                                              width=50)
        # self.growth_axis_btn.grid(row = 1, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)

        # self.model_select = customtkinter.CTkComboBox(master= self.growth_axis_frame,
        #                              values=["Select a model","General", "glycymeris"],
        #                              command= self.model_select)
        
        # self.model_select.grid(row = 1, column = 1, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)

        # self.run_model_btn = customtkinter.CTkButton(self.growth_axis_frame, text = "Analyse Growth Axis",
        #                                              command = self.tools_axis_run,
        #                                              width=50)
        # self.run_model_btn.grid(row = 1, column = 2, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)


    ###########################################################################
        # self.micromill_frame = customtkinter.CTkFrame(self.classframe)
        # self.micromill_frame.grid(row = 1, column = micromill_col, 
        #                             pady = self.btn_off, padx = self.frm_x, 
        #                             sticky = tk.NW)
        
        # self.anno_select_label = customtkinter.CTkLabel(self.micromill_frame, text = "Micromill tracks")
        # self.anno_select_label.grid(row = 0, column = 0, columnspan = 4, pady = 0, padx = self.frm_x)  
        
        # self.ref_point_btn = customtkinter.CTkButton(self.micromill_frame, text = "Add reference point",
        #                                              command = self.add_ref_points,
        #                                              width=50)
        # self.ref_point_btn.grid(row = 1, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        # self.micro_line_btn = customtkinter.CTkButton(self.micromill_frame, text = "Add drill line",
        #                                              command = self.add_drill_line,
        #                                              width=50)
        # self.micro_line_btn.grid(row = 1, column = 2, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        # self.drill_bit_label = customtkinter.CTkLabel(self.growth_axis_frame, text = "Drill bit size")
        # self.drill_bit_label.grid(row = 0, column = 0, columnspan = 3, pady = 0, padx = self.frm_x) 
        
        # self.micro_dot_btn = customtkinter.CTkButton(self.micromill_frame, text = "Add drill dot",
        #                                              command = self.add_drill_dot,
        #                                              width=50)
        # self.micro_dot_btn.grid(row = 1, column = 3, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
        
        
        # self.drill_size_entry = customtkinter.CTkEntry(self.micromill_frame)
        # self.drill_size_entry.grid(row = 1, column = 4, pady = 5)
        # self.drill_size_entry.insert(0, "Enter drill bit size (um)") 

        
   
    
    ###########################################################################

    def add_ref_points(self):
        print("Add ref point mode")
        self.tools_toggle_mode("ref_point")
        self.active_mode_label.configure(text = str("Add Reference Point"))
        
    def add_drill_line(self):
        print("drill line")
        self.tools_toggle_mode("drill_line")
        self.active_mode_label.configure(text = str("Add drill line"))
        
    def add_drill_dot(self):
        print("drill_dot") 
        self.tools_toggle_mode("drill_point")
        self.active_mode_label.configure(text = str("Add drill spot"))
            
    # def test(self):
    #     gb_test(self.WN)
    
    def show(self):
        self.classframe.grid(row = 0, column = 0, sticky = "NW")

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
        
    def tools_toggle_mode(self, mode):
        if mode != "anno":
            self.active_mode_label.configure(text = mode)
        toggle_mode(mode, self.WN)
        
    def tools_anno_mode(self, anno_mode):
        self.tools_toggle_mode("anno")
        self.active_mode_label.configure(text = str("Anno: " + anno_mode))
        set_anno_type(anno_mode, self.WN)
        
        if anno_mode =="text":
            self.show_text_box()
        
    def series_select(self, event):
        series = self.series_selectbox.get()
        self.current_series_label.configure(text = series)
        toggle_series(series, self.WN)
        
    def show_text_box(self):
        
        if self.txt_bx_vis == False:                        
            
            self.text_frame = customtkinter.CTkFrame(self.parent)
            self.text_frame.grid(row = 1, column = 0, sticky = "NW")
            
            self.txt_bx_lbl = customtkinter.CTkLabel(self.text_frame, text = "Enter text in box \nthen click on image to place.")
            self.txt_bx_lbl.grid(row = 0, column = 0,  pady = 0, padx = 5)  
            
            self.text_entry = customtkinter.CTkEntry(self.text_frame)
            self.text_entry.grid(row = 1, column = 0, pady = 5)
            
            self.txt_cls_btn = customtkinter.CTkButton(self.text_frame, text = "close text window",
                                                         command = self.close_txt_win,
                                                         width=50)
            
            self.txt_cls_btn.grid(row = 2, column = 0, pady = self.btn_y, padx = self.btn_x, sticky=tk.EW)
            
            self.txt_bx_vis = not self.txt_bx_vis

    def close_txt_win(self):
        self.txt_bx_vis = False
        self.text_frame.grid_forget()
        toggle_mode("measure", self.WN)
        self.active_mode_label.configure(text = str("Measure"))
        self.parent.focus_set()
        
    def tools_axis_run(self):
        WA.wins[self.WN].canvas.CVI_analyse_axis()
        
    def model_select(self, event):
        WA.wins[self.WN].canvas.IDT.model = event
        print(event)