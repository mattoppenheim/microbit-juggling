''' Main module for the microbit_juggling project.
Sets up the pyqtgraph.
Data collection from the microbits is done in a separate thread.
Communication between the graph and the data collection thread via pydispatch.
Data samples are held in numpy arrays.

Matthew Oppenheim May 2018. '''


import PySide
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from pyqtgraph.ptime import time
import sys

# how many samples to average to obtain the sample frequency
FREQ_AVG = 100

# how many samples to display
NUM_SAMPLES = 300
# frequence to refresh the display
SCREEN_REFRESH_RATE = 15

class MicrobitJuggle():
    def __init__(self):
        self.app = QtGui.QApplication([])
        mb1 = self.initialise_data()
        mb2 = self.initialise_data()
        mb3 = self.initialise_data()
        self.mb_data = [mb1, mb2, mb3]
        self.initialise_data()
        win = pg.GraphicsWindow()
        win.setWindowTitle('Microbit accelerometer data')
        p1 = win.addPlot()
        win.nextRow()
        p2 = win.addPlot()
        win.nextRow()
        p3 = win.addPlot()
        for plot in [p1, p2, p3]:
            plot.setYRange(0,3000)
        self.text = pg.TextItem('text', anchor=(0,3))
        p3.addItem(self.text)
        self.curve1 = p1.plot()
        self.curve2 = p2.plot()
        self.curve3 = p3.plot()
        self.index = 0
        self.last_time = time()
        self.freq = None
        self.freq_list = np.zeros(FREQ_AVG)


    def graph_update_rate(self):
            ''' Calculate graph refresh frequency. '''
            now_time = time()
            dt = now_time - self.last_time
            self.last_time = now_time
            if self.freq is None:
                self.freq = 1.0/dt
            else:
                s = np.clip(dt*3., 0, 1)
                self.freq = self.freq * (1-s) + (1.0/dt) * s
            self.freq_list[-1] = self.freq
            return(FREQ_AVG*np.average(self.freq_list))


    def initialise_data(self):
        ''' Create a numpy arrays of 0s. '''
        # MAKE dtype INT
        return np.zeros(NUM_SAMPLES,dtype=int)

    def roll_data(self, data):
        ''' Rolls <data> by one sample. '''
        # using slices is 2.5 times faster than using np.roll
        data[:-1] = data[1:]
        return data

    def update(self):
        ''' Update the plot curves with a new value. SYNTHETIC DATA '''
        for data in self.mb_data:
            data[-1] = int(abs(np.random.normal(scale=1000)))
        self.text.setText('self.frequency: {:0.1f}'.format(self.graph_update_rate(), color=(255,255,0)))
        self.curve1.setData(self.mb_data[0])
        self.curve2.setData(self.mb_data[1])
        self.curve3.setData(self.mb_data[2])
        for data in self.mb_data:
            data = self.roll_data(data)
        else:
            self.index+=1
        # self.app.processEvents()



if __name__ == '__main__':
    print('instantiating MicrobitJuggle ')
    microbit_juggling = MicrobitJuggle()
    timer = QtCore.QTimer()
    timer.timeout.connect(microbit_juggling.update)
    # timer units are milliseconds. timer.start(0) to go as fast as practical.
    timer.start(1000/SCREEN_REFRESH_RATE)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_'):
        QtGui.QApplication.instance().exec_()

