'''
Created on 2012-3-21

@author: chinple
'''
import os

import socket
from BaseHTTPServer import BaseHTTPRequestHandler
import re
from inspect import getargspec
from urlparse import parse_qsl
import urllib
import time
from json.decoder import JSONDecoder
from json.encoder import JSONEncoder

def tryGet(obj, key, defValue):
    try:
        return obj[key]
    except:
        return defValue

class __ObjEncoder__(JSONEncoder):
    def default(self, obj):
        return str(obj)

_jsd, _jsn = JSONDecoder(), __ObjEncoder__()

def parseRequestParam(paramStr):
    try:
        try:
            return _jsd.decode(paramStr)
        except:
            reqParam = {}
            for name, value in parse_qsl(urllib.unquote(paramStr)):
                reqParam[name] = value
            return reqParam
    except:
        return {}

def decodeHttpBody(headers, body):
    if "gzip" == tryGet(headers, "content-encoding", ""):
        import StringIO
        import gzip
        gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(body))
        body = gzipper.read()
    try:
        return body.decode(headers["Content-Type"].split("charset=")[1])
    except:
        return body

class CServerHandler(BaseHTTPRequestHandler):
    mainpage = None
    webroot = None
    uploadFolder = "."
    rHandler = None  # router handler, set by @createHttpServer
    sessionCookie = None
    session = None
    redirectPath = None
    maxBodySize = 104857600

    def __init__(self, *tupleArg, **jsonArg):
        self.server_version = "CSERVER 1.0"
        BaseHTTPRequestHandler.__init__(self, *tupleArg, **jsonArg)

    def finish(self):
        try:
            BaseHTTPRequestHandler.finish(self)
        except socket.error as ex:
            self.__handle_close_error(ex)

    def __handle_close_error(self, ex):
        self.close_connection = 1
        try:
            self.log_error("Close %s for %s", self.requestline, ex)
        except:
            self.log_error("Close %s for %s", self, ex)
        
    def handle_one_request(self):
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except socket.error as ex:
            self.__handle_close_error(ex)

    def do_POST(self):
        self.__handleNoException(True)

    def do_DELETE(self):
        self.__handleNoException(True)

    def do_PUT(self):
        self.__handleNoException(True)

    def do_PATCH(self):
        self.__handleNoException(True)

        self.addContentType("text/%s", 'xml', "css", 'xsl', 'ini', 'in', 'txt', 'py', 'cpp', 'java', 'md')
            return "application/%s" % fileType
