"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (dtmdvd@gmail.com)
                    Social Cognition in Human-Robot Interaction
                    Istituto Italiano di Tecnologia (IIT)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import logging
import logging.config
import logging.handlers

import threading
import os
import csv
import datetime

class PykronLogger:
    ''' logging wrapper for quick setup
    
    creates a singleton _instance and adds basic handlers
    '''

    _instance = None

    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'   # base format
    FORMAT_VERBOSE = '%(asctime)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
    FORMAT_JSON = '{"asctime": "%(asctime)-15s", "created": %(created)f, "relativeCreated": %(relativeCreated)f, "levelname": "%(levelname)s", "module": "%(module)s", "process": %(process)d, "processName": "%(processName)s", "thread": %(thread)d, "threadName": "%(threadName)s", "message": "%(message)s"}'

    LOGGING_LEVEL = logging.DEBUG
    LOGGING_PATH = None      # starts file logger
    LOGGING_SETTINGS = None  # sets usage of a dictionary




    @staticmethod
    def getInstance():
        if PykronLogger._instance == None:
            PykronLogger()
        return PykronLogger._instance

    def __init__(self):
        if PykronLogger._instance != None:
            raise Exception("This class is a singleton!")
        else:
            PykronLogger._instance = self
            # choose fileconfig > dictconfig > basic
            # TODO add fileconfig support
            if PykronLogger.LOGGING_SETTINGS is None:
                self._logger = logging.getLogger('pykron')
                self._logger.setLevel(PykronLogger.LOGGING_LEVEL)

                # default behaviour is file logger > stream logger
                if PykronLogger.LOGGING_PATH is None:
                    self.addStreamHandler()
                else:
                    self.addFileHandler()
            else:
                logging.config.dictConfig(PykronLogger.LOGGING_SETTINGS)
                self._logger = logging.getLogger('pykron')

    def addFileHandler(self,path=None,filename='pykron.log',format=None):
        if path is None:
            filepath = os.path.join(PykronLogger.LOGGING_PATH, filename)
            self._fexec_name = datetime.datetime.now().strftime('pykron_%d.%m.%Y_%H:%M.csv')
            with open(os.path.join(PykronLogger.LOGGING_PATH, self._fexec_name), 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['Datetime', 'Func_Name', 'Task_Name', 'Status', 'Start_Ts', 'End_Ts', 'Duration', 'Idle_Time', 'Return_Value', 'Exception', 'Args'])
        else:
            # this one is different to allow other logging level files later
            # but will not save execution statistics
            filepath = os.path.join(path, filename)
        ch = logging.FileHandler(filepath, mode='w')
        ch.setLevel(PykronLogger.LOGGING_LEVEL)
        if format is None:
            format = PykronLogger.FORMAT
        formatter = logging.Formatter(format)
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    def addStreamHandler(self,stream=None,format=None):
        # TODO format is not the best choice for the variable, any better name?
        ch = logging.StreamHandler(stream) # None defaults to sys.stderr
        ch.setLevel(PykronLogger.LOGGING_LEVEL)
        if format is None:
            formatter = PykronLogger.FORMAT
        formatter = logging.Formatter(format)
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    @property
    def log(self):
       return self._logger

    def log_execution(self, task_exec):
        if PykronLogger.LOGGING_PATH is None:
            return
        with open(os.path.join(PykronLogger.LOGGING_PATH, self._fexec_name), 'a') as f:
            writer = csv.writer(f)
            writer.writerow(task_exec)

    def log_execution_filename(self):
        return self._fexec_name



    # to be deprecated:
    LOGGING_SETTINGS_JSON = {

        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'json': {
                'format': '{"asctime": "%(asctime)-15s", "created": %(created)f, "relativeCreated": %(relativeCreated)f, "levelname": "%(levelname)s", "module": "%(module)s", "process": %(process)d, "processName": "%(processName)s", "thread": %(thread)d, "threadName": "%(threadName)s", "message": "%(message)s"}'
            },
            'verbose': {
                'format': '%(asctime)s - %(levelname)s - %(module)s - %(process)d - %(thread)d - %(message)s'
            },
            'simple': {
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level':'DEBUG',
                'class':'logging.FileHandler',
                # this works, but only in a configfile:
                #'filename': (__import__('datetime').datetime.now().strftime('log/pykron_%%Y-%%m-%%d_%%H-%%M-%%S.log'), 'a'),
                'filename': 'pykron.log',
                'mode': 'w',
                'formatter': 'json'
            },
            'console': {
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter': 'simple'
            }
        },
        'loggers': {
            'default': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG'
            }
        },
        'root': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG'
        }
    }