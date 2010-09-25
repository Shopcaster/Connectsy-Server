# Copyright 2010 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Timezone related utilities for PyMongo."""

from datetime import (timedelta,
                      tzinfo)

ZERO = timedelta(0)


class FixedOffset(tzinfo):
    """Fixed offset timezone, in minutes east from UTC.

    Implementation from the Python `standard library documentation
    <http://docs.python.org/library/datetime.html#tzinfo-objects>`_.
    """

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO


"""UTC"""
utc = FixedOffset(0, "UTC")
