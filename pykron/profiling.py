"""
BSD 2-Clause License

Copyright (c) 2021, Davide De Tommaso (davide.detommaso@iit.it),
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

import sys
import os
import datetime
import __main__

if sys.version_info > (3,7):
    import cProfile, pstats, io
    from pstats import SortKey

class PykronProfiler:

    def __init__(self):
        self._profilers = {}
        self._restrictions = set()

    def addTask(self, task):
        self._profilers[task.task_id] = cProfile.Profile(subcalls=False, builtins=False)
        self._restrictions.add(task.func_name)
        task.set_profiler(self._profilers[task.task_id])

    def saveStats(self):
        f_stats = []
        for task_id, profiler in self._profilers.items():
            stream = io.StringIO()
            sortby = SortKey.CUMULATIVE
            ps = pstats.Stats(profiler, stream=stream).strip_dirs()
            filename = str(task_id) + '.stats'
            ps.dump_stats(filename)
            f_stats.append(filename)
        ps = pstats.Stats(*f_stats)
        for f in f_stats:
            os.remove(f)
        ps.sort_stats(sortby)

        restrictions = str(self._restrictions)
        restrictions= restrictions.replace('{','').replace('}','').replace(',','|').replace('\'','').replace(' ', '')
        ps.print_stats(restrictions)
        print(stream.getvalue())
        datetimestr = datetime.datetime.now().strftime('%d.%m.%Y_%H:%M')
        main_name = os.path.split(__main__.__file__)[1].split('.')[0]
        filename = "%s_%s.stats" % (main_name, datetimestr)
        ps.dump_stats(filename)
