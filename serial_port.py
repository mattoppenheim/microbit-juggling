''' Creates a serial port for the microbit.
Matthew Oppenheim May 2018. '''

import logging
import serial
import serial.tools.list_ports as list_ports
from time import sleep

BAUD = 115200
PID_MICROBIT = 516
VID_MICROBIT = 3368
TIMEOUT = 0.1

logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class SerialPort():
    def __init__(self, pid=PID_MICROBIT, vid=VID_MICROBIT, baud=BAUD, timeout=TIMEOUT):
        self.serial_port = self.open_serial_port(pid, vid, baud, timeout)


    def count_same_ports(self, ports, pid, vid):
        ''' Count how many ports with pid and vid are in <ports>. '''
        return len([p for p in ports if p.pid==pid and p.vid==vid])


    def get_serial_data(self, serial_port):
        ''' get serial port data '''
        inWaiting = serial_port.inWaiting()
        read_bytes = serial_port.readline(inWaiting)
        if not read_bytes:
            return
        return read_bytes.decode()


    def get_serial_port(self):
        ''' Return the serial port. '''
        return self.serial_port


    def open_serial_port(self, pid=PID_MICROBIT, vid=VID_MICROBIT, baud=BAUD, timeout=TIMEOUT):
        ''' open a serial connection '''
        print('looking for attached microbit on a serial port')
        # serial = find_comport(pid, vid, baud)
        serial_port = serial.Serial(timeout=timeout)
        serial_port.baudrate = baud
        ports = list(list_ports.comports())
        print('scanning ports')
        num_mb = self.count_same_ports(ports, pid, vid)
        logging.info('{} microbits found'.format(num_mb))
        if num_mb>1:
            logging.info('**** check for false connections ****')
        ports.sort(reverse=True)
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
        # except (AttributeError, SerialException) as e:
        except Exception as e:
            print('cannot open serial port: {}'.format(e))
            return None
        # 100ms delay
        sleep(0.1)
        return serial_port


if __name__ == '__main__':
    print('instatiating SerialPort()')
    serial_port = SerialPort()
    print('finished')
