"""
Created on Nov 16, 2009

@author: epb
"""

from sys import argv
from sys import exit
import logging.handlers

from parser import parse_file

LOG_FILE = '../log/mylog.log'

def set_up_logging():
    global myLogger
    myLogger = logging.getLogger('myLogger')
    myLogger.setLevel(logging.INFO) #handler = logging.FileHandler(LOG_FILE)
    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s: %(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    myLogger.addHandler(handler)

if __name__ == '__main__':
    
    set_up_logging()
    
    myLogger.info('Starting cochonut')
    
    # get file to parse
    file = ''
    try:
        file = argv[1]
    except IndexError:
        msg = 'File not specified'
        myLogger.error(msg)
        exit(msg)
    
    # parse input
    if file:
        try:
            parse_file(file, myLogger)
        except Exception as e:
            msg = 'Failed to parse file: ' + e.args[0]
            myLogger.error(msg)
            exit(msg)
