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

        dbconn = sqlite3.connect(settings.DATABASE)

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

                        params = [response.SwVer, response.Date, response.Mode, response.State, response.Status, response.IgnitionFail, response.PelletJam, response.Tset, response.Tboiler, response.Flame,
                                   response.Heater, response.CHPump, response.BF, response.FF, response.Fan, response.Power, response.ThermostatStop]

                        dbconn.execute("INSERT INTO [BurnerLogs] ([Timestamp], [SwVer], [Date], [Mode], [State], [Status], [IgnitionFail], [PelletJam], [Tset], [Tboiler], [Flame], \
                                               [Heater], [CHPump], [BF], [FF], [Fan], [Power], [ThermostatStop]) VALUES (datetime(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
                        dbconn.commit()

            except Exception, e1:
                print "error communicating...: " + str(e1)

            time.sleep(5)
