#!/usr/bin/python

import os
import time
import multiprocessing
from multiprocessing.managers import BaseManager
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

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class GetInfoHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT [SwVer], [Power], [Flame], [Tset], [Tboiler], [State], [Status] \
                          FROM [BurnerLogs] WHERE [Timestamp] >= datetime('now', '-1 minutes') ORDER BY [Timestamp] DESC LIMIT 1")

        result = []
        rows = cursor.fetchall()
        for row in rows:
            d = dict(zip(row.keys(), row))
            result.append(d)

        self.write(json.dumps(result))
        self.set_header("Content-Type", "application/json")
        cursor.connection.close()


class GetStatsHandler(tornado.web.RequestHandler):
    def get(self):
        dbconn = sqlite3.connect(settings.DATABASE)
        cursor = dbconn.cursor()
        cursor.row_factory=sqlite3.Row
        cursor.execute("SELECT strftime('%Y-%m-%dT%H:%M:%fZ', [Timestamp]) AS [Timestamp], [Power], [Flame], [Tset], [Tboiler], [ThermostatStop] \
                          FROM [BurnerLogs] WHERE [Timestamp] >= datetime('now', '-6 hours')")

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
                          FROM (SELECT datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours', '+' || (1 * (a.[a] + (10 * b.[a]) + (100 * c.[a]))) || ' hours') AS [Date] \
                                  FROM (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS a \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS b \
                                 CROSS JOIN (SELECT 0 AS a UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) AS c \
                               ) AS t \
                         WHERE t.[Date] BETWEEN datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours') AND datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds') \
                        UNION ALL \
                        SELECT strftime('%Y-%m-%dT%H:%M:%fZ', datetime('now')) AS [Timestamp], \
                               ifnull((SELECT SUM([FFWorkTime]) \
                                         FROM [BurnerLogs] AS BL \
                                        WHERE BL.[TimeStamp] BETWEEN datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds', '-24 hours') AND datetime('now', '-' || strftime('%M', 'now') || ' minutes', '-' || strftime('%S', 'now') || ' seconds')), \
                                      0) as [FFWorkTime] \
                        ORDER BY [Timestamp]")

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
                           [Timestamp] DATETIME NOT NULL PRIMARY KEY, \
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
