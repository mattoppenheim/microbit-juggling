<h1>Real time data display python scripts.</h1>

Real time sensor data display with Python 3.
Example using BBC micro:bits. Three BBC micro:bits are polled to collect their accelerometer data. This is displayed real time.
 Uses pyqtgraph for the data display.
 Uses pydispatcher to communicate between the data collection thread and the real time data display thread.

A receiver microbit is attached to the laptop.
The C code for this is in radio-rx-2.c. Load radio-rx-2-combined.hex on to the receiver microbit.
Three transmitter microbits are polled to send accelerometer data.
The C code for these is radio-tx-2.c.
The ID for each transmitter needs to be changed in the code to be 0,1,2.
Load radio-tx-2-combined.hex on to the receiver microbits.

Only valid for micro:bit v1. Not test on v2 of the board.

 Matthew Oppenheim 2018-2021
