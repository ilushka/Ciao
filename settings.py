import os

#basepath to look for conf/connectors/whatelse
basepath = os.path.dirname(os.path.abspath(__file__)) + os.sep

#enable/disable debug
# atm this params has to be set to True only
# if you want to use a file as stdin instead of the real one
debug = True

#configuration dictionary
conf = {
	"backlog" : 5, #this value must match number of enabled connectors (we could len(connectors))
	"server": {
		"host" : "localhost",
		"port" : 8900
	},
	#path starting with slash will be handled like absolute ones
	"paths": {
		"conf" : "conf/",
		"connectors" : "connectors/"
	},
	"logfile" : "bridge.log"
}

#TODO comunication settings
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

#adjust some settings about paths
if not conf['paths']['conf'].startswith(os.sep): #relative path
	conf['paths']['conf'] = basepath + conf['paths']['conf']
if not conf['paths']['conf'].endswith(os.sep):
	conf['paths']['conf'] += os.sep

def init():
	global conf
	if not conf['paths']['conf'].startswith(os.sep): #relative path
		global basepath
		conf['paths']['conf'] = basepath + conf['paths']['conf']
