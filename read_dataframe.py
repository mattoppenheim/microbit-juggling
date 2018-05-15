''' Read data from pandas dataframe.
For the microbit juggling project.
Return the last x accelerometer scans from the microbit accelerometer
dataframe.

Pandas dataframe row format is:
'time', 'id', 'count', 'x_acc', 'y_acc', 'z_acc', 'mag_acc'

'mag_acc' is the absoulte acceleration, sqrt(x^2+y^2+z^2)

dispatcher message is of format:
microbit dataframe, number of scans

Matthew Oppenheim May 2108'''

from io import StringIO
import pandas as pd
from pydispatch import dispatcher


DF_COL_NAMES = ['time', 'id', 'count', 'x_acc', 'y_acc', 'z_acc', 'mag_acc']


TEST_DATA = StringIO("""2018-05-14 16:26:22.465195,1,30,-240,336,240,477
2018-05-14 16:26:23.396913,1,31,-1472,208,32,1486
2018-05-14 16:26:24.325855,1,32,-752,192,224,807
2018-05-14 16:26:25.253932,1,33,-1920,208,-80,1932
2018-05-14 16:26:26.183994,1,34,272,336,-272,510
2018-05-14 16:26:27.109257,1,35,-1808,128,-288,1835
2018-05-14 16:26:28.040290,1,36,-272,400,-352,598
2018-05-14 16:26:28.970327,1,37,-1680,144,-272,1707
2018-05-14 16:26:29.898358,1,38,-2032,288,-288,2072
2018-05-14 16:26:30.828075,1,39,-992,240,-528,1149
2018-05-14 16:26:31.759633,1,40,320,496,-352,687
2018-05-14 16:26:32.691503,1,41,-1456,288,-272,1508
2018-05-14 16:26:33.621250,1,42,-848,208,-560,1037
2018-05-14 16:26:34.552612,1,43,336,400,-224,568
2018-05-14 16:26:35.483881,1,44,-1184,224,-576,1335
2018-05-14 16:26:36.415481,1,45,432,352,-224,600
2018-05-14 16:26:37.346161,1,46,-2032,352,-656,2164""")

dispatcher.connect(dispatcher_receive, signal='get_data', sender='main')


def dispatcher_receive(message):
    ''' Handle dispatcher message. '''
    # message is of form microbit dataframe, number of scans to extract
    microbit_df, scans = message
    get_mag_acc(microbit_df, scans)


def dispatcher_send(message_txt, signal, sender):
    ''' Use dispatcher to send message_txt. '''
    dispatcher.send(signal=signal, message=message_txt, sender=sender)


def get_mag_acc(df, scans):
    ''' Return the last <scans> of mag_acc from df. '''
    mag_acc = df.loc[df.index[-scans:],'mag_acc'].values.tolist()
    dispatcher_send(mag_acc, signal='mag_acc_list', sender='read_dataframe')


if __name__ == '__main__':
    scans = 5
    test_df = pd.read_csv(TEST_DATA, header=None, index_col=0, names=DF_COL_NAMES)
    print(test_df)
    print(test_df.loc[test_df.index[-scans:],'mag_acc'].values.tolist())
    print(get_mag_acc(test_df, scans))
