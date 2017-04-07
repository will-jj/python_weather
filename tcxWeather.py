"""
tcxWeather
"""
import os
import pickle
import json
from datetime import datetime, timedelta #unused time, date

import requests
import tcxparser
import numpy as np

from pytz import timezone


class TcxRide:
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
        self.strava_time = self.raw.time_values()
        self.length = len(self.strava_time)
        self.latitude = self.raw.latitude_points()
        self.longitude = self.raw.longitude_points()
        self.distance = self.raw.distance_points()
        self.distance_total = self.distance[self.length-1]
        self.time_zone = timezone('Europe/London')


        self.bearing = list()
        self.bear = list()

        self.mph = 0
        self.mps = 0
        self.kph = 0

        self.len = 0


        self.lat = 0 # np.array()
        self.lon = 0 # np.array()
        self.dist = 0 # np.array()

        self.time = list()


        self.time_seconds = list()
        self.total_time = 0

        self.ride_start_time = 0 #datetime
        self.weather_data = list()
        self.precip_intensity = list()
        self.wind_bearing = list()
        self.rel_wind_bear = list()
        self.apparent_temperature = list()
        self.cloud_cover = list()
        self.dew_point = list()
        self.humidity = list()
        self.icon = list()
        self.ozone = list()

        self.precip_probability = list()
        self.precip_type = list()
        self.pressure = list()
        self.summary = list()
        self.temperature = list()
        self.visibility = list()
        self.wind_bearing = list()
        self.wind_speed = list()
        self.forecast_time = list()
        self.delta_time = list()
        self.time_hr = list()
        self.time_min = list()
        self.time_hour_time = list()



    def __bearing(self):
        self.bearing = bearing_func(self.latitude, self.longitude)

    def __bearingdec(self):
        self.bear = bearing_func(self.lat, self.lon)

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
        self.__time()

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
            num_points = self.distance_total/distance
        elif 'Points' in kwargs:
            num_points = kwargs['Points']
        elif 'Time' in kwargs:
            if hasattr(self, 'mps'):
                num_points = self.total_time/kwargs['Time']
            else:
                raise Exception('no speed defined use x.Speed(mps =y | kph =z | mph =w)')
        else:
            raise Exception('Define decimation in terms of Distance= (m)| Points = (n)| Time = (s)')

        num_points = np.floor(num_points).astype(int)
        print('Decimating to {0} Points'.format(num_points))
        ind = np.linspace(0, (self.length-1), num_points, endpoint=True, retstep=False, dtype=None)
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
            delta_dist = self.dist[itr]-self.dist[itr-1]
            time_sec_add += delta_dist/self.mps
            time_sec_add = int(np.floor(time_sec_add))
            combined = self.ride_start_time + timedelta(seconds=time_sec_add)
            self.time.append(combined)


    def __time(self):
        self.time_seconds.append(0)
        timetot = 0
        for itr in range(1, self.length):
            delta_dist = self.distance[itr]-self.distance[itr-1]
            timetot += delta_dist/self.mps
            self.time_seconds.append(int(timetot))
        self.total_time = timetot



    def set_ride_start_time(self, **kwargs):

        """
        Enter ride start time

        Keyword Args:

            Date (str): Enter date in format d/m (if not entered defaults to today)
            Time (str): Enter ride start time in format H:M

        """

        if self.mps == 0:
            raise Exception('Please input ride speed first')

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
        delta_hours = (fin_time-time_now)/timedelta(hours=1)
        delta_hours = abs(delta_hours)
        if delta_hours >= 60:
            raise Exception(
                'Outwith 60 hour forecast range, your finish time is {} from now'.format(delta_hours))



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
            TcxRide.__init__(self, kwargs['xmlfile'])
        else:
            raise  Exception('No xmlfile=filestr or loadPrev = picklestring given')

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
        if  self.weather_data:
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
                        '{0}/{1}{2}.json'.format(kwargs['fileDirectory'], kwargs['fileName'], itr), 'wb')
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
            self.forecast_time.append(
                self.time_zone.localize(datetime.fromtimestamp(int(self.weather_data[itr]["currently"]["time"]))))
            self.delta_time.append(
                (self.time[itr] - self.forecast_time[itr]))
            self.time_min.append(
                (np.round((self.delta_time[itr] / timedelta(minutes=1)))).astype(int))
            self.time_hr.append(
                (np.round((self.delta_time[itr] / timedelta(hours=1)))).astype(int))
            self.wind_bearing.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["windBearing"])
            self.apparent_temperature.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["apparentTemperature"])
            self.cloud_cover.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["cloudCover"])
            self.dew_point.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["dewPoint"])
            self.humidity.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["humidity"])
            self.icon.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["icon"])
            self.ozone.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["ozone"])
            self.pressure.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["pressure"])
            self.summary.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["summary"])
            self.temperature.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["temperature"])
            self.time_hour_time.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["time"])
            self.visibility.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["visibility"])
            self.wind_bearing.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["windBearing"])
            self.wind_speed.append(
                self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["windSpeed"])
            self.rel_wind_bear.append(
                (self.wind_bearing[itr] - self.bear[itr]) % 360)
            if (self.time_min[itr]) < 60:
                self.precip_probability.append(
                    self.weather_data[itr]["minutely"]["data"][self.time_min[itr]]["precipProbability"])
                self.precip_intensity.append(
                    self.weather_data[itr]["minutely"]["data"][self.time_min[itr]]["precipIntensity"])
                if self.precip_intensity[itr] > 0:
                    self.precip_type.append(
                        self.weather_data[itr]["minutely"]["data"][self.time_min[itr]]["precipType"])
                else:
                    self.precip_type.append("None")
            else:
                self.precip_intensity.append(
                    self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["precipIntensity"])
                self.precip_probability.append(
                    self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["precipProbability"])
                if self.precip_intensity[itr] > 0:
                    self.precip_type.append(
                        self.weather_data[itr]["hourly"]["data"][self.time_hr[itr]]["precipType"])
                else:
                    self.precip_type.append("None")
            if 'fileDirectory' in kwargs:
                if 'fileName' in kwargs:
                    with open('{0}/{1}.pkl'.format(kwargs['fileDirectory'], kwargs['fileName']), 'wb') as output:
                        pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)


def bearing_func(lat, lon):
    bearing = list()
    bearing.append(0)
    phi = list()
    lambd = list()
    for deg in lat:
        phi.append(np.deg2rad(deg))
    for deg in lon:
        lambd.append(np.deg2rad(deg))
    for itr in range(1, len(lat)):
        arc_a = np.sin(lambd[itr]-lambd[itr-1]) * np.cos(phi[itr])
        arc_b = np.cos(phi[itr-1])*np.sin(phi[itr]) - np.sin(phi[itr-1])*np.cos(phi[itr])*np.cos(lambd[itr]-lambd[itr-1])
        bearing.append(np.degrees(np.arctan2(arc_a, arc_b))%360)
    return bearing
    
