##    This file extends the YunBridge.
##
##    Copyright (C) 2015 Arduino Srl (http://www.arduino.org/)
##    Author : Fabrizio De Vita (fabriziodevita92@gmail.com)
##

import json
import sleekxmpp

class XMPPClient(sleekxmpp.ClientXMPP):

    data_rx = [None]

    def __init__(self, jid, password, socket_queue):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
    
        self.socket_queue = socket_queue

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)
        
        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)

        # Service Discovery
        self.register_plugin('xep_0030')
        # Data Forms
        self.register_plugin('xep_0004')
        # PubSub
        self.register_plugin('xep_0060')
        # XMPP Ping
        self.register_plugin('xep_0199')

    def start(self, event):
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        
        if msg['type'] in ('chat', 'normal'):
            entry = {
                "data" : [str(msg["from"]), str(msg["body"])]
            }
            self.socket_queue.put(entry)
