''' Sends messages to BBC Micro:bits to retrieve their accelerometer sensor data.
Needs a microbit mounted on a USB port to act as the transmitter.
This class sends messages with a target ID to the transmitter microbit.
The transmitter microbit transmits these messages.
The receiver microbit matching the ID transmits its accelerometer data.
The transmitter microbit passes this data back through the USB port.

input: ManagedStrings from microbit
format: ST,count,x_acc,y_acc,z_acc,adc, EN
output: parse and display the accelerometer data for each microbit
Uses a pandas dataframe for storing data for each microbit
Incoming scans from the microbit are parsed to a one row dataframe
for each scan
These scan dataframes are reconfigured and added to the microbit dataframe
For a single microbit, we can tack partial scans together.
with multiple microbits, we don't know where the partial scans come from
So we can only parse complete scans
optparse used for argument parsing as this works with the notebook as well as scripts '''


from datetime import datetime
from pydispatch import dispatcher
import logging
import math
from serial_port import SerialPort
import numpy as np
from optparse import OptionParser
import sys
from serial_port import SerialPort
from time import sleep
import pandas as pd
import pathlib


BAUD = 115200
DF_COL_NAMES = ['time', 'id', 'count', 'x_acc', 'y_acc', 'z_acc', 'mag_acc']
SCAN_DELAY = 0.1
SCAN_COL_NAMES = ['id', 'count', 'x_acc', 'y_acc', 'z_acc']
START_SCAN = 'ST'
END_SCAN = 'EN'
MAX_ROWS = 500
PID_MICROBIT = 516
VID_MICROBIT = 3368
TIMEOUT = 0.1
OUT_FILEPATH = '/home/matthew/data/documents/infolab21/progs/jupyter_notebooks/microbit/out_data.txt'

logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def now_time():
    '''returns the local time as a string'''
    now = datetime.now()
    return now.strftime("%H:%M:%S.%f")


def system_exit(message):
    ''' quit script '''
    print('system exit: {}'.format(message))
    sys.exit(0)


class ReadMicrobits():
    def __init__(self, num_microbits=3):
        self.num_microbits = num_microbits
        logging.info('logging {} microbits'.format(self.num_microbits))
        dispatcher.connect(self.dispatcher_receive_data_request,
            signal='request_data', sender='main')
        self.main()


    def calc_mag(self, df_scan):
        ''' calculate mag_acc from x, y, z acceleration in df_scan '''
        mag_acc = int(math.sqrt(df_scan['x_acc']**2 +
            df_scan['y_acc']**2 + df_scan['z_acc']**2))
        return mag_acc


    def check_for_duplicate_counts(self, df_scan, df_dict):
        ''' flag if there are any duplicates in the count column '''
        # print('df_scan[\'count\']:{}'.format(df_scan['count'].values[0]))
        if df_scan['count'].values[0] in set(df_dict['count']):
            print('found replicated count: {} id: {}'.format(
                df_scan['count'].values[0], df_scan['id'].values[0]))


    def create_blank_scan(self, ident):
        ''' create a scan with NaN for all sensor values '''
        blank_scan = [np.nan] * len(SCAN_COL_NAMES)
        id_index = SCAN_COL_NAMES.index('id')
        blank_scan[id_index] = ident
        blank_scan.insert(0, START_SCAN)
        blank_scan[-1] = END_SCAN
        blank_scan = ','.join(str(a) for a in blank_scan)
        return blank_scan


    def create_df_dict(self):
        ''' create a dictionary of dataframes to store the microbit data '''
        mb_names = ['mb_{}'.format(id_x) for id_x in range(self.num_microbits)]
        df_dict = {name: pd.DataFrame(columns=DF_COL_NAMES) for name in mb_names}
        for mb_id in df_dict.keys():
            df_dict[mb_id] = df_dict[mb_id].set_index('time')
            # df_mb = df_mb.set_index('time')
        return df_dict


    def create_df_scan(self, scan, now_time):
        ''' create a df_scan '''
        df_scan = self.unpack_scan(scan)
        df_scan['mag_acc'] = self.calc_mag(df_scan)
        df_scan['time'] = self.timestring(now_time)
        df_scan = df_scan.set_index('time')
        return df_scan


    def create_multi_scans_dict(self):
        ''' create multi_scans lists for keeping scan fragments for each microbit '''
        mb_names = ['mb_{}'.format(id_x) for id_x in range(self.num_microbits)]
        multi_scans_dict = {name:'' for name in mb_names}
        print('multi_scans_dict created: {}'.format(multi_scans_dict))
        return multi_scans_dict


    def create_plot_data(self, num_samples):
        ''' Assemble the data to be dispatched and plotted in main.py. '''
        # Return a dict {mb_id: np array of scans}
        plot_data = {}
        for mb in self.df_dict.keys():
            df = self.df_dict[mb]
            len_df = len(df)
            if len_df < num_samples:
                num_samples = len_df
            # Get the mag_acc column for the last num_samples.
            plot_data[mb] = df.loc[df.index[-num_samples:],
                'mag_acc'].values.tolist()
        return plot_data


    def dispatcher_receive_data_request(self, message):
        ''' Dispatch microbit data. '''
        data_to_send = self.create_plot_data(message)
        dispatcher.send(message=data_to_send,
            sender='read_microbits', signal='plot_data')


    def get_single_scan(self, scans, start_scan=START_SCAN, end_scan=END_SCAN):
        ''' return a single scan and the remainder from scans
        ip: scan plus noise data
        op: single scan '''
        try:
            start = scans.index(start_scan)
            end = scans.index(end_scan, start)+len(end_scan)
            single_scan= scans[start:end]
            return single_scan
        except ValueError as e:
            # print('get_single_scan: {} input: {}'.format(e, scans))
            return ""


    def poll_microbit(self, mb_id, serial_port):
        ''' Poll a microbit connected to serial with its id. '''
        try:
            serial_port.write((mb_id + '\n').encode())
        except AttributeError as e:
                print(e)

    def process_data(self, read_bytes, multi_scans):
        ''' process data from serial port
        return scan: '''
        scan = ''
        multi_scans = multi_scans + read_bytes
        # print('process_data, read_bytes: {}'.format(read_bytes))
        try:
            scan = (self.get_single_scan(read_bytes))
                # if all the scans are processed a ValueError will be raised
                # by get_single_scan
        except ValueError as e:
            print('process_data, ValueError: {}'.format(e))
        return (scan)


    def text_all_scan(self, df_dict):
        ''' create single string of all last scans in df_dict '''
        out_text = []
        for dict in df_dict:
            last_row = df_dict[dict].tail(1)
            last_row_text = last_row.values.flatten().tolist()
            out_text.append(last_row_text)
        return out_text


    def timestring(self, timestamp):
        ''' create a string from timestamp '''
        return timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")


    def trim_df(self, df):
        ''' trim dataframe to be MAX_ROWS long '''
        length = len(df)
        if length > MAX_ROWS:
            excess = length - MAX_ROWS
            df = df.drop(df.index[:excess])
        return df


    def unpack_scan(self, scan):
        ''' unpack a single scan into a DataFrame
        ip: ST,id,count,x_acc,y_acc,z_acc,EN
        op: DataFrame as a single row '''
        if not scan:
            return
        a = (scan.split(','))
        # remove ST and EN markers
        a = a[1:-1]
        a = [int(a[i]) for i in range(len(a))]
        column_names = list(SCAN_COL_NAMES)
        try:
            df = pd.DataFrame([a],columns=column_names)
        except AssertionError as e:
            print('unpack_scan: {}'.format(e))
        return df


    def update_df_dict(self, df_scan, df_mb):
        ''' update df_dict for a microbit with a single scan '''
        df_mb = df_mb.append(df_scan)
        # print('update_df_dict, df_mb.tail(1): {}'.format(df_mb.tail(1)))
        df_mb = df_mb.drop_duplicates(['count'])
        # trim the df to the maximum permitted length
        df_mb = self.trim_df(df_mb)
        return df_mb


    def write_file(self, file_path):
        ''' create a file if it does not exist '''
        path = pathlib.Path(file_path)
        if not path.is_file():
            return


    def main(self):
        parser = OptionParser()
        parser.add_option('-f', '--fake',
                          default='False',
                    help='Fake microbits')
        (options,args) = parser.parse_args()
        print('options:{} args: {}'.format(options, args))
        if options.fake:
            print('Fake microbit option detected')
        # serial = open_serial_port()
        Microbit_Serial_Port = SerialPort()
        serial_port = Microbit_Serial_Port.get_serial_port()
        print('serial_port: {}'.format(serial_port))
        if not serial_port:
            system_exit('microbit not found connected to a serial port')
        # df_dict is a dict of pandas DataFrames, one for each microbit
        self.df_dict = self.create_df_dict()
        microbits = [a for a in sorted(self.df_dict.keys())]
        print('microbit id\'s: {}'.format(microbits))
        old_time = datetime.now()
        while (1):
            # have base station act as controller and poll each of the sensor microbits
            now_time = datetime.now()
            # time_delta = now_time - old_time
            # old_time = now_time
            # print(time_delta.total_seconds())
            # print(text_all_scan(df_dict))
            for mb_id in microbits:
                # poll each microbit in turn by transmitting their id
                sleep(SCAN_DELAY/2)
                self.poll_microbit(mb_id, serial_port)
                # scan = ''
                # requested data, now wait for data, then read data

                # This sleep command controls the frequency of data collection.
                sleep(SCAN_DELAY/2)
                print('polling: {}'.format(mb_id))
                read_bytes = Microbit_Serial_Port.get_serial_data(serial_port)
                # If no receipt, the mb_id stays in the serial buffer. Tried serial.flush().
                if read_bytes in microbits:
                    print('*** id only, polling: {} read_bytes: {}, continuing'.format(mb_id, read_bytes))
                    continue
                if not read_bytes:
                    print('*** no read_bytes mb_id: {}'.format(mb_id))
                    continue
                try:
                    scan = self.get_single_scan(read_bytes)
                except (TypeError, ValueError, AttributeError) as e:
                    print('get_single_scan error: {}'.format(e))
                    scan = self.create_blank_scan(mb_id)
                if len(scan.split(',')) != len(SCAN_COL_NAMES)+2:
                    print('*** short scan: {} mb_id: {} read_bytes: {}'.format(
                        scan, mb_id, read_bytes))
                    continue
                df_scan = self.create_df_scan(scan, now_time)
                # get microbit id from scan
                ident = 'mb_{}'.format(df_scan['id'].values[0])
                # check_for_duplicate_counts(df_scan, df_dict[ident])
                print('scan: {} mb_id: {} ident:{}'.format(scan, mb_id, ident))
                self.df_dict[ident] = self.update_df_dict(df_scan,
                    self.df_dict[ident])
                #  print(df_dict[ident].to_csv())


if __name__ == '__main__':
    print('starting ReadMicrobits')
    sys.argv = ['--fake', 'True']
    print('now_time: {}'.format(now_time()))
    read_microbits = ReadMicrobits(num_microbits=2)
