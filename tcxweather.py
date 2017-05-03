"""
tcxweather
"""
import os
import pickle
import json
from datetime import datetime, timedelta  # unused time, date

import requests
# from python_weather import tcxparser
import numpy as np
# import stravalib
from pytz import timezone


class TcxRide:
    """
    Class to obtain data from tcx file and aditional parameters such as ride speed.

    """

    def __init__(self, **kwargs):
        """
        Init function to initialise TCXRide with chosen TCX File for non weather based analysis

        Keyword Args:
            strava_course (obj): Pass Strava Course
            xmlfile (str): TCX path/file you wish to use

        """
        if 'strava_course' in kwargs:
            course = kwargs['strava_course']
            self.distance = course['distance'].data
            self.latitude, self.longitude = zip(*course['latlng'].data)
        elif 'xmlfile' in kwargs:
            raise Exception('No longer supported')
            # self.raw = tcxparser.TCXParser(kwargs['xmlfile'])
            # self.latitude = self.raw.latitude_points()
            # self.longitude = self.raw.longitude_points()
            # self.distance = self.raw.distance_points()
        else:
            raise Exception('No valid data')

        self.length = len(self.distance)
        self.distance_total = self.distance[-1]
        self.time_zone = timezone('Europe/London')
        self.bearing = list()
        self.bear = list()
        self.mph = 0
        self.mps = 0
        self.kph = 0
        self.len = 0

        self.lat = None  # np.array()
        self.lon = None  # np.array()
        self.dist = 0  # np.array()

        self.time = list()

        self.time_seconds = list()
        self.total_time = 0

        self.ride_start_time = 0  # datetime
        self.weather_data = list()
        self.weather = {
            'precip_intensity': [],
            'wind_bearing': [],
            'rel_wind_bear': [],
            'apparent_temperature': [],
            'cloud_cover': [],
            'dew_point': [],
            'humidity': [],
            'icon': [],
            'ozone': [],
            'wind_head': [],
            'wind_cross': [],
            'precip_probability': [],
            'precip_type': [],
            'pressure': [],
            'summary': [],
            'temperature': [],
            'visibility': [],
            'wind_speed': [],
            'forecast_time': [],
            'delta_time': [],
            'time_hr': [],
            'time_min': [],
            'time_hour_time': []
        }

    def __bearing(self):
        self.bearing = GeoFuncs.bearing_func(self.latitude, self.longitude)

    def __bearingdec(self):
        self.bear = GeoFuncs.bearing_func(self.lat, self.lon)

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
            self.kph = self.mps * mps_kph
        elif 'kph' in kwargs:
            self.kph = kwargs['kph']
            self.mps = self.kph / mps_kph
            self.mph = self.mps * mps_mph
        elif 'mps' in kwargs:
            self.mps = kwargs['mps']
            self.kph = self.mps * mps_kph
            self.mph = self.mps * mps_mph
        self.__time()

    def decimate(self, **kwargs):
        """
        Create decimated version of data in self to aquire weather data
        with reasonable amount of api calls

        Keyword Args:
            Distance (dec): Define decimation in metres between samples
            Points (int): Define num of points for weather calls
            Time (dec): Define decimation in time spacing seconds

        """
        if 'Distance' in kwargs:
            distance = kwargs['Distance']
            # points not constant this is average
            num_points = self.distance_total / distance
        elif 'Points' in kwargs:
            num_points = kwargs['Points']
        elif 'Time' in kwargs:
            if hasattr(self, 'mps'):
                num_points = self.total_time / kwargs['Time']
            else:
                raise Exception('no speed defined use x.Speed(mps =y | kph =z | mph =w)')
        else:
            raise Exception('Define decimation in terms of Distance= (m)| Points = (n)| Time = (s)')

        num_points = np.floor(num_points).astype(int)
        print('Decimating to {0} Points'.format(num_points))
        ind = np.linspace(
            0, (self.length - 1), num_points, endpoint=True, retstep=False, dtype=None)
        ind = np.floor(ind)
        ind = ind.astype(int)
        self.len = num_points
        self.lat = np.array(self.latitude)
        self.lon = np.array(self.longitude)
        self.dist = np.array(self.distance)
        self.lat = self.lat[np.ix_(ind)]
        self.lon = self.lon[np.ix_(ind)]
        self.dist = self.dist[np.ix_(ind)]
        self.__bearingdec()
        self.__time_dec()

    def __time_dec(self):
        time_sec_add = 0
        self.time.append(self.ride_start_time)
        for itr in range(1, self.len):
            delta_dist = self.dist[itr] - self.dist[itr - 1]
            time_sec_add += delta_dist / self.mps
            time_sec_add = int(np.floor(time_sec_add))
            combined = self.ride_start_time + timedelta(seconds=time_sec_add)
            self.time.append(combined)

    def __time(self):
        self.time_seconds.append(0)
        timetot = 0
        for itr in range(1, self.length):
            delta_dist = self.distance[itr] - self.distance[itr - 1]
            timetot += delta_dist / self.mps
            self.time_seconds.append(int(timetot))
        self.total_time = timetot

    def set_ride_start_time(self, **kwargs):

        """
        Enter ride start time

        Keyword Args:
            Unix: provide unix
            Date (str): Enter date in format d/m (if not entered defaults to today)
            Time (str): Enter ride start time in format H:M

        """

        if self.mps == 0:
            raise Exception('Please input ride speed first')
        if 'unix' in kwargs:
            start_time = datetime.fromtimestamp(kwargs['unix'])
        else:
            if 'date' in kwargs:
                datein = datetime.strptime(kwargs["date"], "%d/%m").date()
                datein = datein.replace(year=datetime.today().year)
            else:
                datein = datetime.today().date()
            if 'time' in kwargs:
                timein = datetime.strptime(kwargs["time"], "%H:%M").time()
            else:
                raise Exception('No time given')

            start_time = datetime.combine(datein, timein)

        if 'test_date' in kwargs:
            test_date = datetime.strptime(kwargs["test_date"], "%d/%m/%y").date()
            if 'test_time' in kwargs:
                test_time = datetime.strptime(kwargs["test_time"], "%H:%M").time()
                time_now = datetime.combine(test_date, test_time)

            else:
                raise Exception('No time given')
        else:
            time_now = datetime.now()

        fin_time = start_time + timedelta(seconds=self.total_time)
        delta_hours = (fin_time - time_now) / timedelta(hours=1)
        delta_hours = abs(delta_hours)
        if delta_hours >= 60:
            raise Exception(
                'Outwith 60 hour range, predicted finish time in {} hours'.format(delta_hours))

        self.ride_start_time = self.time_zone.localize(start_time)


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
            with open(kwargs['loadPrev'], 'rb') as dict_file:
                loaded_dict = pickle.load(dict_file)

            self.__dict__.update(loaded_dict.__dict__)
        elif 'xmlfile' in kwargs:
            TcxRide.__init__(self, xmlfile=kwargs['xmlfile'])
        elif 'strava_course' in kwargs:
            TcxRide.__init__(self, strava_course=kwargs['strava_course'])
        else:
            raise Exception('No reasonable input given: see docstring')

    def get_weather_data(self, apikey, **kwargs):
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
        if self.weather_data:
            raise Exception('Data already exists')

        if self.len:
            print('Gathering weather data...')
        else:
            raise Exception('Data not decimated not making API call')
        for itr in range(0, self.len):
            url = '{0}{1}/{2},{3}?exclude=daily,alerts,flags&units={4}'.format(
                urlprov, apikey, self.lat[itr], self.lon[itr], kwargs['units'])
            data = requests.get(url).content
            if 'fileDirectory' in kwargs:
                if 'fileName' in kwargs:
                    if not os.path.exists(kwargs['fileDirectory']):
                        os.makedirs(kwargs['fileDirectory'])
                    file = open(
                        '{0}/{1}{2}.json'.format(kwargs['fileDirectory'],
                                                 kwargs['fileName'], itr), 'wb')
                    file.write(data)
                    file.close()

            self.weather_data.append(json.loads(data))
        print('Gathered weather data')

    def load_existing_data(self, location):
        """
        Loads existing JSON format weather data
        Args:

            location (str): file path and base name of the multiple JSON files

       """

        if self.weather_data:
            raise Exception('Data already exists')
        for itr in range(0, self.len):
            filename = '{0}{1}.json'.format(location, itr)
            # print('Loading' filename)
            with open(filename) as data_file:
                self.weather_data.append(json.load(data_file))

    def clear_weather_data(self):

        """
        Call function to remove .weather_data from object
        This will allow you to re-generate new weather data
        """

        del self.weather_data

    def get_forecast(self, **kwargs):

        """
        Adds forecast to self
        Keyword Args:

            fileDirectory(str): Path for files to be saved ie: myDir/myInnerDir
            fileName(str): File name

        """

        for itr in range(0, self.len):
            # self..append(self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]][""])
            forecast_time = self.time_zone.localize(
                datetime.fromtimestamp(int(self.weather_data[itr]["currently"]["time"])))
            delta_time = (self.time[itr] - forecast_time)
            time_mins = (np.round((delta_time / timedelta(minutes=1)))).astype(int)
            time_hr = (np.round((delta_time / timedelta(hours=1)))).astype(int)
            hour_weather = self.weather_data[itr]["hourly"]["data"][time_hr]

            self.weather['wind_bearing'].append(hour_weather["windBearing"])
            self.weather['apparent_temperature'].append(hour_weather["apparentTemperature"])
            self.weather['cloud_cover'].append(hour_weather["cloudCover"])
            self.weather['dew_point'].append(hour_weather["dewPoint"])
            self.weather['humidity'].append(hour_weather["humidity"])
            self.weather['icon'].append(hour_weather["icon"])
            self.weather['ozone'].append(hour_weather["ozone"])
            self.weather['pressure'].append(hour_weather["pressure"])
            self.weather['summary'].append(hour_weather["summary"])
            self.weather['temperature'].append(hour_weather["temperature"])
            self.weather['time_hour_time'].append(hour_weather["time"])
            self.weather['visibility'].append(hour_weather["visibility"])
            self.weather['wind_bearing'].append(hour_weather["windBearing"])
            self.weather['wind_speed'].append(hour_weather["windSpeed"])
            self.weather['rel_wind_bear'].append(
                (hour_weather['windBearing'] - self.bear[itr]) % 360)
            self.weather['wind_head'].append(
                np.sin(np.deg2rad(hour_weather["rel_wind_bear"])) * hour_weather["windSpeed"])
            self.weather['wind_cross'].append(
                np.cos(np.deg2rad(hour_weather["rel_wind_bear"])) * hour_weather["windSpeed"])
            if time_mins < 60:
                minute_weather = self.weather_data[itr]["minutely"]["data"][time_mins]
                self.weather['precip_probability'].append(minute_weather["precipProbability"])
                self.weather['precip_intensity'].append(minute_weather["precipIntensity"])
                if minute_weather["precipIntensity"] > 0:
                    self.weather['precip_type'].append(minute_weather["precipType"])
                else:
                    self.weather['precip_type'].append("None")
            else:
                self.weather['precip_intensity'].append(hour_weather["precipIntensity"])
                self.weather['precip_probability'].append(hour_weather["precipProbability"])
                if hour_weather["precipIntensity"] > 0:
                    self.weather['precip_type'].append(hour_weather["precipType"])
                else:
                    self.weather['precip_type'].append("None")
            if 'fileDirectory' in kwargs:
                if 'fileName' in kwargs:
                    with open('{0}/{1}.pkl'.format(kwargs['fileDirectory'],
                                                   kwargs['fileName']), 'wb') as output:
                        pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)


class GeoFuncs:
    """
    Class to perform static functions.

    """
    @staticmethod
    def bearing_func(lat, lon):
        """
        Calculates bearing given latitude and longitude
        Args:
    
            lat (list): Latitude list
            lon (list): Longitude list
        """

        bearing = list()
        bearing.append(0)
        phi = list()
        lambd = list()
        for deg in lat:
            phi.append(np.deg2rad(deg))
        for deg in lon:
            lambd.append(np.deg2rad(deg))
        for itr in range(1, len(lat)):
            arc_a = np.sin(lambd[itr] - lambd[itr - 1]) * np.cos(phi[itr])
            arc_b = np.cos(phi[itr - 1]) * np.sin(phi[itr]) \
                    - np.sin(phi[itr - 1]) * np.cos(phi[itr]) * np.cos(lambd[itr] - lambd[itr - 1])
            bearing.append(np.degrees(np.arctan2(arc_a, arc_b)) % 360)
        return bearing
