#!/usr/bin/python

import os
import time
import multiprocessing
from multiprocessing.managers import BaseManager
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
import npbc_communication

define("port", default=settings.WEB_UI_PORT, help="run on the given port", type=int)

burnerStatus = None

class BurnerStatus(object):
    def __init__(self):
        self.BurnerResponse = None

    def SetBurnerStatus(self, response):
        self.BurnerResponse = response

    def GetBurnerStatus(self):
        return self.BurnerResponse


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class GetInfoHandler(tornado.web.RequestHandler):
    def get(self):
        result = {}
        status = burnerStatus.GetBurnerStatus()

        if (isinstance(status, npbc_communication.generalInformationResponse)):
            result['SwVer'] = status.SwVer
            result['Date'] = status.Date.isoformat()
            result['Mode'] = status.Mode
            result['State'] = status.State
            result['Status'] = status.Status
            result['IgnitionFail'] = status.IgnitionFail
            result['PelletJam'] = status.PelletJam
            result['Tset'] = status.Tset
            result['Tboiler'] = status.Tboiler
            result['Flame'] = status.Flame
            result['Heater'] = status.Heater
            result['CHPump'] = status.CHPump
            result['BF'] = status.BF
            result['FF'] = status.FF
            result['Fan'] = status.Fan
            result['Power'] = status.Power
            result['ThermostatStop'] = status.ThermostatStop

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")


class GetStatsHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', [Timestamp]) AS [Timestamp], [Power], [Flame], [Tset], [Tboiler] \
                          FROM [BurnerLogs] WHERE [Timestamp] >= datetime('now', '-2 hours')")

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()


class GetConsumptionStatsHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', datetime(t.[Date])) AS [Timestamp], \
                               ifnull((SELECT SUM([FFWorkTime]) \
                                         FROM [BurnerLogs] AS BL \
                                        WHERE BL.[TimeStamp] BETWEEN datetime(t.[Date]) AND datetime(t.[Date], '+3599 seconds')), \
                                      0) as [FFWorkTime] \
                          FROM (SELECT datetime('now', '-' || (60 * (a.[a] + (10 * b.[a]) + (100 * c.[a]))) || ' minutes') AS [Date] \
                                  FROM (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS a \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS b \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS c \
                               ) AS t \
                         WHERE t.[Date] BETWEEN datetime('now', '-24 hours') AND datetime('now') \
                         ORDER BY t.[Date]")

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
                           [ThermostatStop] TINYINT NOT NULL, \
                           [FFWorkTime] INTEGER NOT NULL)")
    dbconn.commit()

if __name__ == '__main__':
    ## Initialize database
    initializeDatabase()

    manager = BaseManager()
    manager.register('BurnerStatus', BurnerStatus)
    manager.start()

    burnerStatus = manager.BurnerStatus()

    ## start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess(burnerStatus)
    sp.daemon = True
    sp.start()

    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/api/getInfo", GetInfoHandler),
            (r"/api/getStats", GetStatsHandler),
            (r"/api/getConsumptionStats", GetConsumptionStatsHandler)
        ]
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print "Listening on port:", options.port

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()
