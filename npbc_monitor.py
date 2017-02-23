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

class GetInfoHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', [Timestamp]) AS [Timestamp], strftime('%Y-%m-%dT%H:%M:%f', [Date]) AS [Date], [Power] FROM [BurnerLogs] WHERE [Timestamp] >= datetime('now', '-12 hours')")

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()

def initializeDatabase():
    dbconn = sqlite3.connect(settings.DATABASE)
    dbconn.execute("CREATE TABLE IF NOT EXISTS [BurnerLogs] ( \
                           [Timestamp] DATETIME PRIMARY KEY, \
                           [SwVer] NVARCHAR NOT NULL, \
                           [Date] DATETIME NOT NULL, \
                           [Mode] INTEGER NOT NULL, \
                           [State] INTEGER NOT NULL, \
                           [Status] INTEGER NOT NULL, \
                           [IgnitionFail] TINYINT NOT NULL, \
                           [PelletJam] TINYINT NOT NULL, \
                           [Tset] INTEGER NOT NULL, \
                           [Tboiler] INTEGER NOT NULL, \
                           [Flame] INTEGER NOT NULL, \
                           [Heater] TINYINT NOT NULL, \
                           [CHPump] TINYINT NOT NULL, \
                           [BF] TINYINT NOT NULL, \
                           [FF] TINYINT NOT NULL, \
                           [Fan] INTEGER NOT NULL, \
                           [Power] INTEGER NOT NULL, \
                           [ThermostatStop] TINYINT NOT NULL)")
    dbconn.commit()

if __name__ == '__main__':
    ## Initialize database
    initializeDatabase()

    ## start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess()
    sp.daemon = True
    sp.start()

    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/api/getInfo", GetInfoHandler)
        ]
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print "Listening on port:", options.port

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()
