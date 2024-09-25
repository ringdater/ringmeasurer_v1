# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 15:17:56 2023

@author: david
"""

#import global_variables as ST

# import customtkinter
# import tkinter as tk
# import math

import win_array as WA

from shellai import peakfinding, tf_util
from scipy.signal import find_peaks

from tkinter import filedialog

import imageio
import tqdm.notebook

import numpy as np
import tensorflow as tf
import os

import yaml

from PIL import Image, ImageTk, ImageDraw, ImageFont

class canvas_object:
    def __init__(self, x1, y1, x2, y2, mode, series, ind):
        self.obj_index = None # what is the index in the object lst - use to keep track of objects between lists
        self.x1 = x1 # the x1 position on the original image - not the canvas position
        self.y1 = y1 # the y1 position on the original image - not the canvas position
        self.x2 = x2 # the x2 position on the original image - not the canvas position
        self.y2 = y2 # the y2 position on the original image - not the canvas position
        self.mode = mode # what mode was the app in when the object was created
        self.series = series # what series was being measured
        self.type = False # is this part of a measurement line
        self.ind = ind # the index in the object_list array
        self.object = None # the actual canvas object
        self.text = None # if the object is text, this is the actual text to display
        self.px_distance = None # measurement length in pixels
        self.abs_distance = None # the calibration for the image defaults to 1 pixel per um
        self.calibrated = False # has the distance had a calibration applied?       
        self.calibration = 1 # the scale factor to use to convert from pixel to absolute distance
        self.line_label = None # holds the label object
        self.year = None # use to assign years to the measurements        
        self.dated = None # has this sample been crossdated
        self.col = None # what colour is the object        
        self.label = None # the label object
        self.label_visible = False # is the label visible or not
        self.label_text = None # the text to show in the label 
        self.point1 = None # object for growth axis line junctions
        self.point2 = None # object for growth axis line junctions
        
# =============================================================================
#  functions       
# =============================================================================

def check_focus(window, event=None):
    if not window.focus_get():
        window.lift()
        window.focus_force()

def toggle_mode(mode, win):

    print("window = " + str(win) + "; mode = " + str(mode))    
    WA.wins[win].canvas.IDT.MODE = mode
    
    if mode == "calibrate":
        WA.wins[win].canvas.IDT.calib_frame.toggle()
        
    if mode == "insert":
        WA.wins[win].canvas.IDT.insert_frame.toggle()
        
    if mode == "ai":
        WA.wins[win].canvas.IDT.model_frame.toggle()

        
# def gb_test(win): 
#     print(WA.wins[win].canvas.IDT.MODE)


def toggle_series(series, win):
    WA.wins[win].canvas.IDT.prev_ser = WA.wins[win].canvas.IDT.ACT_SER
    if series == "series_1":
        WA.wins[win].canvas.IDT.ACT_SER = "series_1"
    if series == "series_2":
        WA.wins[win].canvas.IDT.ACT_SER = "series_2"
    if series == "series_3":
        WA.wins[win].canvas.IDT.ACT_SER = "series_3"
    if series == "insert":
        WA.wins[win].canvas.IDT.ACT_SER = "insert" 
    WA.wins[win].canvas.IDT.toolbar.current_series_label.configure(text =  WA.wins[win].canvas.IDT.ACT_SER)
    
def set_anno_type(anno_type, win):    
    WA.wins[win].canvas.IDT.anno_type = anno_type

def set_order(tmp_series):
    if len(tmp_series) != 0:
        ordered = [None] * len(tmp_series)
        for i in range(len(ordered)):
            for j in range(len(tmp_series)):
                if tmp_series[j].ind == i:
                    ordered[i] = tmp_series[j]                    
        return ordered 

def run_model(image_path, mask_path, sel_model):
    print(image_path)
    print(mask_path)
    

    # load the config file
    with open("config.yaml", "r") as fd:
        cfg = yaml.safe_load(fd)
    
    # experimental settings
    
    # size of patches to extract for prediction
    # (this should be the same as the model was trained on)
    patch_shape = tuple(cfg['testing']['patch_shape'])
    
    # stride (in pixels) between extracted patches
    stride_step = cfg['testing']['stride']
    
    # specify the paths to the image and mask
    #image_path = "test/140013_image.tif"
    #ST.mask_path = "test/140013_mask.tif"
    
    # load the image and mask
    image = np.array(imageio.v2.imread(image_path))
    
    line_mask = np.array(imageio.v2.imread(mask_path))
    
    # get the coords of the test patches (patch_coords), their centres (lc), 
    # and the coordinates of the hand-drawn axis of maximum growth (full_lc)
    patch_coords, lc, full_lc = tf_util.get_test_patch_locations(
        line_mask, patch_shape, stride_step
    )
    
    # larger batch sizes will make the predictions faster, 
    # but will lead to higher cpu and memory usage (lower if the needed)
    # NOTE: use powers of 2, e.g., 2, 4, 8, 16, ...
    batch_size = 32
    
    # create the test dataset
    test_ds = tf_util.convert_patches_into_tf_ds(
        patch_coords, image, batch_size=batch_size
    )
    
    # load the model
    model_path = "models/" + sel_model
    
    model = tf.keras.models.load_model(model_path)
    
    # predict all the images of the test dataset (batched)
    predictions = []
    
    for batch in tqdm.notebook.tqdm(test_ds, leave=False):
        # make the prediction
        pred = model(batch, training=False)
    
        # convert to numpy and store
        predictions.append(pred.numpy().squeeze())
    
    # join together the predictions
    predictions = np.concatenate(predictions, axis=0)
    
    ringfinding_patch_size = 3
    ringfinding_method = "max"
    
    # list of prominences to extract for
    prominence = 0.05
    
    # minimum width of peaks
    peak_width = 1
    
    # minimum distance between peaks (in pixels). this value was selected by
    # looking at the minimum distance between the peaks training images (~30) and
    # choosing a smaller value (25)
    peak_min_dist = 25
    
    # create the prediction image. this maps the predicted patches into 
    # an image mask of a predefined shape
    predicted_mask, _ = tf_util.create_patch_image(
        patches=predictions,
        patch_coords=patch_coords,
        image_shape=image.shape
    )
    
    # get the pixel value pooled in a (ringfinding_patch_size, ringfinding_patch_size)
    # patch along the pixels of the growth axis, pooling ling `ringfinding_method``
    r = tf_util.extract_rings_patchbased(
        line_coords=full_lc,
        image=predicted_mask,
        patch_size=ringfinding_patch_size,
        method=ringfinding_method
    )
    
    # normalise the values such that the largest value is one and the
    # smallest is zero. note that this is done so that the prominence
    # value, has as close to the same meaning for each set of pixels
    rnormed = peakfinding.normalize_vector(r)
    
    # find the peaks
    r_peaks, _ = find_peaks(
        rnormed, 
        prominence=prominence, 
        width=peak_width,
        distance=peak_min_dist,
    )
    
#    xvalues = np.arange(rnormed.size)   

    # finally, convert to (y, x) coordinates
    image_peak_pixels = full_lc[r_peaks]

    return image_peak_pixels


# def analyse_axis(filename, axis_data, model):
#     img = Image.open(filename)   
#     width, height = img.size
#     image = Image.new ('RGB', (width, height))
    
#     draw = ImageDraw.Draw(image)
#     draw.rectangle ((0,0,width,height), fill = (255,255,255) )
    
#     for i in range(len(axis_data)-1):
#         draw.line((axis_data[i][0],axis_data[i][1],
#                    axis_data[i+1][0],axis_data[i+1][1]), 
#                    fill="black",
#                    width = 5)
        
#     img_name = os.path.splitext(os.path.basename(filename))[0]    
#     img_dir = os.path.dirname(filename)
    
#     axis_path = img_dir +"/" + img_name + "_growth_axis.png"
#     image.save(axis_path)
           
#     return axis_path
  
def analyse_axis(axis_data, filename=None):
    img = Image.open(filename) if filename else Image.new('RGB', (800, 600), color='white')
    width, height = img.size
    
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), fill=(255, 255, 255))
    
    for i in range(len(axis_data) - 1):
        draw.line((axis_data[i][0], axis_data[i][1],
                   axis_data[i + 1][0], axis_data[i + 1][1]),
                  fill="black",
                  width=5)
    

    # If filename is not provided, ask the user to choose the location
    maskname = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG files", "*.png")],
                                            title="Save Growth Axis Image")
    if not maskname:
        return None  # User canceled the operation
        
    image.save(maskname)
    
    return maskname      

