#!/usr/bin/python

import serial
import time
import multiprocessing
import settings
import sqlite3
import npbc_communication
import binascii

class SerialProcess(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):
        sp = serial.Serial(settings.SERIAL_PORT, settings.SERIAL_BAUDRATE, timeout=1)
        print "communicating on port: " + sp.portstr

        while (sp.is_open):
            try:
                time.sleep(0.1)
                sp.reset_input_buffer()
                sp.reset_output_buffer()

                time.sleep(0.1)
                requestData = npbc_communication.generalInformationCommand().getRequestData()
                sp.write(requestData)

                time.sleep(0.5)
                responseData = bytearray([0x5A, 0x5A, 0x1D, 0x16, 0x14, 0x12, 0x53, 0x07, 0x1B, 0x18, 0x1D, 0x09, 0x09, 0x0D, 0x0B, 0x8C,
                                          0x0D, 0x0E, 0x0F, 0x4C, 0x46, 0x92, 0x13, 0x14, 0x1D, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0xB7])
                if (sp.in_waiting > 0):
                    responseData = bytearray(sp.read(sp.in_waiting))

                if (len(responseData) > 0):
                    response = npbc_communication.generalInformationCommand().processResponseData(responseData)

                    if (isinstance(response, npbc_communication.failResponse)):
                        print "failResponse() received"

                    if (isinstance(response, npbc_communication.generalInformationResponse)):
                        print "generalInformationResponse() received"

            except Exception, e1:
                print "error communicating...: " + str(e1)

            #request = npbc_communication.generalInformationCommand().getRequestData()
            #print binascii.hexlify(request)

            #response = npbc_communication.generalInformationCommand().processResponseData(bytearray([0x5A, 0x6A, 0x1D, 0x16, 0x14, 0x12, 0x53, 0x07, 0x1B, 0x18, 0x1D, 0x09, 0x09, 0x0D, 0x0B, 0x8C,
            #                        0x0D, 0x0E, 0x0F, 0x4C, 0x46, 0x92, 0x13, 0x14, 0x1D, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0xB7]))
            #print binascii.hexlify(response.RawData)

            #response = npbc_communication.setBoilerTemperatureCommand(59).processResponseData(bytearray([0x5A, 0x5A, 0x02, 0x34, 0xCA]))
            #print binascii.hexlify(response.RawData)

            dbconn = sqlite3.connect(settings.DATABASE)
            dbconn.execute("INSERT INTO [BurnerLogs] ([Date]) VALUES (datetime())")
            dbconn.commit()
            time.sleep(5)
