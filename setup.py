# -*- coding: utf-8 -*-
"""
Created on Tue Oct  3 15:35:29 2023

@author: David Reynolds
"""

import os
import subprocess

app_directory = os.path.dirname(os.path.abspath(__file__))

# Define the path to the requirements.txt file
requirements_file = app_directory + "/requirements.txt"

# Run the pip install command to install dependencies
subprocess.run(["pip", "install", "-r", requirements_file])
