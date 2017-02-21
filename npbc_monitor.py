#!/usr/bin/python

import os
import time
import multiprocessing
import serialworker
import json
import sqlite3
import settings
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options

define("port", default=settings.WEB_UI_PORT, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('main.js')

if __name__ == '__main__':
    ## Initialize database
    dbconn = sqlite3.connect(settings.DATABASE)
    dbconn.execute("CREATE TABLE IF NOT EXISTS [BurnerLogs] ([Date] DATETIME PRIMARY KEY)")
    dbconn.commit()

    ## start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess()
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
