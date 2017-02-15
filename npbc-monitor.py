import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options
import os
import time
import multiprocessing
import serialworker
import json

## Change this to match your local settings
SERIAL_PORT = 'COM1'
SERIAL_BAUDRATE = 9600
WEB_UI_PORT = 8080
##

define("port", default=WEB_UI_PORT, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('main.js')

if __name__ == '__main__':
    ## start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess(SERIAL_PORT, SERIAL_BAUDRATE)
    sp.daemon = True
    sp.start()
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {'path':  './'})
        ]
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print "Listening on port:", options.port

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()