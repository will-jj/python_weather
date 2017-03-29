"""
tcxWeather
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from builtins import open
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object
import numpy as np
import pickle
import tcxparser
import json
import requests
import os
import time
import calendar

from datetime import datetime, timedelta, date, time

from pytz import timezone


class TcxRide(object):
    '''
    Class to obtain data from tcx file and aditional parameters such as ride speed.

    '''
    def __init__(self, xmlfile):
        """
        Init function to initialise TCXRide with chosen TCX File for non weather based analysis

        Args:
            xmlfile (str): TCX path/file you wish to use
        """

        self.raw = tcxparser.TCXParser(xmlfile)
        self.stravaTime = self.raw.time_values()
        self.length = len(self.stravaTime)
        self.latitude = self.raw.latitude_points()
        self.longitude = self.raw.longitude_points()
        self.distance = self.raw.distance_points()
        self.distanceTotal = self.distance[self.length-1]
        self.__bearing__()
        self.tZ = timezone('Europe/London')

    def __bearing__(self):
        self.bearing = list()
        self.bearing.append(0) # first bearing 0
        phi = list()
        lambd = list()
        for x in self.latitude:
            phi.append(np.deg2rad(x))
        for x in self.longitude:
            lambd.append(np.deg2rad(x))
        for x in range(1, self.length):
            y = np.sin(lambd[x]-lambd[x-1]) * np.cos(phi[x])
            x = np.cos(phi[x-1])*np.sin(phi[x]) - np.sin(phi[x-1])*np.cos(phi[x])*np.cos(lambd[x]-lambd[x-1])
            self.bearing.append(np.degrees(np.arctan2(y, x))%360)

    def __bearingdec__(self): # fix to one function for both bearings
        self.bear = list()
        self.bear.append(0) # first bearing 0
        phi = list()
        lambd = list()
        for x in self.lat:
            phi.append(np.deg2rad(x))
        for x in self.lon:
            lambd.append(np.deg2rad(x))
        for x in range(1, len(self.lat)):
            y = np.sin(lambd[x]-lambd[x-1]) * np.cos(phi[x])
            x = np.cos(phi[x-1])*np.sin(phi[x]) - np.sin(phi[x-1])*np.cos(phi[x])*np.cos(lambd[x]-lambd[x-1])
            self.bear.append(np.degrees(np.arctan2(y, x))%360) # 0-360 instead of -180:180

    def speed(self, **kwargs):

        """
        Define speed for ride

        Keyword Args:
            mph (dec): Define ride speed in mph
            kph (dec): Define ride speed in kph
            mps (dec): Define ride speed in mps

        """

        mps_mph = 2.23694
        mps_kph = 3.6
        if 'mph' in kwargs:
            self.mph = kwargs['mph']
            self.mps = self.mph / mps_mph
            self.kph = self.mps*mps_kph
        elif 'kph' in kwargs:
            self.kph = kwargs['kph']
            self.mps = self.kph/mps_kph
            self.mph = self.mps*mps_mph
        elif 'mps' in kwargs:
            self.mps = kwargs['mps']
            self.kph = self.mps*mps_kph
            self.mph = self.mps*mps_mph
        self.__time__()

    def decimate(self, **kwargs):
        """
        Create decimated version of data in self to aquire weather data
        with reasonable amount of api calls

        Keyword Args:
            Distance (dec): Define decimation in metres between samples
            Points (int): Define num of points for weather calls
            # TODO Time (dec): Define decimation in time spacing

        """
        if 'Distance' in kwargs:
            distance = kwargs['Distance']
            # points not constant this is average
            numPoints = self.distanceTotal/distance
        elif 'Points' in kwargs:
            numPoints = kwargs['Points']
        elif 'Time' in kwargs:
            if hasattr(self, 'mps'):
                numPoints = self.totalTime/kwargs['Time']
            else:
                raise Exception('no speed defined use x.Speed(mps =y | kph =z | mph =w)')
        else:
            raise Exception('Define decimation in terms of Distance= (m)| Points = (n)| Time = (s)')

        numPoints = np.floor(numPoints).astype(int)
        print('Decimating to {0} Points'.format(numPoints))
        ind = np.linspace(0, (self.length-1), numPoints, endpoint=True, retstep=False, dtype=None)
        ind = np.floor(ind)
        ind = ind.astype(int)
	print(ind)
        self.len = numPoints
        self.lat = np.array(self.latitude)
        self.lon = np.array(self.longitude)
        self.dist = np.array(self.distance)
        self.lat = self.lat[np.ix_(ind)]
        self.lon = self.lon[np.ix_(ind)]
        self.dist = self.dist[np.ix_(ind)]
        self.__bearingdec__()
        self.__timeDec__()

    def __timeDec__(self):
        self.time = list()
        timeSectoAdd = 0
        self.time.append(self.rideStartTime)
        for x in range(1, self.len):
            delDist = self.dist[x]-self.dist[x-1]
            timeSectoAdd += delDist/self.mps
            timeSectoAdd = int(np.floor(timeSectoAdd))
            combined = self.rideStartTime + timedelta(seconds=timeSectoAdd)
            self.time.append(combined)


    def __time__(self):
        self.timeSeconds = list()
        self.timeSeconds.append(0)
        timetot = 0
        for x in range(1, self.length):
            delDist = self.distance[x]-self.distance[x-1]
            timetot += delDist/self.mps
            self.timeSeconds.append(int(timetot))
        self.totalTime = timetot



    def setRideStartTime(self, **kwargs): #TODO (Check is in range of forecast)

        """
        Enter ride start time

        Keyword Args:

            Date (str): Enter date in format d/m (if not entered defaults to today)
            Time (str): Enter ride start time in format H:M

        """

        if 'date' in kwargs:
            datein = datetime.strptime(kwargs["date"], "%d/%m").date()
            datein = datein.replace(year=datetime.today().year)
        else:
            datein = datetime.today().date()
        if 'time' in kwargs:
            timein = datetime.strptime(kwargs["time"], "%H:%M").time()
        else:
            raise Exception('No time given')
        self.rideStartTime = datetime.combine(datein, timein)
        self.rideStartTime = self.tZ.localize(self.rideStartTime)


class RideWeather(TcxRide):
    """
    Ride weather class adds weather data functionality to TcxRide
    """

    def __init__(self, **kwargs):
        """
        Init function to initialise Ride weather with chosen TCX File

        Keyword Args:
            loadPrev (str): Pickle file of a prior run
            xmlfile (str): TCX path/file you wish to use
        """
        if 'loadPrev' in kwargs:
            with open(kwargs['loadPrev'], 'rb') as f:
                a = pickle.load(f)

            self.__dict__.update(a.__dict__)
        elif 'xmlfile' in kwargs:
            TcxRide.__init__(self, kwargs['xmlfile'])
        else:
            raise  Exception('No xmlfile=filestr or loadPrev = picklestring given')

    def getWeatherData(self, apikey, **kwargs):
        """
        Collects weather data from DarkSky
        Args:
            apikey (str): Your API key
        Keyword Args:
            units (str): Units used for weather call options: see darksky for options past si...
            fileDirectory(str): Path for files to be saved ie: myDir/myInnerDir
            fileName(str): File name

        """


        urlprov = 'https://api.darksky.net/forecast/'
        if hasattr(self, 'weatherData'):
            raise Exception('Data already exists')
        self.weatherData = list()
        if hasattr(self, 'len'):
            print('Gathering weather data...')
        else:
            raise Exception('Data not decimated not making API call')
        for x in range(0, self.len):
            url = '{0}{1}/{2},{3}?exclude=daily,alerts,flags&units={4}'.format(urlprov, apikey, self.lat[x], self.lon[x], kwargs['units'])
            data = requests.get(url).content
            if 'fileDirectory' in kwargs:
                if 'fileName' in kwargs:
                    if not os.path.exists(kwargs['fileDirectory']):
                        os.makedirs(kwargs['fileDirectory'])
                    file = open('{0}/{1}{2}.json'.format(kwargs['fileDirectory'], kwargs['fileName'], x), 'wb')
                    file.write(data)
                    file.close()


            self.weatherData.append(json.loads(data))
        print('Gathered weather data')

    def loadExistingData(self, location):
        """
        Loads existing JSON format weather data
        Args:

            location (str): file path and base name of the multiple JSON files

       """

        if hasattr(self, 'weatherData'):
            raise Exception('Data already exists')
        self.weatherData = list()
        for x in range(0, self.len):
            filename = '{0}{1}.json'.format(location, x)
            # print('Loading' filename)
            with open(filename) as data_file:
                self.weatherData.append(json.load(data_file))

    def clearWeatherData(self):

        """
        Call function to remove .weatherData from object
        This will allow you to re-generate new weather data
        """

        del self.weatherData

    def getForecast(self, **kwargs):  # potentially make this its own class inheriting from tcxweather

        """
        Adds forecast to self
        Keyword Args:

            fileDirectory(str): Path for files to be saved ie: myDir/myInnerDir
            fileName(str): File name

        """


        self.precipIntensity = list()
        self.windBearing = list()
        self.relWindBear = list()
        self.apparentTemperature = list()
        self.cloudCover = list()
        self.dewPoint = list()
        self.humidity = list()
        self.icon = list()
        self.ozone = list()
        self.precipIntensity = list()
        self.precipProbability = list()
        self.precipType = list()
        self.pressure = list()
        self.summary = list()
        self.temperature = list()
        self.visibility = list()
        self.windBearing = list()
        self.windSpeed = list()
        self.forecastTime = list()
        self.deltaTime = list()
        self.timeHr = list()
        self.timeMin = list()
        self.timeHourTime = list()
        for x in range(0, self.len):
            # self..append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]][""])
            self.forecastTime.append(
                self.tZ.localize(datetime.fromtimestamp(int(self.weatherData[x]["currently"]["time"]))))
            self.deltaTime.append((self.time[x] - self.forecastTime[x]))
            self.timeMin.append((np.round((self.deltaTime[x] / timedelta(minutes=1)))).astype(int))
            self.timeHr.append((np.round((self.deltaTime[x] / timedelta(hours=1)))).astype(int))
            self.windBearing.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windBearing"])
            self.apparentTemperature.append(
                self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["apparentTemperature"])
            self.cloudCover.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["cloudCover"])
            self.dewPoint.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["dewPoint"])
            self.humidity.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["humidity"])
            self.icon.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["icon"])
            self.ozone.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["ozone"])
            self.pressure.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["pressure"])
            self.summary.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["summary"])
            self.temperature.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["temperature"])
            self.timeHourTime.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["time"])
            self.visibility.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["visibility"])
            self.windBearing.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windBearing"])
            self.windSpeed.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windSpeed"])
            self.relWindBear.append((self.windBearing[x] - self.bear[x]) % 360)
            if (self.timeMin[x]) < 60:
                self.precipProbability.append(
                    self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipProbability"])
                self.precipIntensity.append(
                    self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipIntensity"])
                if self.precipIntensity[x] > 0:
                    self.precipType.append(self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipType"])
                else:
                    self.precipType.append("None")
            else:
                self.precipIntensity.append(
                    self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipIntensity"])
                self.precipProbability.append(
                    self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipProbability"])
                if self.precipIntensity[x] > 0:
                    self.precipType.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipType"])
                else:
                    self.precipType.append("None")
            if 'fileDirectory' in kwargs:
                if 'fileName' in kwargs:

                    with open('{0}/{1}.pkl'.format(kwargs['fileDirectory'], kwargs['fileName']), 'wb') as output:

                        pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)


