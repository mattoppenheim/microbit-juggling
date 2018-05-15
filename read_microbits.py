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
import math
import numpy as np
from optparse import OptionParser
import pandas as pd
import pathlib
import serial
import serial.tools.list_ports as list_ports
import sys
from time import sleep


BAUD = 115200
DF_COL_NAMES = ['time', 'id', 'count', 'x_acc', 'y_acc', 'z_acc', 'mag_acc']
SCAN_DELAY = 0.4
SCAN_COL_NAMES = ['id', 'count', 'x_acc', 'y_acc', 'z_acc']
START_SCAN = 'ST'
END_SCAN = 'EN'
MAX_ROWS = 500
NUM_MICROBITS = 2
PID_MICROBIT = 516
VID_MICROBIT = 3368
TIMEOUT = 0.1
OUT_FILEPATH = '/home/matthew/data/documents/infolab21/progs/jupyter_notebooks/microbit/out_data.txt'


def calc_mag(df_scan):
    ''' calculate mag_acc from x, y, z acceleration in df_scan '''
    mag_acc = int(math.sqrt(df_scan['x_acc']**2 +
        df_scan['y_acc']**2 + df_scan['z_acc']**2))
    return mag_acc


def check_for_duplicate_counts(df_scan, df_dict):
    ''' flag if there are any duplicates in the count column '''
    # print('df_scan[\'count\']:{}'.format(df_scan['count'].values[0]))
    if df_scan['count'].values[0] in set(df_dict['count']):
        print('found replicated count: {} id: {}'.format(
            df_scan['count'].values[0], df_scan['id'].values[0]))


def create_blank_scan(ident):
    ''' create a scan with NaN for all sensor values '''
    blank_scan = [np.nan] * len(SCAN_COL_NAMES)
    id_index = SCAN_COL_NAMES.index('id')
    blank_scan[id_index] = ident
    blank_scan.insert(0, START_SCAN)
    blank_scan[-1] = END_SCAN
    blank_scan = ','.join(str(a) for a in blank_scan)
    return blank_scan


def create_df_dict():
    ''' create a dictionary of dataframes to store the microbit data '''
    mb_names = ['mb_{}'.format(id_x) for id_x in range(NUM_MICROBITS)]
    df_dict = {name: pd.DataFrame(columns=DF_COL_NAMES) for name in mb_names}
    for mb_id in df_dict.keys():
        df_dict[mb_id] = df_dict[mb_id].set_index('time')
        # df_mb = df_mb.set_index('time')
    return df_dict


def create_df_scan(scan, now_time):
    ''' create a df_scan '''
    df_scan = unpack_scan(scan)
    df_scan['mag_acc'] = calc_mag(df_scan)
    df_scan['time'] = timestring(now_time)
    df_scan = df_scan.set_index('time')
    return df_scan


def create_multi_scans_dict():
    ''' create multi_scans lists for keeping scan fragments for each microbit '''
    mb_names = ['mb_{}'.format(id_x) for id_x in range(NUM_MICROBITS)]
    multi_scans_dict = {name:'' for name in mb_names}
    print('multi_scans_dict created: {}'.format(multi_scans_dict))
    return multi_scans_dict


def get_serial_data(serial):
    ''' get serial port data '''
    inWaiting = serial.inWaiting()
    read_bytes = serial.readline(inWaiting)
    if not read_bytes:
        return
    return read_bytes.decode()


def get_single_scan(scans, start_scan=START_SCAN, end_scan=END_SCAN):
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


def open_serial_port(pid=PID_MICROBIT, vid=VID_MICROBIT, baud=BAUD, timeout=TIMEOUT):
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


def poll_microbit(mb_id, serial):
    ''' Poll a microbit connected to serial with its id. '''
    try:
        serial.write((mb_id + '\n').encode())
    except AttributeError as e:
            print(e)

def process_data(read_bytes, multi_scans):
    ''' process data from serial port
    return scan: '''
    scan = ''
    multi_scans = multi_scans + read_bytes
    # print('process_data, read_bytes: {}'.format(read_bytes))
    try:
        scan = (get_single_scan(read_bytes))
            # if all the scans are processed a ValueError will be raised
            # by get_single_scan
    except ValueError as e:
        print('process_data, ValueError: {}'.format(e))
    return (scan)


def system_exit(message):
    ''' quit script '''
    print('system exit: {}'.format(message))
    sys.exit(0)


def text_all_scan(df_dict):
    ''' create single string of all last scans in df_dict '''
    out_text = []
    for dict in df_dict:
        last_row = df_dict[dict].tail(1)
        last_row_text = last_row.values.flatten().tolist()
        out_text.append(last_row_text)
    return out_text


def timestring(timestamp):
    ''' create a string from timestamp '''
    return timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")


def trim_df(df):
    ''' trim dataframe to be MAX_ROWS long '''
    length = len(df)
    if length > MAX_ROWS:
        excess = length - MAX_ROWS
        df = df.drop(df.index[:excess])
    return df


def unpack_scan(scan):
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


def update_box(text_box, df_data, col_name):
    ''' update text_box with current, max, min from df '''
    acc_col = [col for col in df_data.columns if col_name in col]
    current = df_data.iloc[-1][acc_col].values[0]
    try:
        text = 'current: {} max: {} min: {}'.format(
            current,
            int(df_data[acc_col].max().item()),
            int(df_data[acc_col].min().item()))
    except ValueError as e:
        print(e)
        return
    text_box.value = text
    return


def update_df_dict(df_scan, df_mb):
    ''' update df_dict for a microbit with a single scan '''
    df_mb = df_mb.append(df_scan)
    # print('update_df_dict, df_mb.tail(1): {}'.format(df_mb.tail(1)))
    df_mb = df_mb.drop_duplicates(['count'])
    # trim the df to the maximum permitted length
    df_mb = trim_df(df_mb)
    return df_mb


def update_slider(slider, df_data, col_name):
    ''' update range slider with the current reading from df_data['col_name'] '''
    update_col = [col for col in df_data.columns if col_name in col]
    current = df_data.iloc[-1][update_col].values[0]
    if current > 0:
        slider.value = (0, current)
    else:
        slider.value = (current, 0)
    return


def write_file(file_path):
    ''' create a file if it does not exist '''
    path = pathlib.Path(file_path)
    if not path.is_file():
        return


def main():
    parser = OptionParser()
    parser.add_option('-f', '--fake',
                      default='False',
                help='Fake microbits')
    (options,args) = parser.parse_args()
    print('options:{} args: {}'.format(options, args))
    if options.fake:
        print('Fake microbit option detected')
    serial = open_serial_port()
    if not serial:
        system_exit('microbit not found connected to a serial port')
    # df_dict is a dict of pandas DataFrames, one for each microbit
    df_dict = create_df_dict()
    microbits = [a for a in sorted(df_dict.keys())]
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
            poll_microbit(mb_id, serial)
            # scan = ''
            # requested data, now wait for data, then read data

            # This sleep command controls the frequency of data collection.
            # sleep(0.015)
            sleep(SCAN_DELAY/2)
            print('{}: polling'.format(mb_id))
            read_bytes = get_serial_data(serial)
            # If no receipt, the mb_id stays in the serial buffer. Tried serial.flush().
            if read_bytes in microbits:
                print('*** id only, polling: {} read_bytes: {}, continuing'.format(mb_id, read_bytes))
                continue
            if not read_bytes:
                print('*** no read_bytes mb_id: {}'.format(mb_id))
                continue
            try:
                scan = get_single_scan(read_bytes)
            except (TypeError, ValueError, AttributeError) as e:
                print('get_single_scan error: {}'.format(e))
                scan = create_blank_scan(mb_id)
            if len(scan.split(',')) != len(SCAN_COL_NAMES)+2:
                print('*** short scan: {} mb_id: {} read_bytes: {}'.format(
                    scan, mb_id, read_bytes))
                continue
            df_scan = create_df_scan(scan, now_time)
            # get microbit id from scan
            ident = 'mb_{}'.format(df_scan['id'].values[0])
            # check_for_duplicate_counts(df_scan, df_dict[ident])
            print('scan: {} mb_id: {} ident:{}'.format(scan, mb_id, ident))
            df_dict[ident] = update_df_dict(df_scan, df_dict[ident])
            print(df_dict[ident].to_csv())
            trash = serial.read()
            # print('trash: {}'.format(trash))
            serial.flush()


if __name__ == '__main__':
    sys.argv = ['--fake', 'True']
    main()
