import re
import socket
import termios
import logging
import settings

#enable/disable echo on tty
def enable_echo(fd, enabled):
	(iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = termios.tcgetattr(fd)
	if enabled:
		lflag |= termios.ECHO
	else:
		lflag &= ~termios.ECHO
	new_attr = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
	termios.tcsetattr(fd, termios.TCSANOW, new_attr)

def clean_command(command):
	return command.rstrip()

def is_valid_command(command):
	#a valid command must contain at least two fields: connector and action
	elements = command.split(";", 2)
	if len(elements) >= 2 and elements[1] in settings.allowed_actions:
		return elements
	return False, False