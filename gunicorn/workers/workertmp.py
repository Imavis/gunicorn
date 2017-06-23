# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import platform
import struct
from monotonic import monotonic

from gunicorn import util

PLATFORM = platform.system()
IS_CYGWIN = PLATFORM.startswith('CYGWIN')


class WorkerTmp(object):
    _ts_len = len(struct.pack('d', 0.0))

    def __init__(self, cfg):
        self._rfd, self._wfd = os.pipe()
        self._last_update = monotonic()
        self._buffer = b''
        util.set_non_blocking(self._rfd)

    def notify(self):
        os.write(self._wfd, struct.pack('d', monotonic()))

    def last_update(self):
        while True:
            r = util.read_nonblock(self._rfd, 64)
            if r:
                self._buffer += r
            else:
                break
        blen = len(self._buffer)
        if blen >= self._ts_len:
            i1 = blen - blen % self._ts_len
            i0 = i1 - self._ts_len
            self._last_update = struct.unpack('d', self._buffer[i0:i1])[0]
            self._buffer = self._buffer[i1:]
        return self._last_update

    def fileno(self):
        return self._rfd, self._wfd

    def close(self):
        os.close(self._rfd)
        os.close(self._wfd)
