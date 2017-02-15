import serial
import time
import multiprocessing

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
            time.sleep(10)
