#!/usr/bin/python

class commandBase(object):
    __header = [0x5A, 0x5A]

    def __init__(self, commandId):
        self.__commandId = commandId
        self.IsSuccessful = False

    def getRequestData(self, data):
        request = bytearray()
        
        # data length = 1 byte command Id + requestData.Length + 1 byte checksum
        request.append(len(data) + 2)
        
        # command Id
        request.append(self.__commandId)
        
        # request data
        request.extend(data)
        
        # checksum
        request.append(self.__calculateCheckSum(request))

        # increment request data values
        for i in range(2, len(data) + 3, 1):
            request[i] = request[i] + i - 1

        # header
        for i in range(len(self.__header) - 1, -1, -1):
            request.insert(0, self.__header[i])

        return request

    def processResponseData(self, data):
        self.IsSuccessful = False
        response = bytearray()
        
        if (len(data) < len(self.__header) + 2):
            print "Invalid response"
            return bytearray()

        return response

    def __calculateCheckSum(self, data):
        return (sum(data) % 256) ^ 0xFF


class generalInformationCommand(commandBase):
    def __init__(self):
        super(generalInformationCommand, self).__init__(0x01)

    def getRequestData(self):
        super(generalInformationCommand, self).processResponseData(bytearray([1, 2, 3, 4]))
        return super(generalInformationCommand, self).getRequestData(bytearray())
