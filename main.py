''' Main module for the microbit_juggling project.
Sets up the pyqtgraph.
Data collection from the microbits is done in a separate thread.
Communication between the graph and the data collection thread via pydispatch.
Data samples are held in numpy arrays.
To do: dynamically change the number of microbits and graphs

Matthew Oppenheim May 2018. '''

import logging
import numpy as np
from pydispatch import dispatcher
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.ptime import time
from read_microbits import ReadMicrobits
import sys
import threading

# how many samples to average to obtain the sample frequency
FREQ_AVG = 5
NUM_MICROBITS = 3
# how many samples to display
NUM_SAMPLES = 5
# frequency to refresh the display
SCREEN_REFRESH_RATE = 30

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

def system_exit(message):
    ''' quit script '''
    print('system exit: {}'.format(message))
    sys.exit(0)


class MicrobitJuggle():
    def __init__(self, num_microbits=3):
        logging.info('started main.py')
        if num_microbits > 3:
            system_exit('max num_microbits is 3')
        mb_thread = threading.Thread(target=ReadMicrobits)
        mb_thread.start()
        self.app = QtGui.QApplication([])
        win = pg.GraphicsWindow()
        win.setWindowTitle('Microbit accelerometer data')
        p0 = win.addPlot()
        win.nextRow()
        p1 = win.addPlot()
        win.nextRow()
        p2 = win.addPlot()
        for plot in [p0, p1, p2]:
            plot.setYRange(0,3000)
        self.text = pg.TextItem('text', anchor=(0,3))
        p2.addItem(self.text)
        self.curve0 = p0.plot()
        self.curve1 = p1.plot()
        self.curve2 = p2.plot()
        self.index = 0
        self.last_time = time()
        self.freq = None
        self.freq_list = np.zeros(FREQ_AVG)
        self.mb_dict = self.create_mb_dict(num_microbits)
        dispatcher.connect(self.dispatcher_receive_data,
            sender='read_microbits', signal='plot_data')


    def dispatcher_receive_data(self, message):
        ''' Handle <message> sent through dispatch. '''
        self.mb_dict = message
        # logging.info('received: {}'.format(self.mb_dict))


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


    def create_mb_dict(self, num_microbits):
        ''' Create a dictionary to store the microbit data. '''
        mb_names = ['mb_{}'.format(id_x) for id_x in range(num_microbits)]
        mb_dict = {name: self.initialise_data() for name in mb_names}
        return mb_dict


    def initialise_data(self):
        ''' Create a numpy array of 0s. '''
        # MAKE dtype INT
        return np.zeros(NUM_SAMPLES,dtype=int)


    def roll_data(self, data):
        ''' Rolls <data> by one sample. '''
        # using slices is 2.5 times faster than using np.roll
        data[:-1] = data[1:]
        return data


    def update(self):
        ''' Update the plot curves with new data. SYNTHETIC DATA '''
        dispatcher.send(message=NUM_SAMPLES, sender='main', signal='request_data')
        self.text.setText('screen refresh rate: {:0.1f}'.format(
            self.graph_update_rate(), color=(255,255,0)))
        self.curve0.setData(self.mb_dict['mb_0'])
        self.curve1.setData(self.mb_dict['mb_1'])
        self.curve2.setData(self.mb_dict['mb_2'])
        for data in self.mb_dict.values():
            data = self.roll_data(data)
        self.app.processEvents()


if __name__ == '__main__':
    logging.info('starting MicrobitJuggle ')
    microbit_juggling = MicrobitJuggle(num_microbits=3)
    timer = QtCore.QTimer()
    timer.timeout.connect(microbit_juggling.update)
    # timer units are milliseconds. timer.start(0) to go as fast as practical.
    timer.start(1000/SCREEN_REFRESH_RATE)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_'):
        QtGui.QApplication.instance().exec_()

