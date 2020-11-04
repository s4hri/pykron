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

class PykronLogger:
    LOGGING_SETTINGS = None
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

    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOGGING_LEVEL = logging.DEBUG
    LOGGING_PATH = None
    _instance = None

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
            if PykronLogger.LOGGING_SETTINGS is None:
                self._logger = logging.getLogger('pykron')
                self._logger.setLevel(PykronLogger.LOGGING_LEVEL)
                if not PykronLogger.LOGGING_PATH is None:
                    filename = os.path.join(PykronLogger.LOGGING_PATH, 'pykron.log')
                    ch = logging.FileHandler(filename, mode='w')
                else:
                    ch = logging.StreamHandler()
                ch.setLevel(PykronLogger.LOGGING_LEVEL)
                formatter = logging.Formatter(PykronLogger.FORMAT)
                ch.setFormatter(formatter)
                self._logger.addHandler(ch)
            else:
                logging.config.dictConfig(PykronLogger.LOGGING_SETTINGS)
                self._logger = logging.getLogger('pykron')
            self._task_id = 0

    @property
    def log(self):
       return self._logger

    # get_native_id is not unique and not readable easily during the ongoing execution
    # this solution has the advantage of being consecutive
    _id_lock = threading.Lock()
    def getNewId(self):
        with self._id_lock:
            self._task_id += 1
            return self._task_id
