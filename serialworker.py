#!/usr/bin/python

import serial
import time
import multiprocessing
import settings
import sqlite3
import npbc_communication
import binascii

class SerialProcess(multiprocessing.Process):
    def __init__(self, serial_port, serial_baudrate):
        multiprocessing.Process.__init__(self)
        #self.sp = serial.Serial(serial_port, serial_baudrate, timeout=1)

    #def close(self):
        #self.sp.close()

    def writeSerial(self, data):
        self.sp.write(data)
        # time.sleep(1)

    def readSerial(self):
        return self.sp.readline().replace("\n", "")

    def run(self):

        #self.sp.flushInput()

        while True:
            print "serialworker..."

            request = npbc_communication.generalInformationCommand().getRequestData()
            print binascii.hexlify(request)
            response = npbc_communication.generalInformationCommand().processResponseData(bytearray([0x5A, 0x5A, 0x1D, 0x16, 0x14, 0x12, 0x53, 0x07, 0x1B, 0x18, 0x1D, 0x09, 0x09, 0x0D, 0x0B, 0x8C,
                                    0x0D, 0x0E, 0x0F, 0x4C, 0x46, 0x92, 0x13, 0x14, 0x1D, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0xB7]))
            print binascii.hexlify(response.RawData)

            dbconn = sqlite3.connect(settings.DATABASE)
            dbconn.execute("INSERT INTO [BurnerLogs] ([Date]) VALUES (datetime())")
            dbconn.commit()
            time.sleep(10)
