#https://github.com/vkurup/python-tcxparser
#Copyright (c) 2013-6, Vinod Kurup
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification,
#are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"Simple parser for Garmin TCX files."
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

from builtins import range
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object
import time
from lxml import objectify

namespace = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'


class TCXParser(object):

    def __init__(self, tcx_file):
        tree = objectify.parse(tcx_file)
        self.root = tree.getroot()
        self.activity = self.root.Courses.Course

    def hr_values(self):
        return [int(x.text) for x in self.root.xpath('//ns:HeartRateBpm/ns:Value', namespaces={'ns': namespace})]

    def altitude_points(self):
        return [float(x.text) for x in self.root.xpath('//ns:AltitudeMeters', namespaces={'ns': namespace})]

    def time_values(self):
        return [x.text for x in self.root.xpath('//ns:Time', namespaces={'ns': namespace})]

    def latitude_points(self):
        return [float(x.text) for x in self.root.xpath('//ns:Position/ns:LatitudeDegrees', namespaces={'ns': namespace})]
   
    def longitude_points(self):
        return [float(x.text) for x in self.root.xpath('//ns:Position/ns:LongitudeDegrees', namespaces={'ns': namespace})]
    
    def distance_points(self):
        return [float(x.text) for x in self.root.xpath('//ns:Trackpoint/ns:DistanceMeters', namespaces={'ns': namespace})]
    
    @property
    def latitude(self):
        if hasattr(self.activity.Track.Trackpoint, 'Position'):
            return self.activity.Track.Trackpoint.Position.LatitudeDegrees.pyval

    @property
    def longitude(self):
        if hasattr(self.activity.Track.Trackpoint, 'Position'):
            return self.activity.Track.Trackpoint.Position.LongitudeDegrees.pyval

    @property
    def activity_type(self):
        return self.activity.attrib['Sport'].lower()

    @property
    def completed_at(self):
        return self.activity.Lap[-1].Track.Trackpoint[-1].Time.pyval

    @property
    def distance(self):
        distance_values = self.root.findall('.//ns:DistanceMeters', namespaces={'ns': namespace})
        if distance_values:
            return distance_values[-1]
        return 0

    @property
    def distance_units(self):
        return 'meters'

    @property
    def duration(self):
        """Returns duration of workout in seconds."""
        return sum(lap.TotalTimeSeconds for lap in self.activity.Lap)

    @property
    def calories(self):
        return sum(lap.Calories for lap in self.activity.Lap)

    @property
    def hr_avg(self):
        """Average heart rate of the workout"""
        hr_data = self.hr_values()
        return sum(hr_data)/len(hr_data)

    @property
    def hr_max(self):
        """Minimum heart rate of the workout"""
        return max(self.hr_values())

    @property
    def hr_min(self):
        """Minimum heart rate of the workout"""
        return min(self.hr_values())

    @property
    def pace(self):
        """Average pace (mm:ss/km for the workout"""
        secs_per_km = self.duration/(self.distance/1000)
        return time.strftime('%M:%S', time.gmtime(secs_per_km))

    @property
    def altitude_avg(self):
        """Average altitude for the workout"""
        altitude_data = self.altitude_points()
        return sum(altitude_data)/len(altitude_data)

    @property
    def altitude_max(self):
        """Max altitude for the workout"""
        altitude_data = self.altitude_points()
        return max(altitude_data)

    @property
    def altitude_min(self):
        """Min altitude for the workout"""
        altitude_data = self.altitude_points()
        return min(altitude_data)

    @property
    def ascent(self):
        """Returns ascent of workout in meters"""
        total_ascent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i+1] - altitude_data[i]
            if diff > 0.0:
                total_ascent += diff
        return total_ascent

    @property
    def descent(self):
        """Returns descent of workout in meters"""
        total_descent = 0.0
        altitude_data = self.altitude_points()
        for i in range(len(altitude_data) - 1):
            diff = altitude_data[i+1] - altitude_data[i]
            if diff < 0.0:
                total_descent += abs(diff)
        return total_descent
