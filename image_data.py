# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 09:24:29 2023

@author: dr454
"""
import re

class image_data:    
    def __init__(self, img_win, filename, sample_id):
        self.img_win = img_win
        self.filename = filename
        self.sample_id = sample_id
        
        self.TOP_LEFT = None # used to keep track of the image position when zooming and scrolling
        
        self.toolbar = None
        self.calib_frame = None
        self.settings_window = None
        self.error_frame = None
        self.insert_frame = None
        self.results = None
        self.model_frame = None
        
        self.model = "Select a model"
        
        self.object_list = []
        self.MODE = "measure" # what mode is the app in?]
        self.act_mod_txt_label = self.MODE
        
        self.moving = None # store the details of the sample being moved
        
        self.ACTIVE = -1 # toggle between -1/1 if a line is being drawn

        self.TMP = None # hold the coordinates of the first part of the line being drawn before it gets stored properly
        self.TMP_LINE = None # A temporaruy line before it can be stored in the right place
        
        self.circ_1 = None
        self.circ_2 = None
        self.par_line_1 = None
        self.par_line_2 = None
        

        self.FT_SZ = 22
        
        self.L_WIDTH = 5 # how wide are the lines?
        self.L_COL = "green" # what colour are the measurement lines?
        
        self.ACT_COLOR = "#ff8400"
        self.ser_1_col = "#ff8400"
        self.ser_2_col = "#00bd0d"
        self.ser_3_col = "#9c00ff"
        self.insert_col = "black"
        self.growth_Axis_col = "black"
        
        self.ANNOTE_COL = "yellow" # what colour are the annotation?
        self.active_col = "red" # colourof active measurement line
        self.PROXIMITY = 15 # how close to the points do you need to be to select them
       
        self.lab_x_off = 0
        self.lab_y_off = 0
        
        self.line_cap_len = 25
        self.line_cap_thickness = 5
        self.line_cap = (self.line_cap_thickness, 0, self.line_cap_len)
        
        self.IN_CONFIRM = False # sets whether the increment has been selected
        #GETTING_POINTS = -1 #toggle between -1 and 1 when clicking the first and second point
        self.M1_label_text = [] # will contain the text leabel in the insert frame]
        self.M1 = [0] # get index of the first point
        self.adjusting = -1
        self.adj_point = None

        self.SERIES = []
        self.TMP_SERIES = [] # will be used when modifying a series to insert the extra lines
        self.SERIES_1 = [] # contains the data for each of the measurement series
        self.SERIES_2 = []
        self.SERIES_3 = []
        self.INSERT_SERIES = [] #the series to use to hold measurements that are to be inserted
        self.MEAN_SERIES = [] # arithmetic mean of series 1-3 # not currently used   
       
        self.prev_series = "series_1" # Will contain the name ofthe series previously masured
        self.ACT_SER = "series_1"
        
        self.ANNOTATIONS = [] # store all the annotations here
        self.GROWTH_LINE = [] # the data for the growth line. each index contains [x, y] positions
        self.active_growth_line = [] # stores the temporary line that follows the mouse when drawing a new growth line
        
        self.CALIBRATED = False
        self.CALIBRATION = None
        self.calibration_SF = 1
        self.sb_length = 0 # length of the scale bar
        
        self.toggle_labels = 1
        
        self.anno_frame = None
        self.Anno_text = None
        self.anno_type = "line"
        self.show_anno = -1

        #### AI stuff
        self.selected_model = "final_model"
        self.tmp_points = []
        self.AI_MODE = "delete" 
        self.AI_insert_pos = None
        
        ### crossdating stuff
        self.start_year = 0
        self.assigned = False
        
    def to_dict(self):
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
        
        for i in range(len(self.object_list)):  
            x1.append(self.object_list[i].x1)
            x2.append(self.object_list[i].x2)
            y1.append(self.object_list[i].y1)
            y2.append(self.object_list[i].y2)
            mode.append(self.object_list[i].mode)
            series.append(self.object_list[i].series)
            ob_type.append(regex.sub('', str(self.object_list[i].type)))
            ind.append(self.object_list[i].ind)     
            text.append(self.object_list[i].text)
            px_distance.append(self.object_list[i].px_distance)
            abs_distance.append(self.object_list[i].abs_distance)
            calibrated.append(self.object_list[i].calibrated)
            calibration.append(self.object_list[i].calibration)
            label_text.append(self.object_list[i].label_text)
            year.append(self.object_list[i].year)   
            dated.append(self.object_list[i].dated)
            col.append(self.object_list[i].col)
        
       
        return {
            'id': self.sample_id,
            'age': self.filename,
            
            'calibrated': self.CALIBRATED,
            'calibration': self.CALIBRATION,
            'calibration_sf': self.calibration_SF,
            'sb_length': self.sb_length,
            
            'start_year': self.start_year,
            
            'object_list_x1': x1,            
            'object_list_x2': x2,
            'object_list_y1': y1,            
            'object_list_y2': y2,
            'object_list_mode': mode,
            'object_list_series': series,
            'object_list_ob_type': ob_type,
            'object_list_ind': ind,
            'object_list_text': text,
            'object_list_px_distance': px_distance,
            'object_list_abs_distance': abs_distance,
            'object_list_label_text': label_text,
            'object_list_year': year,
            'object_list_dated': dated,
            'object_list_col': col,            

        }
        
        