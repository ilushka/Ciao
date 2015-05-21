#enable/disable debug
# atm this params has to be set to True only
# if you want to use a file as stdin instead of the real one
debug = True

#configuration dictionary
"""
#TODO here we have to:
 scan SOMEDIR_CONF for connector configuration (bridge-side)
"""
conf = {
	"backlog" : 5, #this value must match number of enabled connectors (we could len(connectors))
	"srvhost" : "localhost",
	"srvport" : 8900,
	"logfile" : "bridge.log",
	"connectors" : {
		"xmpp" : {
			"implements" : {
				"read" : "with_message",
				"write" : "with_queue",
				"writeresponse" : "with_queue"
			}
		}
	}
}

#comunication settings
#bridge_msgsize = 1024
#connector_msgsize = 1024

#allowed action accepted from bridge(MCU-side)
allowed_actions = {
	#requires 3 params - connector;action;data(optional)
	"r": { "params": 3, "map": "read"},
	#requires 3 params - connector;action;data
	"w": { "params": 3, "map": "write"},
	#requires 4 params - connector;action;reference;data
	"wr": { "params": 4, "map": "writeresponse"}
}

#serialization settings
# ASCII code for GroupSeparator (non-printable char)
entry_separator = chr(30)
# ASCII code for UnitSeparator (non-printable char)
keyvalue_separator = chr(31)