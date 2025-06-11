#!/usr/bin/env python3
import sys
import os

# Set dataset to standard
os.environ['DATASET'] = 'standard'
sys.argv.append('standard')

# Import and run the main module
from index import *
