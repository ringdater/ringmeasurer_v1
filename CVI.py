import math
import warnings
import tkinter as tk

import numpy as np

from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# from settings_frame import settings_window
from tools import toolbar
from calibration_window import calibration_window
from holder_frame import holder_frame
from results import results
from insert_measurement import insert_measurement
from settings_frame import settings_window

import customtkinter as ctk

import platform # need to get OS name to set the correct mouse bindings

from global_functions import canvas_object, toggle_series, toggle_mode, analyse_axis, run_model

from image_data import image_data

import win_array as WA

from ai_analysis import AI_analysis

# Basis of the CanvasImage function provided through 
# https://stackoverflow.com/questions/41656176/tkinter-canvas-zoom-move-pan


class AutoScrollbar(ttk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        raise tk.TclError('Cannot use place with the widget ' + self.__class__.__name__)

class CanvasImage:
    """ Display and zoom image """
    def __init__(self, placeholder, path, sample_id, win_num):
        """ Initialize the ImageFrame """
        self.system = platform.system() 
        self.IDT = image_data(img_win = int(win_num), 
                                   filename = path,
                                   sample_id = sample_id)
        
        #self.WN = int(win_num) # index to make sure the canvas knows where the ST data is in the array
                
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.__delta = 1.3  # zoom magnitude
        self.__filter = Image.LANCZOS  # 
        self.__previous_state = 0  # previous state of the keyboard
        self.path = path  # path to the image, should be public for outer classes
        # Create ImageFrame in placeholder widget
        self.__imframe = ttk.Frame(placeholder)  # placeholder of the ImageFrame object
        # Vertical and horizontal scrollbars for canvas
        hbar = AutoScrollbar(self.__imframe, orient='horizontal')
        vbar = AutoScrollbar(self.__imframe, orient='vertical')
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Create canvas and bind it with scrollbars. Public for outer classes
        self.canvas = tk.Canvas(self.__imframe, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.__scroll_x)  # bind scrollbars to the canvas
        vbar.configure(command=self.__scroll_y)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.__show_image())  # canvas is resized
        
        self.canvas.bind('<ButtonPress-3>', self.__move_from)  # remember canvas position
        self.canvas.bind('<B3-Motion>',     self.__move_to)  # move canvas to the new position
        
        self.canvas.bind('<MouseWheel>', self.__wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.__wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.__wheel)  # zoom for Linux, wheel scroll up
        
        self.canvas.bind('<Button-1>',   self.CVI_clicked)       
        
        if self.system == "Darwin":
            self.canvas.bind('<ButtonPress-2>',   self.__move_from)
            self.canvas.bind('<B2-Motion>',     self.__move_to)
            self.canvas.bind('<B1-Motion>',     self.adjust_point)
            
        self.canvas.bind("<Motion>",     self.CVI_mouse_move)
        
        # self.canvas.bind('<Delete>',  self.CVI_delete_object)
        
        self.canvas.bind("<BackSpace>", self.delete_last)
        
        self.canvas.bind('<B1-Motion>',  self.adjust_point)
        
        self.canvas.bind('<Shift-Button-1>', self.delete_object)
        
        self.canvas.bind('<Control-Button-1>', self.ctrl_click)
        self.canvas.bind('<Control-KeyPress>', self.ctrl_click)
        
        self.canvas.bind('<ButtonRelease-1>', self.end_adjust)
        self.canvas.bind("<KeyRelease>", self.end_adjust)
        
        self.canvas.bind('<Double-Button-1>', self.end_line)
        
        ## mac specific bindings
        self.canvas.bind('<Shift-MouseWheel>', self.__wheel)
        
        # Handle keystrokes in idle mode, because program slows down on a weak computers,
        # when too many key stroke events in the same time
        self.canvas.bind('<Key>', lambda event: self.canvas.after_idle(self.__keystroke, event))
        # Decide if this image huge or not
        self.__huge = False  # huge or not
        self.__huge_size = 1400000  # define size of the huge image
        self.__band_width = 1024  # width of the tile band
        Image.MAX_IMAGE_PIXELS = 10000000000  # suppress DecompressionBombError for the big image
        with warnings.catch_warnings():  # suppress DecompressionBombWarning
            warnings.simplefilter('ignore')
            self.__image = Image.open(self.path)  # open image, but down't load it
        self.imwidth, self.imheight = self.__image.size  # public for outer classes
        if self.imwidth * self.imheight > self.__huge_size * self.__huge_size and \
           self.__image.tile[0][0] == 'raw':  # only raw images could be tiled
            self.__huge = True  # image is huge
            self.__offset = self.__image.tile[0][2]  # initial tile offset
            self.__tile = [self.__image.tile[0][0],  # it have to be 'raw'
                           [0, 0, self.imwidth, 0],  # tile extent (a rectangle)
                           self.__offset,
                           self.__image.tile[0][3]]  # list of arguments to the decoder
        self.__min_side = min(self.imwidth, self.imheight)  # get the smaller image side
        # Create image pyramid
        self.__pyramid = [self.smaller()] if self.__huge else [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.__ratio = max(self.imwidth, self.imheight) / self.__huge_size if self.__huge else 1.0
        self.__curr_img = 0  # current image from the pyramid
        self.__scale = self.imscale * self.__ratio  # image pyramide scale
        self.__reduction = 2  # reduction degree of image pyramid
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:  # top pyramid image is around 512 pixels in size
            w /= self.__reduction  # divide on reduction degree
            h /= self.__reduction  # divide on reduction degree
            self.__pyramid.append(self.__pyramid[-1].resize((int(w), int(h)), self.__filter))
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
        self.__show_image()  # show image on the canvas
        self.canvas.focus_set()  # set focus on the canvas
        
        self.IDT.TOP_LEFT = self.canvas.create_oval(0, 0, -1,-1)
        # turn on the toolbar

        # initialise frames and windows
        self.IDT.toolbar = toolbar(self.canvas, self.IDT.img_win)             
        self.IDT.calib_frame = calibration_window(self.canvas, self.IDT.img_win)
        
        self.IDT.toolbar.sample_label.configure(text = "Loaded image: " + sample_id)
        self.IDT.toolbar.toggle()
        
        self.IDT.results = results(placeholder, self.IDT.img_win, self.IDT.sample_id)
        #self.IDT.error_frame = holder_frame(self.canvas, self.IDT.img_win)
        
        self.IDT.insert_frame = insert_measurement(self.canvas, self.IDT.img_win)
        
        self.IDT.settings_window = settings_window(self.canvas, self.IDT.img_win)
        
        self.IDT.model_frame = AI_analysis(self.IDT.img_win, self.canvas, self.path)
        
        
       # 
        
        #print("canvas WA len = " + str(len(WA.wins)))
        #WS.DT[self.WN].restart_frame = restart_frame(self.canvas, placeholder)


    def smaller(self):
        """ Resize image proportionally and return smaller image """
        w1, h1 = float(self.imwidth), float(self.imheight)
        w2, h2 = float(self.__huge_size), float(self.__huge_size)
        aspect_ratio1 = w1 / h1
        aspect_ratio2 = w2 / h2  # it equals to 1.0
        if aspect_ratio1 == aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(w2)  # band length
        elif aspect_ratio1 > aspect_ratio2:
            image = Image.new('RGB', (int(w2), int(w2 / aspect_ratio1)))
            k = h2 / w1  # compression ratio
            w = int(w2)  # band length
        else:  # aspect_ratio1 < aspect_ration2
            image = Image.new('RGB', (int(h2 * aspect_ratio1), int(h2)))
            k = h2 / h1  # compression ratio
            w = int(h2 * aspect_ratio1)  # band length
        i, j, n = 0, 1, round(0.5 + self.imheight / self.__band_width)
        while i < self.imheight:
            print('\rOpening image: {j} from {n}'.format(j=j, n=n), end='')
            band = min(self.__band_width, self.imheight - i)  # width of the tile band
            self.__tile[1][3] = band  # set band width
            self.__tile[2] = self.__offset + self.imwidth * i * 3  # tile offset (3 bytes per pixel)
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]  # set tile
            cropped = self.__image.crop((0, 0, self.imwidth, band))  # crop tile band
            image.paste(cropped.resize((w, int(band * k)+1), self.__filter), (0, int(i * k)))
            i += band
            j += 1
        print('\r' + 30*' ' + '\r', end='')  # hide printed string
        return image

    def redraw_figures(self):
        """ Dummy function to redraw figures in the children classes """
        pass

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        self.__imframe.grid(**kw)  # place CanvasImage widget on the grid
        self.__imframe.grid(sticky='nswe')  # make frame container sticky
        self.__imframe.rowconfigure(0, weight=1)  # make canvas expandable
        self.__imframe.columnconfigure(0, weight=1)

    def pack(self, **kw):
        """ Exception: cannot use pack with this widget """
        raise Exception('Cannot use pack with the widget ' + self.__class__.__name__)

    def place(self, **kw):
        """ Exception: cannot use place with this widget """
        raise Exception('Cannot use place with the widget ' + self.__class__.__name__)

    # noinspection PyUnusedLocal
    def __scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.__show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def __scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.__show_image()  # redraw the image

    def __show_image(self):
        """ Show image on the Canvas. Implements correct image zoom almost like in Google Maps """
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            if self.__huge and self.__curr_img < 0:  # show huge image
                h = int((y2 - y1) / self.imscale)  # height of the tile band
                self.__tile[1][3] = h  # set the tile band height
                self.__tile[2] = self.__offset + self.imwidth * int(y1 / self.imscale) * 3
                self.__image.close()
                self.__image = Image.open(self.path)  # reopen / reset image
                self.__image.size = (self.imwidth, h)  # set size of the tile band
                self.__image.tile = [self.__tile]
                image = self.__image.crop((int(x1 / self.imscale), 0, int(x2 / self.imscale), h))
            else:  # show normal image
                image = self.__pyramid[max(0, self.__curr_img)].crop(  # crop current img from pyramid
                                    (int(x1 / self.__scale), int(y1 / self.__scale),
                                     int(x2 / self.__scale), int(y2 / self.__scale)))
            #
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1)), self.__filter))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


    def __move_from(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area

    def __wheel(self, event):
        """ Zoom with mouse wheel """
        
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        
       
        if self.IDT.TMP != None:
            temp_TMP = self.absolute(self.IDT.TMP[0], self.IDT.TMP[1])
        
        if self.outside(x, y): return  # zoom only inside image area
                
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120 or event.delta == -1:  # scroll down, smaller
            if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120 or event.delta == 1:  # scroll up, bigger
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        self.redraw_figures()  # method for child classes
        self.__show_image()
        
        if self.IDT.TMP != None:
            temp_TMP = self.convert_to_canvas(temp_TMP[0], temp_TMP[1])
            self.IDT.TMP = temp_TMP

    def __keystroke(self, event):
        """ Scrolling with the keyboard.
            Independent from the language of the keyboard, CapsLock, <Ctrl>+<key>, etc. """
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            pass  # do nothing if Control key is pressed
        else:
            self.__previous_state = event.state  # remember the last keystroke state
            # Up, Down, Left, Right keystrokes
            if event.keycode in [68, 39, 102]:  # scroll right: keys 'D', 'Right' or 'Numpad-6'
                self.__scroll_x('scroll',  1, 'unit', event=event)
            elif event.keycode in [65, 37, 100]:  # scroll left: keys 'A', 'Left' or 'Numpad-4'
                self.__scroll_x('scroll', -1, 'unit', event=event)
            elif event.keycode in [87, 38, 104]:  # scroll up: keys 'W', 'Up' or 'Numpad-8'
                self.__scroll_y('scroll', -1, 'unit', event=event)
            elif event.keycode in [83, 40, 98]:  # scroll down: keys 'S', 'Down' or 'Numpad-2'
                self.__scroll_y('scroll',  1, 'unit', event=event)

    def crop(self, bbox):
        """ Crop rectangle from the image and return it """
        if self.__huge:  # image is huge and not totally in RAM
            band = bbox[3] - bbox[1]  # width of the tile band
            self.__tile[1][3] = band  # set the tile height
            self.__tile[2] = self.__offset + self.imwidth * bbox[1] * 3  # set offset of the band
            self.__image.close()
            self.__image = Image.open(self.path)  # reopen / reset image
            self.__image.size = (self.imwidth, band)  # set size of the tile band
            self.__image.tile = [self.__tile]
            return self.__image.crop((bbox[0], 0, bbox[2], band))
        else:  # image is totally in RAM
            return self.__pyramid[0].crop(bbox)

    def destroy(self):
        """ ImageFrame destructor """
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)  # close all pyramid images
        del self.__pyramid[:]  # delete pyramid list
        del self.__pyramid  # delete pyramid variable
        self.canvas.destroy()
        self.__imframe.destroy()

###############################################################################

    def convert_to_canvas(self, x, y):
        top_left_coords = self.canvas.coords(self.IDT.TOP_LEFT)
        cx = top_left_coords[0] + (x * self.imscale)
        cy = top_left_coords[1] + (y * self.imscale)
        return([cx, cy])
    
    # get the coordinates on the original image
    def absolute(self, x, y):
        top_left_coords = self.canvas.coords(self.IDT.TOP_LEFT)
        x1 = (x - top_left_coords[0])/self.imscale
        y1 = (y - top_left_coords[1])/self.imscale
        return([x1, y1]) 

    def add_to_series(self):
        if len(self.IDT.object_list) == 0: return
    
        if self.IDT.object_list[len(self.IDT.object_list) - 1].series == "series_1":
            self.IDT.SERIES_1.append(self.IDT.object_list[len(self.IDT.object_list) - 1])
        
        if self.IDT.object_list[len(self.IDT.object_list) - 1].series == "series_2":
            self.IDT.SERIES_2.append(self.IDT.object_list[len(self.IDT.object_list) - 1])
        
        if self.IDT.object_list[len(self.IDT.object_list) - 1].series == "series_3":
            self.IDT.SERIES_3.append(self.IDT.object_list[len(self.IDT.object_list) - 1])
        
        if self.IDT.object_list[len(self.IDT.object_list) - 1].series == "insert":
            self.IDT.INSERT_SERIES.append(self.IDT.object_list[len(self.IDT.object_list) - 1])    
        

    def CVI_clicked(self, event):        
        if  self.IDT.MODE == "measure":
            if  self.IDT.ACT_SER == "series_1":
                self.IDT.ACT_COLOR = self.IDT.ser_1_col
            if  self.IDT.ACT_SER == "series_2":
                self.IDT.ACT_COLOR = self.IDT.ser_2_col
            if self.IDT.ACT_SER == "series_3":
                self.IDT.ACT_COLOR = self.IDT.ser_3_col                
            self.draw_line(event)  
            
        if  self.IDT.MODE == "ref_point":
            self.IDT.ACT_COLOR = "black"
            self.draw_point(event)
            
        if  self.IDT.MODE == "drill_point":
            self.IDT.ACT_COLOR = "green"
            self.draw_point(event)
            
        if  self.IDT.MODE == "drill_line":
            self.IDT.ACT_COLOR = "green"
            self.draw_line(event)
            
            
        if self.IDT.MODE == "ai":
            self.IDT.ACTIVE = 1
            self.IDT.ACT_COLOR = "black"
            self.draw_Active_growth_line(event)
            self.draw_point(event)
        
        
        if  self.IDT.MODE == "anno":
            self.IDT.ACT_COLOR =  self.IDT.ANNOTE_COL
            if  self.IDT.anno_type == "line":            
                self.draw_line(event)
            if  self.IDT.anno_type == "dot":
                self.draw_point(event)
            if  self.IDT.anno_type == "text":
                self.draw_text(event)
            if  self.IDT.anno_type == "growth_Axis":
                self.draw_growth_axis(event)
                
        if  self.IDT.MODE == "calibrate":
            self.IDT.ACT_COLOR = "blue"
            self.draw_line(event) 
        
        if  self.IDT.MODE == "insert" and len(self.IDT.M1) != 2:
            self.get_points(event, self.hover_over(event))     
        
        if self.IDT.MODE == "insert" and len(self.IDT.M1) == 2:
            if self.IDT.ACT_SER == "insert":
                self.IDT.ACT_COLOR = self.IDT.insert_col
                self.draw_line(event) 

    def hover_over(self, event):
        if len(self.IDT.object_list) == 0: return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)  
        
        prox = self.IDT.PROXIMITY * (1/self.imscale)
        obj = None
        end = None
        ser = None
        
        for i in range(len(self.IDT.object_list)):
            #ßprint(type(self.IDT.object_list[i].object))
            
            if isinstance(self.IDT.object_list[i].object, int): 
                pos = self.canvas.coords(self.IDT.object_list[i].object)                         
            else:
                pos = self.canvas.coords(self.IDT.object_list[i].object[0])                
                    
            if (self.IDT.object_list[i].type == "line" or 
                self.IDT.object_list[i].type == "dot"):
                
                pos = self.canvas.coords(self.IDT.object_list[i].object)
                
                if (x > pos[0] - prox and 
                    x < pos[0] + prox and
                    y > pos[1] - prox and
                    y < pos[1] + prox):                 
                        self.canvas.itemconfig(self.IDT.object_list[i].object, fill="blue") 
                        obj = i
                        end = 1
                        ser = self.IDT.object_list[i].series
                        return [obj, end, ser]
                elif (x > pos[2] - prox and 
                    x < pos[2] + prox and
                    y > pos[3] - prox and
                    y < pos[3] + prox):                 
                        self.canvas.itemconfig(self.IDT.object_list[i].object, fill="blue") 
                        obj = i
                        end = 2  
                        ser = self.IDT.object_list[i].series
                        return [obj, end, ser]
                else:
                    self.canvas.itemconfig(self.IDT.object_list[i].object, fill= self.IDT.object_list[i].col)
            
            elif self.IDT.object_list[i].type == "text":
                if (x > pos[0] - prox and 
                    x < pos[0] + prox and
                    y > pos[1] - prox and
                    y < pos[1] + prox):                 
                        self.canvas.itemconfig(self.IDT.object_list[i].object, fill="blue") 
                        obj = i
                        end = 1
                        return [obj, end, None]
                else:
                    self.canvas.itemconfig(self.IDT.object_list[i].object, fill= self.IDT.object_list[i].col)
                    
            
            elif self.IDT.object_list[i].type == "ai_point":
                 pos = self.canvas.coords(self.IDT.object_list[i].object)
                 
                 if (x > pos[0] - prox and 
                     x < pos[0] + prox and
                     y > pos[1] - prox and
                     y < pos[1] + prox):                 
                         self.canvas.itemconfig(self.IDT.object_list[i].object, fill="blue") 
                         obj = i
                         end = 1
                         ser = "ai_point"
                         return [obj, end, ser]
                 elif (x > pos[2] - prox and 
                     x < pos[2] + prox and
                     y > pos[3] - prox and
                     y < pos[3] + prox):                 
                         self.canvas.itemconfig(self.IDT.object_list[i].object, fill="blue") 
                         obj = i
                         end = 2  
                         ser = self.IDT.object_list[i].series
                         return [obj, end, ser]
                 else:
                     self.canvas.itemconfig(self.IDT.object_list[i].object, fill= self.IDT.object_list[i].col)
             
                
            elif self.IDT.object_list[i].type == "drill_line": 
                
                pos = self.canvas.coords(self.IDT.object_list[i].object[0])                
                #print(pos)
                
                if (x > pos[0] - prox and 
                    x < pos[0] + prox and
                    y > pos[1] - prox and
                    y < pos[1] + prox):  
                                        
                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[0], 
                                           fill= "blue")                                  
                    self.canvas.itemconfig(self.IDT.object_list[i].object[1], 
                                           outline= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[2], 
                                           outline= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[3], 
                                           fill= "blue")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[4], 
                                           fill= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[5], 
                                           outline= "blue")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[6], 
                                           outline= "blue")
                    
                    obj = i
                    end = 1
                    ser = "drill_line"
                    return [obj, end, ser]
                
                elif (x > pos[2] - prox and 
                    x < pos[2] + prox and
                    y > pos[3] - prox and
                    y < pos[3] + prox): 
                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[0], 
                                           fill= "blue")                                  
                    self.canvas.itemconfig(self.IDT.object_list[i].object[1], 
                                           outline= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[2], 
                                           outline= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[3], 
                                           fill= "blue")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[4], 
                                           fill= "blue")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[5], 
                                           outline= "blue")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[6], 
                                           outline= "blue")
                    
                    obj = i
                    end = 2
                    ser = "drill_line"
                    return [obj, end, ser]
                
                else:
                    self.canvas.itemconfig(self.IDT.object_list[i].object[0], 
                                           fill= "green")                                  
                    self.canvas.itemconfig(self.IDT.object_list[i].object[1], 
                                           outline= "green")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[2], 
                                           outline= "green")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[3], 
                                           fill= "green")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[4], 
                                           fill= "green")                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[5], 
                                           outline= "green")
                    self.canvas.itemconfig(self.IDT.object_list[i].object[6], 
                                           outline= "green")
                    
            elif self.IDT.object_list[i].type == "drill_point":   
                if (x > pos[0] - prox and 
                    x < pos[0] + prox and
                    y > pos[1] - prox and
                    y < pos[1] + prox):                 
                    self.canvas.itemconfig(self.IDT.object_list[i].object[0],
                                           fill = "blue",
                                            outline= "blue")  
                    self.canvas.itemconfig(self.IDT.object_list[i].object[1],                                           
                                            outline= "blue") 
                    obj = i
                    end = 1
                    ser = "drill_point"
                    return [obj, end, ser]
                else:                    
                    self.canvas.itemconfig(self.IDT.object_list[i].object[0],
                                           fill = "green",
                                            outline= "green")  
                    self.canvas.itemconfig(self.IDT.object_list[i].object[1],                                           
                                            outline= "green") 
                        
            elif self.IDT.object_list[i].type == "reference":   
                 if (x > pos[0] - prox and 
                     x < pos[0] + prox and
                     y > pos[1] - prox and
                     y < pos[1] + prox):                 
                     
                    self.canvas.itemconfig(self.IDT.object_list[i].object, 
                                            outline= "blue")
                    obj = i
                    end = 1
                    ser = "reference"
                    return [obj, end, ser]
                 else:                      
                    self.canvas.itemconfig(self.IDT.object_list[i].object, 
                                            outline= "green")  
                    
                    
            

    def CVI_mouse_move(self, event):    
        if self.IDT.MODE == "ai" and self.IDT.ACTIVE == 1:
            self.draw_Active_growth_line(event)
        
        elif self.IDT.ACTIVE == 1:    
            self.draw_active_line(event)  
        # elif self.IDT.anno_type == "growth_Axis" and len(self.IDT.GROWTH_LINE) >= 1:
        #     self.draw_active_line(event)
        
        self.hover_over(event) 

    def CVI_adjust_point(self, event):
        self.adjust_point(event)

    # dont delete this
   # def shift_click(self, event):
   #     pass
   #     #delete_object(event, self.WN)
        
    def ctrl_click(self, event):
        self.IDT.adjusting = 1
        
    # defines how big the diameter or total width for the drill bit lines
# takes the size of the drill bit in microns    
    def drill_offset(self, size):
        offset = 0
        print(" ")
        abso_pixel = size * self.IDT.calibration_SF 
        print("abso_pixel = " + str(abso_pixel))         
        print("sf = " + str(self.IDT.calibration_SF))         
        print("imscale = "+ str(self.imscale))
        p1 = self.convert_to_canvas(0, 0)
        p2 = self.convert_to_canvas(abso_pixel, 0)
        print("p1: " + str(p1[0]) + " p2: " + str(p2[0]) )
        print("p2-p1 = " + str(p2[0] - p1[0]))
        
        offset = p2[0] - p1[0]
        
        #offset = canvas_size[0]
        return offset 
        
    
    def draw_active_line(self, event):    
        if self.IDT.MODE != "drill_line":
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.delete(self.IDT.TMP_LINE)     
            if self.IDT.TMP != None:
                self.IDT.TMP_LINE = self.canvas.create_line(self.IDT.TMP[0], self.IDT.TMP[1],
                                                    x, y,
                                                    fill = self.IDT.active_col, 
                                                    width = self.IDT.L_WIDTH,
                                                    arrow = tk.BOTH,
                                                    arrowshape = self.IDT.line_cap)
        
        if self.IDT.MODE == "drill_line":

            # try:
            #     float(self.IDT.toolbar.drill_size_entry.get())
            #     messagebox.showinfo("Success", "Numeric value entered.")
            # except ValueError:
            #     messagebox.showerror("Error", "Please enter drill bit size!")
            #     self.IDT.ACTIVE = -1
            #     return
            
            
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            
            # Delete temporary lines if they are still on the image
            self.canvas.delete(self.IDT.TMP_LINE)   
            self.canvas.delete(self.IDT.circ_1) 
            self.canvas.delete(self.IDT.circ_2) 
            self.canvas.delete(self.IDT.par_line_1) 
            self.canvas.delete(self.IDT.par_line_2) 
            
            if self.IDT.TMP != None:
                self.IDT.TMP_LINE = self.canvas.create_line(self.IDT.TMP[0], self.IDT.TMP[1],
                                                    x, y,
                                                    fill = self.IDT.active_col, 
                                                    width = self.IDT.L_WIDTH)
                
                
                drill_bit = self.IDT.toolbar.drill_size_entry.get()
                if drill_bit.isdigit():
                    drill_bit = int(drill_bit)
                    drill_bit = self.drill_offset(drill_bit)
                else:    
                    drill_bit = 5
               
                # draw end circles
                end1_coords = self.get_circle_coordinates(self.IDT.TMP[0], self.IDT.TMP[1], 1/self.imscale, drill_bit)
                end2_coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
                
                self.IDT.circ_1 = self.canvas.create_oval(end1_coords[0],end1_coords[1],
                                                            end1_coords[2],end1_coords[3],
                                                            outline=self.IDT.ACT_COLOR,
                                                            width=self.IDT.L_WIDTH)
                
                self.IDT.circ_2 = self.canvas.create_oval(end2_coords[0],end2_coords[1],
                                                        end2_coords[2],end2_coords[3],
                                                        outline=self.IDT.ACT_COLOR,
                                                        width=self.IDT.L_WIDTH)
                ## draw parralel lines                               
                
                offset = drill_bit / (1/self.imscale)
                left_line, right_line = self.create_parallel_lines(self.IDT.TMP[0], self.IDT.TMP[1], x, y, offset)
                
                self.IDT.par_line_1 = self.canvas.create_line(left_line[0], left_line[1],
                                        left_line[2],left_line[3],
                                        fill=self.IDT.ACT_COLOR, 
                                        width=self.IDT.L_WIDTH)  
                
                self.IDT.par_line_2 = self.canvas.create_line(right_line[0], right_line[1],
                                        right_line[2], right_line[3],
                                        fill=self.IDT.ACT_COLOR, 
                                        width=self.IDT.L_WIDTH) 
                

                    
            
            

    def draw_line(self, event):
        
        #get coords of where the mouse was clikced in the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)        
        # to start a measurement temporarily store the coordinates where the mouse was clicked
        if self.IDT.ACTIVE == -1:
            self.IDT.TMP = [x,y]   
        
        # if a measurement has already been started, create  a perminent line and store the coordinates
        else:       
            p1 = self.absolute(self.IDT.TMP[0], self.IDT.TMP[1])
            p2 = self.absolute(x, y)       
            
            ind = None
            #get the index for the series
            if self.IDT.MODE == "measure":
                if self.IDT.ACT_SER == "series_1":
                    ind = len(self.IDT.SERIES_1) 
                if self.IDT.ACT_SER == "series_2":
                    ind = len(self.IDT.SERIES_2) 
                if self.IDT.ACT_SER == "series_3":
                    ind = len(self.IDT.SERIES_3) 
                if self.IDT.ACT_SER == "insert" and len(self.IDT.M1) == 2:
                    #ind = len(ST.INSERT_SERIES) 
                    self.IDT.ACT_COLOR = self.IDT.insert_col
                    ind = self.IDT.object_list[self.IDT.M1[1]].ind + len(self.IDT.INSERT_SERIES)
            
            if self.IDT.MODE == "drill_line":   
                drill_lines = 0
                for i in range(len(self.IDT.object_list)):
                      if self.IDT.object_list[i].type == "drill_line":
                          drill_lines = drill_lines + 1
                ind = drill_lines
                    
            self.IDT.object_list.append(canvas_object(p1[0], p1[1],
                                                p2[0], p2[1],
                                                self.IDT.MODE, 
                                                self.IDT.ACT_SER, 
                                                ind))
            self.IDT.object_list[len(self.IDT.object_list)-1].obj_index = (len(self.IDT.object_list) - 1)
            self.IDT.object_list[len(self.IDT.object_list)-1].type = "line"
            self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
            
            if self.IDT.assigned ==False:
                self.IDT.object_list[len(self.IDT.object_list)-1].year = ind 
            else:
                self.IDT.object_list[len(self.IDT.object_list)-1].year = ind + self.IDT.start_year
            
            if self.IDT.MODE != "drill_line":
                self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_line(self.IDT.TMP[0], self.IDT.TMP[1],
                                                                                             x, y,
                                                                                             fill=self.IDT.ACT_COLOR, 
                                                                                             width=self.IDT.L_WIDTH,
                                                                                             arrow=tk.BOTH,
                                                                                             arrowshape = self.IDT.line_cap)        
                
            if self.IDT.MODE == "drill_line":
                self.IDT.object_list[len(self.IDT.object_list)-1].series = "drill_line"
                self.IDT.object_list[len(self.IDT.object_list)-1].type = "drill_line"
                
                drill_bit = self.IDT.toolbar.drill_size_entry.get()
                if drill_bit.isdigit():
                    drill_bit = int(drill_bit)
                    drill_bit = self.drill_offset(drill_bit)
                else:    
                    drill_bit = 5
                
                # draw end circles
                end1_coords = self.get_circle_coordinates(self.IDT.TMP[0], self.IDT.TMP[1], 1/self.imscale, drill_bit)
                end2_coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object = []
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_line(self.IDT.TMP[0], self.IDT.TMP[1],
                                                                                             x, y,
                                                                                             fill=self.IDT.ACT_COLOR, 
                                                                                             width=self.IDT.L_WIDTH))
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(end1_coords[0],end1_coords[1],
                                                                                        end1_coords[2],end1_coords[3],
                                                                                        outline=self.IDT.ACT_COLOR,
                                                                                        width=self.IDT.L_WIDTH))
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(end2_coords[0],end2_coords[1],
                                                                                        end2_coords[2],end2_coords[3],
                                                                                        outline=self.IDT.ACT_COLOR,
                                                                                        width=self.IDT.L_WIDTH))
                ## draw parralel lines
                #drill_bit = int(self.IDT.toolbar.drill_size_entry.get())
                offset = drill_bit/ (1/self.imscale)
                left_line, right_line = self.create_parallel_lines(self.IDT.TMP[0], self.IDT.TMP[1], x, y, offset)
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_line(left_line[0], left_line[1],
                                                                                left_line[2],left_line[3],
                                                                                fill=self.IDT.ACT_COLOR, 
                                                                                width=self.IDT.L_WIDTH))  
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_line(right_line[0], right_line[1],
                                                                                right_line[2], right_line[3],
                                                                                fill=self.IDT.ACT_COLOR, 
                                                                                width=self.IDT.L_WIDTH)) 
                
                # add centre points to help with adjustments
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(self.IDT.TMP[0] + 5, self.IDT.TMP[1] + 5,
                                                                                        self.IDT.TMP[0] - 5, self.IDT.TMP[1] - 5,
                                                                                        fill =self.IDT.ACT_COLOR))
                
                self.IDT.object_list[len(self.IDT.object_list)-1].object.append( self.canvas.create_oval(x + 5, y + 5,
                                                                                        x - 5, y - 5,
                                                                                        fill = self.IDT.ACT_COLOR))
                    
                self.canvas.delete(self.IDT.TMP_LINE)   
                self.canvas.delete(self.IDT.circ_1) 
                self.canvas.delete(self.IDT.circ_2) 
                self.canvas.delete(self.IDT.par_line_1) 
                self.canvas.delete(self.IDT.par_line_2) 
            
            px_distance = math.dist((self.IDT.TMP[0], self.IDT.TMP[1]), 
                                 (x, y)) * (1/self.imscale) 
            
            if self.IDT.MODE == "measure" or self.IDT.MODE == "calibrate":                                                                 
                self.IDT.object_list[len(self.IDT.object_list)-1].px_distance = px_distance
            
            if self.IDT.CALIBRATED == True:
                self.IDT.object_list[len(self.IDT.object_list)-1].px_distance = px_distance
                self.IDT.object_list[len(self.IDT.object_list)-1].calibrated = True
                self.IDT.object_list[len(self.IDT.object_list)-1].calibration = self.IDT.calibration_SF
                self.IDT.object_list[len(self.IDT.object_list)-1].abs_distance = self.IDT.object_list[len(self.IDT.object_list)-1].px_distance * self.IDT.calibration_SF
            
            if self.IDT.CALIBRATED == False: 
               self.IDT.object_list[len(self.IDT.object_list)-1].abs_distance = self.IDT.object_list[len(self.IDT.object_list)-1].px_distance
                
            if self.IDT.MODE == "measure":
                coords = self.canvas.coords(self.IDT.object_list[len(self.IDT.object_list)-1].object)
                label_x = (coords[0] + coords[2]) / 2 + self.IDT.lab_x_off
                label_y = (coords[1] + coords[3]) / 2 + self.IDT.lab_y_off                
                self.IDT.object_list[len(self.IDT.object_list)-1].label_text = self.IDT.object_list[len(self.IDT.object_list)-1].year
                self.IDT.object_list[len(self.IDT.object_list)-1].label = self.canvas.create_text(label_x, label_y,
                                                                                            text= self.IDT.object_list[len(self.IDT.object_list)-1].label_text, 
                                                                                            fill="black", 
                                                                                            font=('Helvetica 15 bold'))
               
                self.IDT.object_list[len(self.IDT.object_list)-1].label_visible = True # is the label visible or not
               
                self.add_to_series()
                self.update_results_window()
                
            if self.IDT.MODE == "anno" or self.IDT.MODE == "calibrate":
                self.IDT.object_list[len(self.IDT.object_list)-1].series = None
                
            self.IDT.TMP = None
            self.canvas.delete(self.IDT.TMP_LINE)
            self.IDT.TMP_LINE = None
                
                    
        #self.canvas.delete(self.IDT.TMP_LINE)         
        self.IDT.ACTIVE = - self.IDT.ACTIVE
        
        
    # def draw_growth_axis(self, event):
    #     #get coords of where the mouse was clikced in the canvas
    #     x = self.canvas.canvasx(event.x)
    #     y = self.canvas.canvasy(event.y)        
    #     # to start a measurement temporarily store the coordinates where the mouse was clicked
    #     #if self.IDT.ACTIVE == -1:
    #     if len(self.IDT.GROWTH_LINE) == 0:            
    #         #self.IDT.TMP = self.absolute(x,y)
    #         self.IDT.TMP = [x,y]            
    #         #x, y = self.absolute(x, y)
    #         self.IDT.GROWTH_LINE.append(self.absolute(x, y))
    #     else:
    #         #tmp = self.IDT.GROWTH_LINE[len(self.IDT.GROWTH_LINE)-1]
    #         #self.IDT.TMP = self.convert_to_canvas(tmp[0], tmp[1])
    #         tmp = self.IDT.GROWTH_LINE[len(self.IDT.GROWTH_LINE)-1]
    #         self.IDT.TMP = self.convert_to_canvas(tmp[0], tmp[1])            
            
    #     # if a measurement has already been started, create  a perminent line and store the coordinates
    #     #else:       
    #     p1 = [self.IDT.TMP[0], self.IDT.TMP[1]]
    #     p2 = [x, y]      
 
    #     ind = None                                 
                
    #     self.IDT.object_list.append(canvas_object(p1[0], p1[1],
    #                                         p2[0], p2[1],
    #                                         self.IDT.MODE, 
    #                                         "growth_axis", 
    #                                         ind))
        
    #     self.IDT.object_list[len(self.IDT.object_list)-1].obj_index = (len(self.IDT.object_list) - 1)
    #     self.IDT.object_list[len(self.IDT.object_list)-1].type = "line"
    #     self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.growth_Axis_col
        
    #     size = 5
    #     self.IDT.object_list[len(self.IDT.object_list)-1].point1 = self.canvas.create_oval(self.IDT.TMP[0] - size, self.IDT.TMP[1]  - size, 
    #                                                                                 self.IDT.TMP[0] + size, self.IDT.TMP[1]  + size,
    #                                                                                 fill = self.IDT.growth_Axis_col)
        
    #     self.IDT.object_list[len(self.IDT.object_list)-1].point2 = self.canvas.create_oval(x - size, y  - size, 
    #                                                                                 x + size, y + size,
    #                                                                                 fill = self.IDT.growth_Axis_col)
        
    #     self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_line(self.IDT.TMP[0], self.IDT.TMP[1],
    #                                                                                  x, y,
    #                                                                                  fill=self.IDT.growth_Axis_col, 
    #                                                                                  width=self.IDT.L_WIDTH)        
                        
    #     self.IDT.object_list[len(self.IDT.object_list)-1].series = "growth_axis"
        
    #     self.IDT.GROWTH_LINE.append(self.absolute(x, y))
       
    #     self.IDT.TMP = p2
          
    #     self.canvas.delete(self.IDT.TMP_LINE)         
    #     self.IDT.ACTIVE = - self.IDT.ACTIVE
      
    def end_line(self, event):
        self.IDT.ACTIVE = -1
        self.canvas.delete(self.IDT.TMP_LINE) 
        self.canvas.delete(self.IDT.active_growth_line)
        #toggle_mode("measure", self.IDT.img_win)
        self.IDT.TMP = None
        self.IDT.TMP_LINE = None
        
    def get_circle_coordinates(self, center_x, center_y, scale, true_size):
        # Calculate the radius of the circle in pixels
        radius_pixels = true_size / scale
    
        # Calculate coordinates of the circle boundaries
        x1_circle = center_x - radius_pixels
        y1_circle = center_y - radius_pixels
        x2_circle = center_x + radius_pixels
        y2_circle = center_y + radius_pixels

        return x1_circle, y1_circle, x2_circle, y2_circle
        
    def draw_point(self, event):    
          
        #get coords of where the mouse was clikced in the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        size = 5
        
        p1 = self.absolute(x, y)       
        
        # to start a measurement temporarily store the coordinates where the mouse was clicked
      
        self.IDT.object_list.append(canvas_object(p1[0] - size, p1[1] - size, 
                                            p1[0] + size, p1[1] + size,
                                            self.IDT.MODE, 
                                            None, 
                                            len(self.IDT.object_list)))
        self.IDT.object_list[len(self.IDT.object_list)-1].obj_index = len(self.IDT.object_list)-1
        
        if  self.IDT.MODE == "ref_point":
            self.IDT.object_list[len(self.IDT.object_list)-1].type = "reference"
            size = 5
            self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_oval(x - size, y - size, 
                                                                                    x + size, y + size,
                                                                                    outline=self.IDT.ACT_COLOR,
                                                                                    width=2)
            self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
        
        if  self.IDT.MODE == "drill_point":
            
            self.IDT.object_list[len(self.IDT.object_list)-1].type = "drill_point"
            self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
            self.IDT.object_list[len(self.IDT.object_list)-1].object = []
            size = 5
            self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(x - size, y - size, 
                                                                                       x + size, y + size,
                                                                                        fill = self.IDT.ACT_COLOR))
            drill_bit = self.IDT.toolbar.drill_size_entry.get()
            if drill_bit.isdigit():
                drill_bit = int(drill_bit)
            else:    
                drill_bit = 5
            
            coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
            
            self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(coords[0],coords[1],
                                                                                    coords[2],coords[3],
                                                                                    outline=self.IDT.ACT_COLOR,
                                                                                    width=2))
            
        
        if  self.IDT.MODE == "anno":
            self.IDT.object_list[len(self.IDT.object_list)-1].type = "dot"
            size = 5
            self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_oval(x - size, y - size, 
                                                                                        x + size, y + size,
                                                                                        fill = self.IDT.ACT_COLOR)
        
        
        if self.IDT.MODE == "ai":
            self.IDT.object_list[len(self.IDT.object_list)-1].type = "ai_point"
            size = 5
            self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_oval(x - size, y - size, 
                                                                                        x + size, y + size,
                                                                                        fill = self.IDT.ACT_COLOR)
            self.draw_growth_line()            
        
        self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
        
    
    def draw_growth_line(self):
        line_points = []
        
        for i in range(len(self.IDT.GROWTH_LINE)):
            self.canvas.delete(self.IDT.GROWTH_LINE[i])
        
        for i in range(len(self.IDT.object_list)):
            if self.IDT.object_list[i].type == "ai_point":
                line_points.append(self.IDT.object_list[i])
    
        if len(line_points) > 1:
            for i in range(len(line_points)-1):
                p1 = self.canvas.coords(line_points[i].object)
                p2 = self.canvas.coords(line_points[i+1].object)
                
                p1_x = (p1[0] + p1[2])/2
                p1_y = (p1[1] + p1[3])/2
                
                p2_x = (p2[0] + p2[2])/2
                p2_y = (p2[1] + p2[3])/2
                
                self.IDT.GROWTH_LINE.append(self.canvas.create_line(p1_x, p1_y,
                                                                p2_x, p2_y,
                                                                fill=self.IDT.growth_Axis_col, 
                                                                width=self.IDT.L_WIDTH))        
   

    
    def draw_Active_growth_line(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)  
        
        line_points = []        
        for i in range(len(self.IDT.object_list)):
            if self.IDT.object_list[i].type == "ai_point":
                line_points.append(self.IDT.object_list[i])
        
           
        if len(line_points) >0:
            
            last_point = line_points[(len(line_points)-1)]     
            
            p1 = self.canvas.coords(last_point.object)
            
            p1_x = (p1[0] + p1[2])/2
            p1_y = (p1[1] + p1[3])/2        
            
            #self.canvas.delete(self.IDT.active_growth_line)
            
            self.canvas.delete(self.IDT.active_growth_line)
            self.IDT.active_growth_line = self.canvas.create_line(p1_x, p1_y,
                                                            x, y,
                                                            fill=self.IDT.growth_Axis_col, 
                                                            width=self.IDT.L_WIDTH)        

    
    
    def create_parallel_lines(self, x1, y1, x2, y2, offset):
        # Calculate the angle of the original line
        angle = np.arctan2((y2 - y1), (x2 - x1))
    
        # Calculate the offsets for the parallel lines
        offset_x = offset * np.sin(angle)
        offset_y = offset * np.cos(angle)
    
        # Calculate new endpoints for the parallel lines
        x1_left, y1_left = x1 + offset_x, y1 - offset_y
        x2_left, y2_left = x2 + offset_x, y2 - offset_y
        x1_right, y1_right = x1 - offset_x, y1 + offset_y
        x2_right, y2_right = x2 - offset_x, y2 + offset_y
    
        left_line = [x1_left, y1_left, x2_left, y2_left]
        right_line = [x1_right, y1_right, x2_right, y2_right]
       
        return left_line, right_line
               
        
        
    def delete_object(self, event):
        
        if self.hover_over(event) != None:
            obj = self.hover_over(event)[0] # was the delete button clicked on an object in the canvas?
          #  series = self.hover_over(event)[2]
          #  print(obj)
            self.canvas.delete(self.IDT.TMP_LINE)               
        
        #if obj != None:
            if not (self.IDT.object_list[obj].type == "drill_point" or 
                self.IDT.object_list[obj].mode == "drill_line"):
                
                self.canvas.delete(self.IDT.object_list[obj].object)
                self.canvas.delete(self.IDT.object_list[obj].label)# remove the object from the canvas
                
                
            elif self.IDT.object_list[obj].type == "drill_point":
                self.canvas.delete(self.IDT.object_list[obj].object[0])
                self.canvas.delete(self.IDT.object_list[obj].object[1])
            
            elif self.IDT.object_list[obj].mode == "drill_line":
                
                self.canvas.delete(self.IDT.TMP_LINE)   
                self.canvas.delete(self.IDT.circ_1) 
                self.canvas.delete(self.IDT.circ_2) 
                self.canvas.delete(self.IDT.par_line_1) 
                self.canvas.delete(self.IDT.par_line_2) 
               
                for i in range(7):
                    self.canvas.delete(self.IDT.object_list[obj].object[i])    
                
            elif self.IDT.object_list.mode == "ai":                
                self.draw_growth_line()
                    
                #print(self.hover_over(event))
                #self.remove_from_Series(self.hover_over(event))
            
            self.remove_from_Series(obj)    
                           
    def delete_last(self, event):  

        if len(self.IDT.object_list) >  0:
            self.canvas.delete(self.IDT.TMP_LINE)
            
            self.canvas.delete(self.IDT.object_list[len(self.IDT.object_list)-1].object) # remove the object from the canvas
            self.canvas.delete(self.IDT.object_list[len(self.IDT.object_list)-1].label)
            
            #print(self.IDT.object_list[len(self.IDT.object_list)-1].series)
            
            if self.IDT.object_list[len(self.IDT.object_list)-1].series == "growth_axis":
                self.canvas.delete(self.IDT.object_list[len(self.IDT.object_list)-1].point1)
                self.canvas.delete(self.IDT.object_list[len(self.IDT.object_list)-1].point2)
                self.IDT.GROWTH_LINE.pop()
                
                
            #remove_from_Series()
            if self.IDT.object_list[len(self.IDT.object_list)-1].series == "series_1":
                self.IDT.SERIES_1.pop()
            if self.IDT.object_list[len(self.IDT.object_list)-1].series == "series_2":
                self.IDT.SERIES_2.pop()
            if self.IDT.object_list[len(self.IDT.object_list)-1].series == "series_3":
                self.IDT.SERIES_3.pop()
            self.IDT.object_list.pop() # remove the object from the list of objects
            self.update_results_window()
            
    def remove_from_Series(self, obj):
        if len(self.IDT.object_list) == 0: return
        
        series = self.IDT.object_list[obj].series
        ind = self.IDT.object_list[obj].ind  
        mode = self.IDT.object_list[obj].mode
              
        if (series == "series_1" or
            series == "series_2" or
            series == "series_3"):
            for i in range(len(self.IDT.object_list)):
                if (self.IDT.object_list[i].series == series and 
                    self.IDT.object_list[i].ind > ind):
                    self.IDT.object_list[i].ind = self.IDT.object_list[i].ind - 1
                    self.IDT.object_list[i].label_text = self.IDT.object_list[i].ind
                    self.canvas.itemconfigure(self.IDT.object_list[i].label,
                                                    text = self.IDT.object_list[i].label_text)
            del_ser = None 
            
        elif  mode == "drill_line":
            for i in range(len(self.IDT.object_list)):
                if (self.IDT.object_list[i].mode == "drill_line" and 
                    self.IDT.object_list[i].ind > ind):
                    self.IDT.object_list[i].ind = self.IDT.object_list[i].ind - 1
        
        elif  mode == "drill_point":
            for i in range(len(self.IDT.object_list)):
                if (self.IDT.object_list[i].mode == "drill_point" and 
                    self.IDT.object_list[i].ind > ind):
                    self.IDT.object_list[i].ind = self.IDT.object_list[i].ind - 1    
        
        elif mode == "ai_point":
            if (self.IDT.object_list[i].mode == "ai" and 
                self.IDT.object_list[i].ind > ind):
                self.IDT.object_list[i].ind = self.IDT.object_list[i].ind - 1  
        
        if series == "series_1":
            for i in range(len(self.IDT.SERIES_1)):
                if self.IDT.SERIES_1[i].ind == ind:
                    del_ser = i                
                elif self.IDT.SERIES_1[i].ind > ind:
                    self.IDT.SERIES_1[i].ind - 1
            self.IDT.SERIES_1.pop(del_ser)                
        
        if series == "series_2":
            for i in range(len(self.IDT.SERIES_2)):
                if self.IDT.SERIES_2[i].ind == ind:
                    del_ser = i                
                elif self.IDT.SERIES_2[i].ind > ind:
                    self.IDT.SERIES_2[i].ind - 1
            self.IDT.SERIES_2.pop(del_ser)        
        
        if series == "series_3":
            for i in range(len(self.IDT.SERIES_3)):
                if self.IDT.SERIES_3[i].ind == ind:
                    del_ser = i                
                elif self.IDT.SERIES_3[i].ind > ind:
                    self.IDT.SERIES_3[i].ind - 1
            self.IDT.SERIES_3.pop(del_ser)
            
        self.IDT.object_list.pop(obj)
        self.sort_object_list()
        self.update_results_window()
        
    def sort_object_list(self):
        tmp_ser_1 = []
        tmp_ser_2 = []
        tmp_ser_3 = []
        tmp_anno = []        
        tmp_drill_lines = []
        tmp_drill_points = []
        tmp_ai_points = []
        
        combined = []
        
        for i in range(len(self.IDT.object_list)):    
            if self.IDT.object_list[i].mode == "measure" and self.IDT.object_list[i].series == "series_1":
                tmp_ser_1.append(self.IDT.object_list[i])
            if self.IDT.object_list[i].mode == "measure" and self.IDT.object_list[i].series == "series_2":
                tmp_ser_2.append(self.IDT.object_list[i]) 
            if self.IDT.object_list[i].mode == "measure" and self.IDT.object_list[i].series == "series_3":
                tmp_ser_3.append(self.IDT.object_list[i])
            if self.IDT.object_list[i].mode == "anno":
                tmp_anno.append(self.IDT.object_list[i])
            if self.IDT.object_list[i].mode == "drill_line":
                tmp_drill_lines.append(self.IDT.object_list[i])
            if self.IDT.object_list[i].mode == "drill_point":
                tmp_drill_points.append(self.IDT.object_list[i])
            if self.IDT.object_list[i].mode == "ai":
                tmp_ai_points.append(self.IDT.object_list[i])
                self.draw_growth_line()
                
           
        if len(tmp_ser_1) > 0:
            tmp_ser_1 = self.set_order(tmp_ser_1)         
            combined = combined + tmp_ser_1 
        if len(tmp_ser_2) > 0:
            tmp_ser_2 = self.set_order(tmp_ser_2)
            combined = combined + tmp_ser_2 
        if len(tmp_ser_3) > 0:
            tmp_ser_3 = self.set_order(tmp_ser_3)
            combined = combined + tmp_ser_3   
        if len(tmp_anno) > 0:    
            combined = combined + tmp_anno         
        if len(tmp_drill_lines) > 0:    
            combined = combined + tmp_drill_lines  
        if len(tmp_drill_points) > 0:    
            combined = combined + tmp_drill_points  
        if len(tmp_ai_points) > 0:
            combined = combined + tmp_ai_points
            
        self.IDT.object_list = combined
        self.update_results_window()
        
    def set_order(self, tmp_series):
        if len(tmp_series) != 0:
            ordered = [None] * len(tmp_series)
            for i in range(len(ordered)):
                for j in range(len(tmp_series)):
                    if tmp_series[j].ind == i:
                        ordered[i] = tmp_series[j]                    
            return ordered       
        
    def get_points(self, event, value):        
        if value != "none":                   
            self.IDT.M1 = [value[2], value[0]]
            ring_no = self.IDT.object_list[value[0]].ind
            self.IDT.insert_frame.M1_label2.configure(text = "Increment selected: " + str(self.IDT.M1[0]) + " Ring: " +  str(ring_no))
            self.IDT.ACTIVE = -1    
        
     
    def end_adjust(self, event):
        self.IDT.adjusting = -1
        self.IDT.adj_point = None
        self.update_results_window()
     
    def adjust_drill_line(self, event, tmp): 
        
        if self.IDT.ACTIVE == 1 and self.IDT.adjusting == -1:
            return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)        
        
        # Check if the Ctrl button is held down
        ctrl_pressed = (event.state & 0x4) != 0
        
        if self.IDT.adj_point == None and tmp != None:        
            self.IDT.adj_point = tmp
            
        elif self.IDT.adj_point != None:   
            
            index = self.IDT.adj_point[0]
            point = self.IDT.adj_point[1]
            #series = self.IDT.adj_point[2]
            
            print(index)
            
            drill_bit = self.IDT.toolbar.drill_size_entry.get()
            if drill_bit.isdigit():
                drill_bit = int(drill_bit)
            else:    
                drill_bit = 5
            
            if self.IDT.adj_point == None and tmp != None:        
                self.IDT.adj_point = tmp
            
            if tmp == None:
                return
            elif self.IDT.adj_point != None: 
            
            
                # Only move the object if the Ctrl button is held down
                if ctrl_pressed:
                    pos = self.canvas.coords(self.IDT.object_list[index].object[0])
                    
                    for i in range(7):
                        self.canvas.delete(self.IDT.object_list[index].object[i])           
                    
                    if point == 1:
  
                        end1_coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
                        end2_coords = self.get_circle_coordinates(pos[2], pos[3], 1/self.imscale, drill_bit)
                        
                        self.IDT.object_list[index].object = []
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(x, y,
                                                                                                                pos[2], pos[3],
                                                                                                                fill=self.IDT.ACT_COLOR, 
                                                                                                                width=self.IDT.L_WIDTH))
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_oval(end1_coords[0],end1_coords[1],
                                                                                                end1_coords[2],end1_coords[3],
                                                                                                outline=self.IDT.ACT_COLOR,
                                                                                                width=self.IDT.L_WIDTH))
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_oval(end2_coords[0],end2_coords[1],
                                                                                                end2_coords[2],end2_coords[3],
                                                                                                outline=self.IDT.ACT_COLOR,
                                                                                                width=self.IDT.L_WIDTH))
                        ## draw parralel lines
                        offset = drill_bit/ (1/self.imscale)
                        left_line, right_line = self.create_parallel_lines(x, y, pos[2], pos[3], offset)
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(left_line[0], left_line[1],
                                                                                        left_line[2],left_line[3],
                                                                                        fill=self.IDT.ACT_COLOR, 
                                                                                        width=self.IDT.L_WIDTH))  
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(right_line[0], right_line[1],
                                                                                        right_line[2], right_line[3],
                                                                                        fill=self.IDT.ACT_COLOR, 
                                                                                        width=self.IDT.L_WIDTH)) 
                        
                        # add centre points to help with adjustments
                        self.IDT.object_list[index].object.append(self.canvas.create_oval(x+ 5, y + 5,
                                                                                                x - 5, y - 5,
                                                                                                fill =self.IDT.ACT_COLOR))
                        
                        self.IDT.object_list[index].object.append( self.canvas.create_oval(pos[2]+5, pos[3]+5,
                                                                                                pos[2]-5, pos[3]-5,
                                                                                                fill = self.IDT.ACT_COLOR))
                            
                        
                        
                        
                        
                        p1 = self.absolute(x, y)
                        self.IDT.object_list[index].x1 = p1[0]
                        self.IDT.object_list[index].y1 = p1[1]                        
                        
                    if point == 2:
                        end1_coords = self.get_circle_coordinates(pos[0], pos[1], 1/self.imscale, drill_bit)
                        end2_coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
                        
                        self.IDT.object_list[index].object = []
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(pos[0], pos[1],
                                                                                            x, y,
                                                                                              fill=self.IDT.ACT_COLOR, 
                                                                                              width=self.IDT.L_WIDTH))

                        self.IDT.object_list[index].object.append(self.canvas.create_oval(end1_coords[0],end1_coords[1],
                                                                                                end1_coords[2],end1_coords[3],
                                                                                                outline=self.IDT.ACT_COLOR,
                                                                                                width=self.IDT.L_WIDTH))
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_oval(end2_coords[0],end2_coords[1],
                                                                                                end2_coords[2],end2_coords[3],
                                                                                                outline=self.IDT.ACT_COLOR,
                                                                                                width=self.IDT.L_WIDTH))
                        ## draw parralel lines
                        offset = drill_bit/ (1/self.imscale)
                        left_line, right_line = self.create_parallel_lines(pos[0], pos[1], x, y,  offset)
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(left_line[0], left_line[1],
                                                                                        left_line[2],left_line[3],
                                                                                        fill=self.IDT.ACT_COLOR, 
                                                                                        width=self.IDT.L_WIDTH))  
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_line(right_line[0], right_line[1],
                                                                                        right_line[2], right_line[3],
                                                                                        fill=self.IDT.ACT_COLOR, 
                                                                                        width=self.IDT.L_WIDTH)) 
                        
                        # add centre points to help with adjustments
                        self.IDT.object_list[index].object.append( self.canvas.create_oval(pos[0]+5, pos[1]+5,
                                                                                                pos[0]-5, pos[1]-5,
                                                                                                fill = self.IDT.ACT_COLOR))
                        
                        self.IDT.object_list[index].object.append(self.canvas.create_oval(x+ 5, y + 5,
                                                                                                x - 5, y - 5,
                                                                                                fill =self.IDT.ACT_COLOR))
                        
    
                        p1 = self.absolute(x, y)
                        self.IDT.object_list[index].x2 = p1[0]
                        self.IDT.object_list[index].y2 = p1[1]    
            

    def adjust_drill_point(self, event, tmp):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)  
        
        self.IDT.adj_point = tmp
        
        index = self.IDT.adj_point[0]
        point = self.IDT.adj_point[1]
        series = self.IDT.adj_point[2]
        
        self.canvas.delete(self.IDT.object_list[index].object[0])
        self.canvas.delete(self.IDT.object_list[index].object[1])

        
        self.IDT.object_list[len(self.IDT.object_list)-1].type = "drill_point"
        self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
        self.IDT.object_list[len(self.IDT.object_list)-1].object = []
        size = 5
        self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(x - size, y - size, 
                                                                                    x + size, y + size,
                                                                                    fill = self.IDT.ACT_COLOR))
        
        drill_bit = int(self.IDT.toolbar.drill_size_entry.get())
        
        coords = self.get_circle_coordinates(x, y, 1/self.imscale, drill_bit)
        
        self.IDT.object_list[len(self.IDT.object_list)-1].object.append(self.canvas.create_oval(coords[0],coords[1],
                                                                                coords[2],coords[3],
                                                                                outline=self.IDT.ACT_COLOR,
                                                                                width=2))
        
        p1 = self.absolute(x, y)
        self.IDT.object_list[index].x1 = p1[0] - size
        self.IDT.object_list[index].y1 = p1[1] - size
        self.IDT.object_list[index].x2 = p1[0] + size
        self.IDT.object_list[index].y2 = p1[1] + size   
        
    def adjust_point(self, event):
        if self.IDT.ACTIVE == 1 and self.IDT.adjusting == -1: return
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)        
        # to start a measurement temporarily store the coordinates where the mouse was clicked
        
        tmp = self.hover_over(event)
        
        if self.IDT.adj_point == None and tmp != None:        
            self.IDT.adj_point = tmp
        
        if tmp == None:
            return
        elif self.IDT.adj_point != None: 
            
            if tmp[2] == "drill_line":
                self.adjust_drill_line(event, tmp)
                
            elif tmp[2] == "drill_point":
                self.adjust_drill_point(event, tmp)
                
            else:          
                index = self.IDT.adj_point[0]
                point = self.IDT.adj_point[1]
                series = self.IDT.adj_point[2]
                
                pos = self.canvas.coords(self.IDT.object_list[index].object)        
                self.canvas.delete(self.IDT.object_list[index].object)
                
                size = 5 # size of circle
                
                if self.IDT.object_list[index].type == "line":    
                    if point == 1:
                        self.IDT.object_list[index].object = self.canvas.create_line(x, y,
                                                                                    pos[2],pos[3],
                                                                                    fill = self.IDT.ACT_COLOR, 
                                                                                    width = self.IDT.L_WIDTH,
                                                                                    arrow = tk.BOTH,
                                                                                    arrowshape = self.IDT.line_cap)
                        p1 = self.absolute(x, y)
                        self.IDT.object_list[index].x1 = p1[0]
                        self.IDT.object_list[index].y1 = p1[1]
                        
                        px_distance = math.dist((x, y), 
                                                (pos[2],pos[3])) * (1/self.imscale)
                        self.IDT.object_list[index].px_distance = px_distance
                        self.IDT.object_list[index].abs_distance = self.IDT.object_list[index].px_distance * self.IDT.object_list[index].calibration
                        
                    if point == 2:
                        self.IDT.object_list[index].object = self.canvas.create_line(pos[0],pos[1],
                                                                                    x, y,
                                                                                    fill = self.IDT.ACT_COLOR, 
                                                                                    width = self.IDT.L_WIDTH,
                                                                                    arrow = tk.BOTH,
                                                                                    arrowshape = self.IDT.line_cap)
                        p1 = self.absolute(x, y)
                        self.IDT.object_list[index].x2 = p1[0]
                        self.IDT.object_list[index].y2 = p1[1]
                        
                        px_distance = math.dist((pos[0],pos[1]),
                                                (x, y)) * (1/self.imscale)
                        
                        self.IDT.object_list[index].px_distance = px_distance
                        self.IDT.object_list[index].abs_distance = self.IDT.object_list[index].px_distance * self.IDT.object_list[index].calibration
              
                    # print("seris: " + str(ST.object_list[index].series) +
                    #       "\nindex: " + str(ST.object_list[index].ind))
                    series_index = self.IDT.object_list[index].ind
                    if series == "series_1":
                         self.IDT.SERIES_1[series_index] =  self.IDT.object_list[index]
                    if series == "series_2":
                         self.IDT.SERIES_2[series_index] =  self.IDT.object_list[index]
                    if series == "series_3":
                         self.IDT.SERIES_3[series_index] =  self.IDT.object_list[index]
                    
                    self.canvas.delete(self.IDT.object_list[index].label)
                    coords = self.canvas.coords(self.IDT.object_list[index].object)
                    label_x = (coords[0] + coords[2]) / 2 + self.IDT.lab_x_off
                    label_y = (coords[1] + coords[3]) / 2 + self.IDT.lab_y_off
                    self.IDT.object_list[index].label = self.canvas.create_text(label_x, label_y,
                                                                                                text= self.IDT.object_list[index].label_text, 
                                                                                                fill="black", 
                                                                                                font=('Helvetica 15 bold'))
                   
                
                if (self.IDT.object_list[index].type == "dot" or 
                    self.IDT.object_list[index].type == "reference"):
                    
                    self.IDT.object_list[index].object = self.canvas.create_oval(x - size, y - size, 
                                                                                x + size, y + size, 
                                                                                fill = self.IDT.ANNOTE_COL)
                    p1 = self.absolute(x, y)
                    self.IDT.object_list[index].x1 = p1[0] - size
                    self.IDT.object_list[index].y1 = p1[1] - size
                    self.IDT.object_list[index].x2 = p1[0] + size
                    self.IDT.object_list[index].y2 = p1[1] + size
                    
                if self.IDT.object_list[index].type == "ai_point":
                    self.IDT.object_list[index].object = self.canvas.create_oval(x - size, y - size, 
                                                                                x + size, y + size, 
                                                                                fill = self.IDT.ANNOTE_COL)
                    p1 = self.absolute(x, y)
                    self.IDT.object_list[index].x1 = p1[0] - size
                    self.IDT.object_list[index].y1 = p1[1] - size
                    self.IDT.object_list[index].x2 = p1[0] + size
                    self.IDT.object_list[index].y2 = p1[1] + size
                    
                    self.draw_growth_line()
                    
                    
            
                if self.IDT.object_list[index].type == "text":
                    self.IDT.object_list[index].object = self.canvas.create_text(x, y, 
                                                                                text = self.IDT.object_list[index].text, 
                                                                                fill = self.IDT.ANNOTE_COL, 
                                                                                font=('Helvetica 15 bold'))
                    p1 = self.absolute(x, y)
                    self.IDT.object_list[index].x1 = p1[0] 
                    self.IDT.object_list[index].y1 = p1[1] 
                    self.IDT.object_list[index].x2 = p1[0] 
                    self.IDT.object_list[index].y2 = p1[1] 
        
       
            
    def load_the_data(self, data):
        # check if the data is the correct format
        names = list(data.columns)
        
        new = ["sample_ID", "x1","y1","x2", "y2", "mode","series", "ob_type", "ind", "text", 
                    "px_distance", "abs_distance",	"calibration",	"calibrated",	
                    "label_text",	"year",	"dated", "col"]
        
        # legacy file structure
        old = ["sample_id",	"ind",	"series", "x1",	"y1", "x2", "y2",
               "px_distance", "abs_distance", "calibration", "calibrated"]
        
        # if the data is in the new format:
        if names[1] == new[1]:
            # if it is the correct format - load the data
            for i in range(data.shape[0]):
                tmp = data.iloc[i]
                
                p1 = self.convert_to_canvas(tmp["x1"], tmp["y1"])
                p2 = self.convert_to_canvas(tmp["x2"], tmp["y2"])
                
                # self.IDT.object_list.append(canvas_object(p1[0], p1[1],
                #                                     p2[0], p2[1],
                #                                     tmp["mode"], 
                #                                     tmp["series"],
                #                                     tmp["ind"]        
                #                                     ))
                
                self.IDT.object_list.append(canvas_object(tmp["x1"], tmp["y1"],
                                                    tmp["x2"], tmp["y2"],
                                                    tmp["mode"], 
                                                    tmp["series"],
                                                    tmp["ind"]        
                                                    ))
                
                N = len(self.IDT.object_list)-1
                
                self.IDT.object_list[N].object = None
                self.IDT.object_list[N].type = tmp["ob_type"]
                self.IDT.object_list[N].text = tmp["text"]
                self.IDT.object_list[N].px_distance = tmp["px_distance"]
                self.IDT.object_list[N].abs_distance = tmp["abs_distance"]
                self.IDT.object_list[N].calibrated = tmp["calibrated"]      
                self.IDT.object_list[N].calibration =  tmp["calibration"]
                self.IDT.object_list[N].label_text =  tmp["label_text"]
                self.IDT.object_list[N].year =  tmp["year"]      
                self.IDT.object_list[N].dated =  tmp["dated"]
                self.IDT.object_list[N].col =  tmp["col"]
                
                if math.isnan(self.IDT.object_list[N].label_text) == False:
                    self.IDT.object_list[N].label_text = int(self.IDT.object_list[N].label_text)
                
                if math.isnan(self.IDT.object_list[N].year) == False:
                    self.IDT.object_list[N].year = int(self.IDT.object_list[N].year)    
                
                # print("check type = " + ST.object_list[N].type)
                if self.IDT.object_list[N].type == "line":
                    # self.IDT.object_list[N].object = self.canvas.create_line(self.IDT.object_list[N].x1, self.IDT.object_list[N].y1,
                    #                                                         self.IDT.object_list[N].x2, self.IDT.object_list[N].y2,
                    #                                                         fill = self.IDT.object_list[N].col, 
                    #                                                         width = self.IDT.L_WIDTH,
                    #                                                         arrow=tk.BOTH,
                    #                                                         arrowshape = self.IDT.line_cap)
                    
                    self.IDT.object_list[N].object = self.canvas.create_line(p1[0], p1[1],
                                                                            p2[0], p2[1],
                                                                            fill = self.IDT.object_list[N].col, 
                                                                            width = self.IDT.L_WIDTH,
                                                                            arrow=tk.BOTH,
                                                                            arrowshape = self.IDT.line_cap)
                if self.IDT.object_list[N].mode == "measure":
                    # label_x = (self.IDT.object_list[N].x1 + self.IDT.object_list[N].x2) / 2 + self.IDT.lab_x_off
                    # label_y = (self.IDT.object_list[N].y1 + self.IDT.object_list[N].y2) / 2 + self.IDT.lab_y_off
                    label_x = (p1[0] + p2[0] ) / 2 + self.IDT.lab_x_off
                    label_y = (p1[1] + p2[1] ) / 2 + self.IDT.lab_y_off
                    
                    self.IDT.object_list[N].label = self.canvas.create_text(label_x, label_y,
                                                                            text = self.IDT.object_list[N].label_text, 
                                                                            fill = "black", 
                                                                            font = ('Helvetica 15 bold'))
                    
                    #check if calibrateed
                    if self.IDT.object_list[N].calibrated:
                        self.IDT.CALIBRATED = True # has the distance had a calibration applied?       
                        self.IDT.CALIBRATION = self.IDT.object_list[N].calibration # the scale factor to use to convert from pixel to absolute distance
                        self.IDT.calibration_SF = self.IDT.CALIBRATION
                       
                        self.IDT.calib_frame.cal_set_label.configure(text = "Calibration set: " + str(round(self.IDT.calibration_SF, 3)))

                if self.IDT.object_list[N].series == "series_1":                    
                    self.IDT.object_list[N].col = self.IDT.ser_1_col #self.IDT.ser_1_col
                    self.IDT.SERIES_1.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_1)-1
                
                elif self.IDT.object_list[N].series == "series_2":
                    self.IDT.object_list[N].col = self.IDT.ser_2_col
                    self.IDT.SERIES_2.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_2)-1
                
                elif self.IDT.object_list[N].series == "series_3":
                    self.IDT.object_list[N].col = self.IDT.ser_3_col
                    self.IDT.SERIES_3.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_3)-1                

                if self.IDT.object_list[N].type == "dot":
                    self.IDT.object_list[N].object = self.canvas.create_oval(self.IDT.object_list[N].x1, self.IDT.object_list[N].y1,
                                                                            self.IDT.object_list[N].x2, self.IDT.object_list[N].y2, 
                                                                            fill = self.IDT.object_list[N].col)
                if self.IDT.object_list[N].type == "text":    
                    self.IDT.object_list[N].object = self.canvas.create_text(self.IDT.object_list[N].x1, self.IDT.object_list[N].y1,
                                                                            text = self.IDT.object_list[N].text, 
                                                                            fill = self.IDT.object_list[N].col,
                                                                            font = ('Helvetica 15 bold'))
                    
            
            self.IDT.start_year = int(min(data["year"]))
            
            if self.IDT.start_year != 0:
                self.IDT.assigned = not self.IDT.assigned
                 
            return
        
        # if the data are legacy data load it this way:
        elif names[1] == old[1]:
            for i in range(data.shape[0]):
                tmp = data.iloc[i]
                p1 = self.convert_to_canvas(tmp["x1"], tmp["y1"])
                p2 = self.convert_to_canvas(tmp["x2"], tmp["y2"])
                
                self.IDT.object_list.append(canvas_object(p1[0], p1[1],
                                                    p2[0], p2[1],
                                                    "measure", 
                                                    tmp["series"],
                                                    tmp["ind"]        
                                                    ))                            
                
                N = len(self.IDT.object_list)-1
                self.IDT.object_list[N].type = "line"
                self.IDT.object_list[N].px_distance = tmp["px_distance"]
                self.IDT.object_list[N].abs_distance = tmp["abs_distance"]
                self.IDT.object_list[N].calibrated = tmp["calibrated"]      
                self.IDT.object_list[N].calibration =  tmp["calibration"]                
                self.IDT.object_list[N].label_text =  tmp["ind"]  
                self.IDT.object_list[N].year =  tmp["ind"] 
                self.IDT.object_list[N].label_text =  tmp["ind"]  
                self.IDT.object_list[N].dated =  False               
                            
                if self.IDT.object_list[N].series == "series_1":                    
                    self.IDT.object_list[N].col = self.IDT.ser_1_col #self.IDT.ser_1_col
                    self.IDT.SERIES_1.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_1)-1
                
                elif self.IDT.object_list[N].series == "series_2":
                    self.IDT.object_list[N].col = self.IDT.ser_2_col
                    self.IDT.SERIES_2.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_2)-1
                
                elif self.IDT.object_list[N].series == "series_3":
                    self.IDT.object_list[N].col = self.IDT.ser_3_col
                    self.IDT.SERIES_3.append(self.IDT.object_list[N])
                    self.IDT.object_list[N].ind = len(self.IDT.SERIES_3)-1
                                                 
                if self.IDT.object_list[N].mode == "measure":                     
                    self.IDT.object_list[N].object = self.canvas.create_line(p1[0], p1[1],
                                                                            p2[0], p2[1],
                                                                            fill = self.IDT.object_list[N].col, 
                                                                            width = self.IDT.L_WIDTH,
                                                                            arrow=tk.BOTH,
                                                                            arrowshape = self.IDT.line_cap)
                    #label_x = (self.IDT.object_list[N].x1 + self.IDT.object_list[N].x2) / 2 + self.IDT.lab_x_off
                    #label_y = (self.IDT.object_list[N].y1 + self.IDT.object_list[N].y2) / 2 + self.IDT.lab_y_off
                    label_x = (p1[0] + p2[0] ) / 2 + self.IDT.lab_x_off
                    label_y = (p1[1] + p2[1] ) / 2 + self.IDT.lab_y_off
                    
                    self.IDT.object_list[N].label = self.canvas.create_text(label_x, label_y,
                                                                            text = self.IDT.object_list[N].label_text, 
                                                                            fill = "black", 
                                                                            font = ('Helvetica 15 bold'))
                    
                    if self.IDT.object_list[N].calibrated:
                        
                        self.IDT.CALIBRATED = True # has the distance had a calibration applied?       
                        self.IDT.CALIBRATION = self.IDT.object_list[N].calibration # the scale factor to use to convert from pixel to absolute distance
                        self.IDT.calibration_SF = self.IDT.CALIBRATION
                       
                        self.IDT.calib_frame.cal_set_label.configure(text = "Calibration set: " + str(round(self.IDT.calibration_SF, 3)))

            return
        else:
            self.IDT.error_frame.label.configure(text = "The loaded file is not \n" +
                                                     "the correct structure \n" +
                                                     "and cannot be loaded")
            self.IDT.error_frame.toggle()
            return     
    
    def draw_text(self, event):       
        
        text = self.IDT.toolbar.text_entry.get()
        
        if len(text)== 0: return
        
        #get coords of where the mouse was clikced in the canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
    
        size = 5
            
        
        
        # to start a measurement temporarily store the coordinates where the mouse was clicked
        
        p1 = self.absolute(x, y)
        
        self.IDT.object_list.append(canvas_object(p1[0] - size, p1[1] - size, 
                                            p1[0] + size, p1[1] + size,
                                            self.IDT.MODE, 
                                            None, 
                                            len(self.IDT.object_list)))
        self.IDT.object_list[len(self.IDT.object_list)-1].obj_index = len(self.IDT.object_list)-1
        self.IDT.object_list[len(self.IDT.object_list)-1].type = "text"
        self.IDT.object_list[len(self.IDT.object_list)-1].col = self.IDT.ACT_COLOR
        self.IDT.object_list[len(self.IDT.object_list)-1].text = text
        self.IDT.object_list[len(self.IDT.object_list)-1].object = self.canvas.create_text(x, y, 
                                                                                    text= self.IDT.object_list[len(self.IDT.object_list)-1].text, 
                                                                                    fill="black", 
                                                                                    font=('Helvetica 15 bold'))
    def update_results_window(self):
        if self.IDT.results != None and self.IDT.results.visible:
            self.IDT.results.update()            
            
    def load_AI_data(self, data):
        for i in range(data.shape[0]-1):
            tmp1 = data.iloc[i]
            tmp2 = data.iloc[i+1]
            p1 = self.convert_to_canvas(tmp1["x1"], tmp1["y1"])
            p2 = self.convert_to_canvas(tmp2["x1"], tmp2["y1"])
            
            px_distance = math.dist((p1[0], p1[1]), 
                                 (p2[0], p2[1])) * (1/self.imscale) 
            
            
            self.IDT.object_list.append(canvas_object(p1[0], p1[1],
                                                p2[0], p2[1],
                                                "measure", 
                                                "series_1",
                                                i        
                                                ))
            
            N = len(self.IDT.object_list)-1
            
            self.IDT.object_list[N].object = None
            self.IDT.object_list[N].type = "line"
            self.IDT.object_list[N].px_distance = px_distance 
            self.IDT.object_list[N].abs_distance = px_distance
            self.IDT.object_list[N].calibrated = False      
            self.IDT.object_list[N].calibration =  1
            self.IDT.object_list[N].label_text =  N 
            self.IDT.object_list[N].year = N    
            self.IDT.object_list[N].dated =  False
            self.IDT.object_list[N].col =  self.IDT.ser_1_col
            
            self.IDT.object_list[N].p1 = tmp1["p"]
            self.IDT.object_list[N].p2 = tmp2["p"]
            
            self.IDT.object_list[N].object = self.canvas.create_line(self.IDT.object_list[N].x1, self.IDT.object_list[N].y1,
                                                                    self.IDT.object_list[N].x2, self.IDT.object_list[N].y2,
                                                                    fill = self.IDT.object_list[N].col, 
                                                                    width = self.IDT.L_WIDTH,
                                                                    arrow=tk.BOTH,
                                                                    arrowshape = self.IDT.line_cap)
            label_x = (self.IDT.object_list[N].x1 + self.IDT.object_list[N].x2) / 2 + self.IDT.lab_x_off
            label_y = (self.IDT.object_list[N].y1 + self.IDT.object_list[N].y2) / 2 + self.IDT.lab_y_off
          
            self.IDT.object_list[N].label = self.canvas.create_text(label_x, label_y,
                                                                    text = self.IDT.object_list[N].label_text, 
                                                                    fill = "black", 
                                                                    font = ('Helvetica 15 bold'))
            
            self.IDT.SERIES_1.append(self.IDT.object_list[N])
            
    # this function shows the analysis of the AI run in the app        
    def show_AI_data(self, data):
        for i in range(len(data)-1):
            #print(data[i][0])
            p1 = self.convert_to_canvas(data[i][1], data[i][0])
            p2 = self.convert_to_canvas(data[i+1][1], data[i+1][0])
            
            px_distance = math.dist((p1[0], p1[1]), 
                                 (p2[0], p2[1])) * (1/self.imscale) 
            
            
            self.IDT.object_list.append(canvas_object(p1[0], p1[1],
                                                p2[0], p2[1],
                                                "measure", 
                                                "series_1",
                                                i        
                                                ))
            
            N = len(self.IDT.object_list)-1
            
            self.IDT.object_list[N].object = None
            self.IDT.object_list[N].type = "line"
            self.IDT.object_list[N].px_distance = px_distance 
            self.IDT.object_list[N].abs_distance = px_distance
            self.IDT.object_list[N].calibrated = False      
            self.IDT.object_list[N].calibration =  1
            self.IDT.object_list[N].label_text =  i 
            self.IDT.object_list[N].year = i    
            self.IDT.object_list[N].dated =  False
            self.IDT.object_list[N].col =  self.IDT.ser_1_col
            
            # self.IDT.object_list[N].p1 = tmp1["p"]
            # self.IDT.object_list[N].p2 = tmp2["p"]
            
            self.IDT.object_list[N].object = self.canvas.create_line(p1[0], p1[1],
                                                                    p2[0], p2[1],
                                                                    fill = self.IDT.object_list[N].col, 
                                                                    width = self.IDT.L_WIDTH,
                                                                    arrow=tk.BOTH,
                                                                    arrowshape = self.IDT.line_cap)
            label_x = (p1[0] + p2[0]) / 2 + self.IDT.lab_x_off
            label_y = (p1[1] + p2[1]) / 2 + self.IDT.lab_y_off
          
            self.IDT.object_list[N].label = self.canvas.create_text(label_x, label_y,
                                                                    text = self.IDT.object_list[N].label_text, 
                                                                    fill = "black", 
                                                                    font = ('Helvetica 15 bold'))
            
            self.IDT.SERIES_1.append(self.IDT.object_list[N])
            
    # def CVI_analyse_axis(self):
    #     #print("running")
    #     if self.IDT.model == "Select a model":
    #         tk.messagebox.askokcancel("Close", "You need to select a model")
    #         return
            
    #     self.run_model_window()
        
    #     if len(self.IDT.GROWTH_LINE)>0:
    #         axis_path = analyse_axis(self.IDT.filename, self.IDT.GROWTH_LINE, self.IDT.model )
    #         #self.run_model_new_axis(axis_path)
            
    #         ### need to check why this is needed!!!!
    #        # self.IDT.object_list = []
                        
    #         AI_data = run_model(self.IDT.filename, axis_path, self.IDT.model )
            
    #         self.show_AI_data(AI_data)
    #         toggle_mode("measure", self.IDT.img_win)
    #         toggle_series("series_1", self.IDT.img_win)
    #         self.close_model_window()
            
            
    # def run_model_window(self): 
    #     self.IDT.model_frame.grid(row = 0, column = 0, padx = 5, pady =125, sticky = tk.EW)
    #     self.note = ctk.CTkLabel(self.IDT.model_frame, text ="Model is running: Results will display automatically")
    #     self.note.grid(row = 0, column = 0, padx = 5, pady = 0)
    #     self.canvas.update()
            
    # def close_model_window(self):
    #     self.IDT.model_frame.grid_forget()
    #     self.canvas.update()