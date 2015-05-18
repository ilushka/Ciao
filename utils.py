import re
import array
import socket
import termios
import logging
import settings

import os, tty, termios, sys
from contextlib import contextmanager

@contextmanager
def cbreak():
  if hasattr(sys.stdin, "fileno") and os.isatty(sys.stdin.fileno()):
    old_attrs = termios.tcgetattr(stdin)
    tty.setcbreak(stdin)
    tty.setraw(stdin)
  try:
    yield
  finally:
    if hasattr(sys.stdin, "fileno") and os.isatty(sys.stdin.fileno()):
      termios.tcsetattr(stdin, termios.TCSADRAIN, old_attrs)

#enable/disable echo on tty
def enable_echo(fd, enabled):
	(iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(fd)
	if enabled:
		lflag |= termios.ECHO
	else:
		lflag &= ~termios.ECHO
	new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
	termios.tcsetattr(fd, termios.TCSANOW, new_attr)

#Command methods
def clean_command(command):
	return command.rstrip()

def is_valid_command(command):
	#a valid command must contain at least two fields: connector and action
	elements = command.split(";", 2)
	if len(elements) >= 2 and elements[1] in settings.allowed_actions:
		return elements
	return False, False

#Serialization methods
#serialize passed dict/list, atm it works only for one level object not nested ones
def serialize(data):
	s = array.array("B")
	entries = []
	if isinstance(data, list):
		for e in data:
			entries.append(escape(e))
	elif isinstance(data, dict):
		for k, v in data.items():
			entries.append(settings.keyvalue_separator.join([escape(k), escape(v)]))
	else:
		entries.append(escape(data))
	s.fromstring(settings.entry_separator.join(entries))
	return s

#unserialize passed dict/list, atm it works only for one level object not nested ones
def unserialize(source):
	data = array.array("B", source)
	#identifying data type
	try:
		index = data.index(ord(settings.keyvalue_separator))
		result = {}
	except ValueError, e:
		try:
			index = data.index(ord(settings.entry_separator))
			result = []
		except ValueError, e:
			result = []

	#converting bytearray into object
	addr, size = data.buffer_info()
	count = 0
	if isinstance(result, dict):
		params = ["",""]
		param_index = 0
		while count < size:
			pick = data.pop(0)
			count +=1
			if pick == ord(settings.keyvalue_separator):
				param_index = 1
				params[param_index] = ""
			elif pick == ord(settings.entry_separator):
				result[escape(params[0], False)] = escape(params[1], False)
				param_index = 0
				params = ["", ""]
			else:
				params[param_index] += chr(pick)
		if params[0] != "":
			result[escape(params[0], False)] = escape(params[1], False)
	else:
		entry = ""
		while count < size:
			pick = data.pop(0)
			count +=1
			if pick == ord(settings.entry_separator):
				result.append(escape(entry, False))
				entry = ""
			else:
				entry += chr(pick)
		result.append(escape(entry, False))
	return result

def escape(s, encode = True):
	if encode:
		return s.encode('unicode-escape')
	else:
		return s.decode('unicode-escape')
