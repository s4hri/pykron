"""
BSD 2-Clause License

Copyright (c) 2020, Davide De Tommaso (davide.detommaso@iit.it),
                    Adam Lukomski (adam.lukomski@iit.it),
                    Social Cognition in Human-Robot Interaction
                    Istituto Italiano di Tecnologia, Genova
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

import threading
import os
import csv
import datetime
import logging
import time
import __main__

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

    @staticmethod
    def getInstance():
        if PykronLogger._instance == None:
            PykronLogger()
        return PykronLogger._instance

    def __init__(self, logging_level=LOGGING_LEVEL, logging_path=LOGGING_PATH, logging_format=FORMAT, save_csv=False):
        if PykronLogger._instance != None:
            raise Exception("This class is a singleton!")
        else:
            PykronLogger._instance = self
            self._logging_level = logging_level
            self._logging_path = logging_path
            self._logging_format = logging_format
            self._logger = logging.getLogger('pykron')
            self._logger.setLevel(logging_level)

            self._executions = []
            self._lock = threading.Lock()
            self._save_csv = save_csv

            if self._logging_path is None:
                self.addStreamHandler()
                if self._save_csv:
                    self._logging_path = '.'
            else:
                self.addFileHandler(logging_path)

    def addFileHandler(self, path):
        datetimestr = datetime.datetime.now().strftime('%d.%m.%Y_%H:%M')
        filename = "pykron_%s_%s.log" % (__main__.__file__, datetimestr)
        filepath = os.path.join(path, filename)
        ch = logging.FileHandler(filepath, mode='w')
        ch.setLevel(self._logging_level)
        formatter = logging.Formatter(self._logging_format)
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    def addStreamHandler(self, stream=None):
        ch = logging.StreamHandler(stream) # None defaults to sys.stderr
        ch.setLevel(self._logging_level)
        formatter = logging.Formatter(self._logging_format)
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

    @property
    def logging_level(self):
       return self._logging_level

    @property
    def log(self):
       return self._logger

    def log_execution(self, task):
        if self._save_csv:
            with self._lock:
                task_exec = [str(time.time()), task.func_name, task.func_loc, task.caller_name, task.caller_loc, task.status, task.arrival_ts, task.start_ts, task.end_ts, task.duration, task.idle_time, str(task.retval), str(task.exception), str(task.args)]
                self._executions.append(task_exec)

    def save_csv(self):
        if self._save_csv:
            datetimestr = datetime.datetime.now().strftime('%d.%m.%Y_%H:%M')
            filename = "pykron_%s_%s.csv" % (__main__.__file__, datetimestr)
            headers = ["Timestamp", "Function", "Location", "Caller function", "Caller location", "Status", "Arrival Ts", "Start Ts", "End Ts", "Duration", "Idle time", "Return value", "Exception", "Args"]
            with open(os.path.join(self._logging_path, filename), 'w') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(self._executions)
