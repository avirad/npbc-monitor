#!/usr/bin/python

class failResponse(object):
    pass


class successResponse(object):
    def __init__(self, data):
        self.RawData = data


class generalInformationResponse(successResponse):
    def __init__(self, data):
        super(generalInformationResponse, self).__init__(data)
        self.SwVer = None
        self.Date = None
        self.Mode = None
        self.State = None
        self.Status = None
        self.IgnitionFail = None
        self.PelletJam = None
        self.Tset = None
        self.Tboiler = None
        self.Flame = None
        self.Heater = None
        self.CHPump = None
        self.BF = None
        self.FF = None
        self.Fan = None
        self.Power = None
        self.ThermostatStop = None


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

        # check header
        for i in range(len(self.__header)):
            if (data[i] != self.__header[i]):
                print "Invalid response header"
                return bytearray()

        # check length
        if (len(data) != len(self.__header) + 1 + data[len(self.__header)]):
            print "Invalid response length"
            return bytearray()

        for i in range(2, len(data) - 1, 1):
            response.append(data[i])

        # decrement response data values
        for i in range(1, len(response), 1):
            response[i] = response[i] - i + 1

        # checksum validation
        if (data[len(data) - 1] != self.__calculateCheckSum(response) + len(response) - 1):
            print "Response checksum validation failed"
            return bytearray()

        del response[0:1]

        self.IsSuccessful = True
        return response

    def __calculateCheckSum(self, data):
        return (sum(data) & 0xFF) ^ 0xFF


class generalInformationCommand(commandBase):
    def __init__(self):
        super(generalInformationCommand, self).__init__(0x01)

    def getRequestData(self):
        return super(generalInformationCommand, self).getRequestData(bytearray())

    def processResponseData(self, response):
        try:
            responseData = super(generalInformationCommand, self).processResponseData(response)
        except:
            self.IsSuccessful = False

        if (self.IsSuccessful == True):
            return generalInformationResponse(responseData)
        else:
            return failResponse()


class setBoilerTemperatureCommand(commandBase):
    def __init__(self, boilerTemperature):
        super(setBoilerTemperatureCommand, self).__init__(0x07)
        self.__boilerTemperature = boilerTemperature

    def getRequestData(self):
        return super(setBoilerTemperatureCommand, self).getRequestData(bytearray(self.__boilerTemperature))

    def processResponseData(self, response):
        try:
            responseData = super(setBoilerTemperatureCommand, self).processResponseData(response)
        except:
            self.IsSuccessful = False

        if (self.IsSuccessful == True and len(responseData) == 1 and responseData[0] == 0x34):
            return successResponse(responseData)
        else:
            return failResponse()
