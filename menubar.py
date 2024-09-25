# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 11:19:32 2023

@author: david
"""
from PIL import Image, ImageTk, ImageDraw, ImageFont
import tkinter as tk
from tkinter.filedialog import asksaveasfile
from tkinter import filedialog
import re
import pandas as pd
import os
import json
from tkinter.filedialog import asksaveasfilename

import win_array as WA

class MenuBar:
    def __init__(self, parent, win_num):
        self.parent = parent
        self.menu = tk.Menu(self.parent)
        self.win_num = win_num
        self.parent.config(menu=self.menu)

        self.fileMenu = tk.Menu(self.menu, tearoff=0)
        self.fileMenu.add_command(label="Load measurements", command = self.load_all_data)
        self.fileMenu.add_separator()
        #self.fileMenu.add_command(label="Save data", command = self.save_data)
        self.fileMenu.add_command(label="Save data as", command = self.save_all_data)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Save image with overlay", command = self.save_image_burnt_overlay)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Export measurements", command = self.export_measurements)
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Load micromill reference points", command = self.load_reference)
        # self.fileMenu.add_command(label="Export micromill points", command = self.save_tracks)

        # self.fileMenu.add_separator()
        # self.fileMenu.add_command(label="save data as json", command = self.save_json)

        # self.fileMenu.add_separator()
        # self.fileMenu.add_command(label="Load AI measurements", command = self.load_AI_data)
        
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label="Close image", command=self.exitProgram)
        
        self.resultsMenu = tk.Menu(self.menu, tearoff=0)
        self.resultsMenu.add_command(label="Show results table", command = self.show_results)

        self.settingsMenu = tk.Menu(self.menu, tearoff=0)
        self.settingsMenu.add_command(label="Show settings", command = self.show_settings)


        self.menu.add_cascade(label="File", menu=self.fileMenu)
        self.menu.add_cascade(label="Results", menu=self.resultsMenu)
        self.menu.add_cascade(label="Settings", menu=self.settingsMenu)

        
    def exitProgram(self):
        self.parent.destroy()
        
    def load_reference(self):
        filename = filedialog.askopenfilename(initialdir = os.getcwd() + "/images",
                                              title = "Select a File")
        
        # if a file is selected then do something:
        if filename:     
            #can read in any number of reference points
            WA.wins[self.win_num].canvas.IDT.ref_points = self.read_freference_points(filename)
            #print(WA.wins[self.win_num].canvas.IDT.ref_points)
        else:
            return
            
    def save_json(self):        
        file_path = asksaveasfilename(defaultextension=".json", 
                                      filetypes=[("JSON files", "*.json")],
                                      title="Save as")

        # If a valid file path is selected, write the JSON data to the file
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(WA.wins[self.win_num].canvas.IDT.to_dict(), f, indent=4)
            print(f"File saved successfully at {file_path}")
    
    def save_tracks(self):
        if len(WA.wins[self.win_num].canvas.IDT.object_list) == 0: return
        object_list = WA.wins[self.win_num].canvas.IDT.object_list
        
        old_refs =WA.wins[self.win_num].canvas.IDT.ref_points
        
        micromill_positions = []
        for i in range(len(object_list)):   
            if object_list[i].type == "reference":
                x_pos = (object_list[i].x1 + object_list[i].x2) /2
                y_pos = (object_list[i].y1 + object_list[i].y2) /2
                
                ref_point = [x_pos, y_pos, old_refs[i][2]] # uses z pos from micromill refs
                
                array_as_strings = [str(item) for item in ref_point]
                # Join the elements of the array with commas
                new_point = ','.join(array_as_strings)                
                micromill_positions.append("REF")
                micromill_positions.append(new_point)
                
            if object_list[i].type == "drill_line":
                point1 = [object_list[i].x1 + object_list[i].y1, old_refs[0][2]]
                point1 = [str(item) for item in point1]
                point1  = ','.join(point1 ) 
                
                point2 = [object_list[i].x2 + object_list[i].y2, old_refs[0][2]]
                point2 = [str(item) for item in point2]
                point2  = ','.join(point2 ) 
                
                micromill_positions.append("LINE")
                micromill_positions.append(point1)
                micromill_positions.append(point2)
                
        data = pd.DataFrame({"positions": micromill_positions})  
        
            
        try:
            file = asksaveasfile(defaultextension=".txt")
            if file: 
                # if a filename is given save the data.
                data.to_csv(file, sep='\t', header=False, index=False)
                file.close()
                
                #WA.wins[self.win_num].window.attributes('-topmost',True)
        except PermissionError:
            tk.messagebox.showerror(title="Warning", message="Error saving the file! \nCheck the file is not open in another application.")
        else:
            # if the user clicks cancel then do nothing.
            #WA.wins[self.win_num].window.attributes('-topmost',True)
            return
        
        
    def save_data(self):
        if len(WA.wins[self.win_num].canvas.IDT.object_list) == 0: return
        
        object_list = WA.wins[self.win_num].canvas.IDT.object_list
        
        sample_ID = []
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        mode = []
        series = []
        ob_type = []
        ind = []        
        text = []
        px_distance = []
        abs_distance = []
        calibration = []
        calibrated = []
        label_text = []
        year  = []    
        dated = []
        col = []
                
        regex = re.compile('[^a-zA-Z]')
        
        for i in range(len(object_list)):           
            sample_ID.append(WA.wins[self.win_num].sample)
            x1.append(object_list[i].x1)
            x2.append(object_list[i].x2)
            y1.append(object_list[i].y1)
            y2.append(object_list[i].y2)
            mode.append(object_list[i].mode)
            series.append(object_list[i].series)
            ob_type.append(regex.sub('', str(object_list[i].type)))
            ind.append(object_list[i].ind)     
            text.append(object_list[i].text)
            px_distance.append(object_list[i].px_distance)
            abs_distance.append(object_list[i].abs_distance)
            calibrated.append(object_list[i].calibrated)
            calibration.append(object_list[i].calibration)
            label_text.append(object_list[i].label_text)
            year.append(object_list[i].year)   
            dated.append(object_list[i].dated)
            col.append(object_list[i].col)
             
        data = pd.DataFrame({"sample_ID": sample_ID,
                            "x1":x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "mode": mode,
                            "series": series,
                            "ob_type": ob_type,
                            "ind": ind,       
                            "text": text,
                            "px_distance": px_distance,
                            "abs_distance": abs_distance,
                            "calibration": calibration,
                            "calibrated": calibrated,
                            "label_text": label_text,
                            "year": year,
                            "dated": dated,
                            "col": col                          
                             })     
        
        #use a file dialog box to let the user choose a filename and location
        if (WA.wins[self.win_num].data_path == ""):
            self.save_all_data()
        else :
            try:
                data.to_csv(WA.wins[self.win_num].data_path , sep=',', header = True, index = False , lineterminator='\n')
            except PermissionError:
                tk.messagebox.showerror(title="Warning", message="Error saving the file! \nCheck the file is not open in another application.")
        return
        
    def save_all_data(self):
        
        if len(WA.wins[self.win_num].canvas.IDT.object_list) == 0: return
        object_list = WA.wins[self.win_num].canvas.IDT.object_list
        
        sample_ID = []
        x1 = []
        y1 = []
        x2 = []
        y2 = []
        mode = []
        series = []
        ob_type = []
        ind = []        
        text = []
        px_distance = []
        abs_distance = []
        calibration = []
        calibrated = []
        label_text = []
        year  = []    
        dated = []
        col = []
                
        regex = re.compile('[^a-zA-Z]')
        
        for i in range(len(object_list)):           
            sample_ID.append(WA.wins[self.win_num].sample)
            x1.append(object_list[i].x1)
            x2.append(object_list[i].x2)
            y1.append(object_list[i].y1)
            y2.append(object_list[i].y2)
            mode.append(object_list[i].mode)
            series.append(object_list[i].series)
            ob_type.append(regex.sub('', str(object_list[i].type)))
            ind.append(object_list[i].ind)     
            text.append(object_list[i].text)
            px_distance.append(object_list[i].px_distance)
            abs_distance.append(object_list[i].abs_distance)
            calibrated.append(object_list[i].calibrated)
            calibration.append(object_list[i].calibration)
            label_text.append(object_list[i].label_text)
            year.append(object_list[i].year)   
            dated.append(object_list[i].dated)
            col.append(object_list[i].col)
             
        data = pd.DataFrame({"sample_ID": sample_ID,
                            "x1":x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "mode": mode,
                            "series": series,
                            "ob_type": ob_type,
                            "ind": ind,       
                            "text": text,
                            "px_distance": px_distance,
                            "abs_distance": abs_distance,
                            "calibration": calibration,
                            "calibrated": calibrated,
                            "label_text": label_text,
                            "year": year,
                            "dated": dated,
                            "col": col                          
                             })     
        
        #use a file dialog box to let the user choose a filename and location
        files = [('Comma Seperated Values', '*.csv'),
                  ('All Files', '*.*')]  
        try:
            file = asksaveasfile(defaultextension = ".csv")
            if file: 
                # if a filename is given save the data.
                
                data.to_csv(file, sep=',', header = True, index = False , lineterminator='\n')
                file.close()
                
                #WA.wins[self.win_num].window.attributes('-topmost',True)
        except PermissionError:
            tk.messagebox.showerror(title="Warning", message="Error saving the file! \nCheck the file is not open in another application.")
        else:
            # if the user clicks cancel then do nothing.
            #WA.wins[self.win_num].window.attributes('-topmost',True)
            return

    def load_all_data(self):
        
        # check if an image has already been loaded. Do nothing if there is no image                     
        if WA.wins[self.win_num].canvas == None: return
              
        
        # select a file
        filename = filedialog.askopenfilename(initialdir = os.getcwd() + "/images",
                                              title = "Select a File")
        
        # if a file is selected then do something:
        if filename:
            
            WA.wins[self.win_num].data_path = filename

            #open the file
            data = pd.read_csv(filename, sep = ",")            
            
            #iterate through the rows of the loaded data and extract the info
            # use tmp_measurement to temporarily to store the info of each 
            # measurement before it is put in the corect array
          
            WA.wins[self.win_num].canvas.load_the_data(data)
           #WA.wins[self.win_num].window.attributes('-topmost',True)
        else:
            #if no file was selected do nothing
           # WA.wins[self.win_num].window.attributes('-topmost',True)
            return
        
    def show_results(self):
        WA.wins[self.win_num].canvas.IDT.results.show()
              
    def show_settings(self):
        WA.wins[self.win_num].canvas.IDT.settings_window.toggle()
    
    def export_measurements(self):
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
      
        ring_index = list(range(WA.wins[self.win_num].canvas.IDT.start_year, max_ser + WA.wins[self.win_num].canvas.IDT.start_year))        
        
        data = pd.DataFrame({"Ring": ring_index,
                             WA.wins[self.win_num].sample + "_series_1": ser_1_widths,
                             WA.wins[self.win_num].sample +"_series_2": ser_2_widths,
                             WA.wins[self.win_num].sample +"_series_3": ser_3_widths})  
        
        #use a file dialog box to let the user choose a filename and location
        files = [('Comma Seperated Values', '*.csv'),
                  ('All Files', '*.*')]  
        try:
            #file = asksaveasfile(filetypes = files, defaultextension = ".csv")
            file = asksaveasfile(defaultextension = ".csv")

        except PermissionError:
            tk.messagebox.showerror(title="Warning", message="Error saving the file! \nCheck the file is not open in another application.")

        if file: 
            # if a filename is given save the data.
            data.to_csv(file, sep=',', header = True, index = False , lineterminator='\n')
            file.close()
        else:
            # if the user clicks cancel then do nothing.
            return
        
    def save_image_burnt_overlay(self):
        img = Image.open(WA.wins[self.win_num].filename)
        draw = ImageDraw.Draw(img)
        
        text_font = ImageFont.truetype('roboto-black.ttf', 32)
       # regex = re.compile('[^a-zA-Z]')
        
        for i in range(len(WA.wins[self.win_num].canvas.IDT.object_list)):
            tmp = WA.wins[self.win_num].canvas.IDT.object_list[i]
            labx_off = WA.wins[self.win_num].canvas.IDT.lab_x_off
            laby_off = WA.wins[self.win_num].canvas.IDT.lab_y_off
            
            if tmp.mode == "measure" and tmp.series == "series_1":
                draw.line((tmp.x1, tmp.y1,
                           tmp.x2, tmp.y2), 
                           fill= WA.wins[self.win_num].canvas.IDT.ser_1_col,
                           width = 5)
            
            if tmp.mode == "measure" and tmp.series == "series_2":
                draw.line((tmp.x1, tmp.y1,
                           tmp.x2, tmp.y2), 
                           fill= WA.wins[self.win_num].canvas.IDT.ser_2_col,
                           width = 5)
                
            if tmp.mode == "measure" and tmp.series == "series_3":
                draw.line((tmp.x1, tmp.y1,
                           tmp.x2, tmp.y2), 
                           fill= WA.wins[self.win_num].canvas.IDT.ser_3_col,
                           width = 5)
                
            if tmp.mode == "measure":
                if WA.wins[self.win_num].canvas.IDT.toggle_labels == 1:
                    px = (tmp.x1  + tmp.x2) / 2
                    py = (tmp.y1  + tmp.y2) / 2
                    draw.text((px + labx_off, py + laby_off), 
                           str(tmp.label_text), (0, 0, 0), font = text_font)
        
            if tmp.mode == "anno" and tmp.type == "dot":
                draw.ellipse((tmp.x1, tmp.y1,
                              tmp.x2,tmp.y2), 
                              fill = WA.wins[self.win_num].canvas.IDT.ANNOTE_COL,
                              outline =(0,0,0))
        
            if tmp.mode == "anno" and tmp.type == "line":
                draw.line((tmp.x1, tmp.y1,
                           tmp.x2, tmp.y2), 
                           fill= WA.wins[self.win_num].canvas.IDT.ANNOTE_COL,
                           width = 5)
            
            if tmp.mode == "anno" and tmp.type == "text":
                draw.text((tmp.x1, tmp.y1), 
                          str(tmp.text), 
                          (0, 0, 0), 
                          font = text_font)
        
 
        files = [ ('png', '*.png'),
                  ('All Files', '*.*')]    
        try:
            file = asksaveasfile(filetypes = files, defaultextension = ".png")
        except PermissionError:
            tk.messagebox.showerror(title="Warning", message="Error saving the file! \nCheck the file is not open in another application.")
 
        if file:
                img.save(file.name)
                file.close()
        else:
            return
        
    def load_AI_data(self):
        if WA.wins[self.win_num].canvas == None: return
              
        
        # select a file
        filename = filedialog.askopenfilename(initialdir = os.getcwd() + "/images",
                                              title = "Select a File")
        
        # if a file is selected then do something:
        if filename:
            
            WA.wins[self.win_num].data_path = filename

            #open the file
            data = pd.read_csv(filename, sep = ",")            
            
            #iterate through the rows of the loaded data and extract the info
            # use tmp_measurement to temporarily to store the info of each 
            # measurement before it is put in the corect array
          
            WA.wins[self.win_num].canvas.load_AI_data(data)
            #WA.wins[self.win_num].canvas.IDT.AI_window.toggle()

           #WA.wins[self.win_num].window.attributes('-topmost',True)
        else:
            #if no file was selected do nothing
           # WA.wins[self.win_num].window.attributes('-topmost',True)
            return
    
    def read_freference_points(self, filename):
        refs = []
        with open(filename, 'r') as file:
            for line in file:
                # get only rows containing numbers
                cleaned_line = line.strip()
                if cleaned_line and cleaned_line[0].isdigit():
                    refs.append(cleaned_line)
            
            # get rid of any non-numeric formating
            cleaned_arr = []
            for item in refs:
                cleaned_item = item.replace('\\', '').replace('}', '')
                cleaned_arr.append(cleaned_item)
            
            #create seperate arrays for each reference point and make sure values 
            #are numbers
            refs = []    
            for i in range(len(cleaned_arr)):                        
                numeric_values = cleaned_arr[i].split(',')            
                numeric_values = [float(value) for value in numeric_values]
                refs.append(numeric_values)
                
        return refs
        