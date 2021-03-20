/* Receive BC Micro:bit radio data and transmit through serial port
v0.0 Nov 2017 Matthew Oppenheim
*/

#include "MicroBit.h"

MicroBit uBit;

// Default serial 115200 baud, 8N1

const uint8_t big_r_arr[] {
    1, 1, 1, 1, 1,
    1, 0, 0, 1, 0,
    1, 0, 1, 0, 0,
    1, 0, 0, 1, 0,
    1, 0, 0, 0, 1,
};

MicroBitImage big_r(5,5,big_r_arr);

void onData(MicroBitEvent)
// send received data to serial port
{
    // uBit.serial.send(" rx ");
    ManagedString s = uBit.radio.datagram.recv();
    // int rssi = uBit.radio.getRSSI();
    uBit.serial.send(s);
    // uBit.serial.send(rssi);
}

void onSerial(MicroBitEvent)
// react to incoming serial data
{
    ManagedString s = uBit.serial.readUntil("\n");
    if (s=="mb_0")
    {
        // poll sensor 0
        uBit.radio.datagram.send("mb_0");
        uBit.display.print(big_r);
    }
    if (s=="mb_1")
    {
        // poll sensor 1
        uBit.radio.datagram.send("mb_1");
        uBit.display.print(big_r);
    }
    if (s=="mb_2")
    {
        // poll sensor 2
        uBit.radio.datagram.send("mb_2");
        uBit.display.print(big_r);
    }
    uBit.serial.eventAfter(1);
    // uBit.serial.send("test " + s);
}

int main()
{
    uBit.init();
    uBit.serial.baud(115200);
    uBit.serial.setRxBufferSize(24);
    uBit.display.print(big_r);
    uBit.messageBus.listen(MICROBIT_ID_RADIO, MICROBIT_RADIO_EVT_DATAGRAM, onData);
    uBit.messageBus.listen(MICROBIT_ID_SERIAL, MICROBIT_SERIAL_EVT_HEAD_MATCH, onSerial);
    uBit.serial.eventAfter(1);
    uBit.radio.enable();
    //uBit.radio.setFrequencyBand(30);
    uBit.radio.setGroup(10);
    while(1)
    {
        uBit.sleep(500);
        release_fiber();
    }
}

