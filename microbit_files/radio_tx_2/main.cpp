/*
Transmit accelerometer data on the BBC micro:bit
Send through radio
v1.0 May 2018 Matthew Oppenheim
*/

#include "MicroBit.h"

MicroBit uBit;
int COUNT = 0;
// ID of this transmitter
int ID = 2;
// string sent by the receiver to this unit to select it
char ID_STR[5] = "mb_2";
// string displayed on this microbit's LEDs
char ID_DISPLAY[2] = "2";

// Default serial 115200 baud, 8N1

const uint8_t big_t_arr[] {
    1, 1, 1, 1, 1,
    0, 0, 1, 0, 0,
    0, 0, 1, 0, 0,
    0, 0, 1, 0, 0,
    0, 0, 1, 0, 0,
};

MicroBitImage big_t(5,5,big_t_arr);

struct AccData {
    /* accelerometer data structure */
    int x_acc;
    int y_acc;
    int z_acc;
};

struct AccString {
    /* accelerometer data structure using ManagedString */
    ManagedString xString;
    ManagedString yString;
    ManagedString zString;
};

AccData getAcc()
/* return x,y,z accelerometer AccData */
{
    AccData acc;
    acc.x_acc = uBit.accelerometer.getX();
    acc.y_acc = uBit.accelerometer.getY();
    acc.z_acc = uBit.accelerometer.getZ();
    return(acc);
};

AccString getAccString()
/* return x,y,z accelerometer AccString */
{
    AccString accString;
    accString.xString = uBit.accelerometer.getX();
    accString.yString = uBit.accelerometer.getY();
    accString.zString = uBit.accelerometer.getZ();
    return(accString);
};

void transmit_sensors()
// send sensor data over radio
{
    AccString accString;
    ManagedString start_mark("ST");
    ManagedString end_mark("EN");
    accString = getAccString();
    uBit.radio.datagram.send(start_mark + "," + ID + "," + COUNT + "," +
    accString.xString + "," + accString.yString + "," +
    accString.zString + "," + end_mark);
    COUNT += 1;
}

void onData(MicroBitEvent)
// send sensor data over radio
{
    ManagedString s = uBit.radio.datagram.recv();
    if (s == ID_STR)
        transmit_sensors();
}

int main()
{
    uBit.init();
    uBit.display.print(ID_DISPLAY);
    uBit.radio.enable();
    uBit.radio.setGroup(10);
    uBit.messageBus.listen(MICROBIT_ID_RADIO, MICROBIT_RADIO_EVT_DATAGRAM, onData);
    while (1) {
        uBit.sleep(500);
        release_fiber();
    }
}

