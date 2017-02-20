#!/usr/bin/python

class GeneralInformationCommand():
    def getRequest(self):
        return bytearray([0x5A, 0x5A, 0x02, 0x01, 0xFD])
