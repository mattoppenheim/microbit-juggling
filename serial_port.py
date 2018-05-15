''' Creates a serial port for the microbit.
Matthew Oppenheim May 2018. '''

import serial
import serial.tools.list_ports as list_ports
from time import sleep

BAUD = 115200
PID_MICROBIT = 516
VID_MICROBIT = 3368
TIMEOUT = 0.1

class SerialPort():
    def __init__(self, pid=PID_MICROBIT, vid=VID_MICROBIT, baud=BAUD, timeout=TIMEOUT):
        self.open_serial_port(pid, vid, baud, timeout)


    def open_serial_port(self, pid=PID_MICROBIT, vid=VID_MICROBIT, baud=BAUD, timeout=TIMEOUT):
        ''' open a serial connection '''
        print('looking for attached microbit on a serial port')
        # serial = find_comport(pid, vid, baud)
        serial_port = serial.Serial(timeout=timeout)
        serial_port.baudrate = baud
        ports = list(list_ports.comports())
        print('scanning ports')
        for p in ports:
            print('pid: {} vid: {}'.format(p.pid, p.vid))
            if (p.pid == pid) and (p.vid == vid):
                print('found target device pid: {} vid: {} port: {}'.format(
                    p.pid, p.vid, p.device))
                serial_port.port = str(p.device)
        if not serial:
            print('no serial port found')
            return None
        try:
            serial_port.open()
            serial_port.flush()
            print('opened serial port: {}'.format(serial))
        except AttributeError as e:
            print('cannot open serial port: {}'.format(e))
            return None
        # 100ms delay
        sleep(0.1)
        return serial_port