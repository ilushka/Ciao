##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)

import logging
import socket, asyncore
import json
#import time
from threading import Thread
from Queue import Queue

class BridgeHandler(asyncore.dispatcher_with_send):

    write_pending = False
    data_pending = None

    def handle_read(self):
        self.logger.debug("Handle READ")
        data = self.recv(2048)
        self.logger.debug("read message: %s" % data)
        if data:
            data_decoded = json.loads(data)
            if "status" in data_decoded:
                if self.write_pending:
                    self.shd["requests"][data_decoded["checksum"]] = self.data_pending
                    self.data_pending = None
                    self.write_pending = False
                else:
                    self.logger.debug("result msg but not write_pending: %s" % data)
            else:
                self.xmpp_queue.put(data_decoded)

    def writable(self):
        if not self.shd["loop"]:
            raise asyncore.ExitNow('Connector is quitting!')
        if not self.socket_queue.empty() and not self.write_pending:
            return True
        return False

    def handle_write(self):
        entry = self.socket_queue.get()
        # we wait a feedback (status + checksum) from bridge)
        self.write_pending = True
        self.data_pending = entry
        self.send(json.dumps(entry))

    def handle_close(self):
        self.logger.debug("Handle CLOSE")
        return
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        while 1:
            self.logger.debug("Trying to reconnect")
            try:
                self.handle_connect("127.0.0.1", 8900)
                self.logger.debug(" - connected")
            except:
                self.logger.debug(" - error")
                time.sleep(5)

    def handle_error(self):
        nil, t, v, tbinfo = asyncore.compact_traceback()

        # sometimes a user repr method will crash.
        try:
            self_repr = repr(self)
        except:
            self_repr = '<__repr__(self) failed for object at %0x>' % id(self)

        self.logger.debug('BridgeSocket - uncaptured python exception %s (%s:%s %s)' % (
            self_repr, t, v, tbinfo
        ))
        self.logger.debug("Handle ERROR")
        return
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        while 1:
            self.logger.debug("Trying to reconnect")
            try:
                self.handle_connect("127.0.0.1", 5555)
                self.logger.debug(" - connected")
            except:
                self.logger.debug(" - error")

class BridgeSocket(asyncore.dispatcher):
    host = None
    port = None
    handler = None
    def __init__(self, shd, xmpp_queue, socket_queue):
        self.shd = shd
        self.xmpp_queue = xmpp_queue
        self.socket_queue = socket_queue
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logging.getLogger("xmpp")

    def handle_connect(self, host, port):
        self.host = host
        self.port = port
        self.connect((host,port))
        self.handler = BridgeHandler(self)

    def exit(self):
        raise asyncore.ExitNow('Connector is quitting!')

class BridgeThread(Thread):
    def __init__(self, shd, xmpp_queue, socket_queue):
        Thread.__init__(self)
        self.daemon = True
        self.shd = shd
        self.socket = BridgeSocket(shd, xmpp_queue, socket_queue)
        self.socket.handle_connect("127.0.0.1", 8900)
        params = {
            "action" : "register",
            "name" : "xmpp"
        }
        self.socket.send(json.dumps(params))

    def run(self):
        try:
            asyncore.loop(0.1)
        except asyncore.ExitNow, e:
            logger = logging.getLogger("xmpp")
            logger.debug("Exception asyncore.ExitNow, closing BridgeSocket. (%s)" % e)

    def stop(self):
        #self.socket.exit()
        #self.socket.close()
        self.join()