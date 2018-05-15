'''
Graph accelerometer data from BBC Micro:bits.
Use pyqtgraph to display the real time data.
Use pydispatcher to communicate between data collection and data display
threads.
main.py - set up the pyqtgraph display.
read_microbits.py - get data from the BBC Micro:bits.
Matthew Oppenheim May 2018
'''

import logging
import pyqtgraph as pg
import threading

class Graph_Data():
    ''' Create the graph to display accelerometer data. '''
    def __init__(self):

