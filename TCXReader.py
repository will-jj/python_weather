import numpy as np
import tcxparser
import json,requests,os,time,calendar

from datetime import datetime,timedelta,date, time

from pytz import timezone

class tcxWeather:
    
    
    def __init__(self, xmlfile='demoRoute.tcx'):
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
        self.bearing.append(0) #first bearing 0
        φ = list()
        λ = list()
        for x in self.latitude:
            φ.append(np.deg2rad(x))
        for x in self.longitude:
            λ.append(np.deg2rad(x))
        
        for x in range(1,self.length):
            y = np.sin(λ[x]-λ[x-1]) * np.cos(φ[x])
            x = np.cos(φ[x-1])*np.sin(φ[x]) - np.sin(φ[x-1])*np.cos(φ[x])*np.cos(λ[x]-λ[x-1])
            self.bearing.append(np.degrees(np.arctan2(y, x))%360)
       
    
    def __bearingdec__(self): #fix to one function for both bearings
        self.bear = list()
        self.bear.append(0) #first bearing 0
        φ = list()
        λ = list()
        for x in self.lat:
            φ.append(np.deg2rad(x))
        for x in self.lon:
            λ.append(np.deg2rad(x))
        
        for x in range(1,len(self.lat)):
            y = np.sin(λ[x]-λ[x-1]) * np.cos(φ[x])
            x = np.cos(φ[x-1])*np.sin(φ[x]) - np.sin(φ[x-1])*np.cos(φ[x])*np.cos(λ[x]-λ[x-1])
            self.bear.append(np.degrees(np.arctan2(y, x))%360) #0-360 instead of -180:180
            
       
    def speed(self,**kwargs):
        mps_mph = 2.23694
        mps_kph = 3.6
        if 'mph' in kwargs:
            self.mph = kwargs['mph']
            self.mps = self.mph/mps_mph
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
        
        
            
            
            
    def decimate(self,**kwargs): #todo add variable input parameters such as dist=10km or time = 1hr or numpoints = 20
        if 'Distance' in kwargs:
            distance = kwargs['Distance']
            #points not constant this is average
            numPoints = self.distanceTotal/distance
            
        if 'Points' in kwargs:
            numPoints = kwargs['Points']
        if 'Time' in kwargs:
            if hasattr(self, 'mps'):
                numPoints = self.totalTime/kwargs['Time']
            else:
                raise Exception('no speed defined use x.Speed(mps =y | kph =z | mph =w)')
            
        else:
            numPoints = 10
        numPoints = np.floor(numPoints).astype(int)
        print('Decimating to {0} Points'.format(numPoints))   
        ind = np.linspace(0, (self.length-1),numPoints, endpoint=True, retstep=False, dtype=None)
        ind = np.floor(ind)
        ind = ind.astype(int)
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
      
        time=0
        self.time.append(self.rideStartTime)
        for x in range(1,self.len):
            delDist = self.dist[x]-self.dist[x-1]
            time += delDist/self.mps  
           
            combined = self.rideStartTime + timedelta(seconds=time)
            
            self.time.append(combined)
        
    def __time__(self):
        self.timeSeconds = list()
        self.timeSeconds.append(0)
        time=0
        for x in range(1,self.length):
            delDist = self.distance[x]-self.distance[x-1]
            time += delDist/self.mps
            self.timeSeconds.append(int (time))
        self.totalTime = time           
        
        
    def getWeatherData(self,apikey='none',units='si',writeF=False):
        if hasattr(self,'weatherData'):
             raise Exception('Data already exists')
        self.weatherData = list()
        
        if hasattr(self, 'len'):
            print('Gathering weather data...')
        else:
            raise Exception('Data not decimated not making API call')

        
        for x in range(0,self.len):
            url='https://api.darksky.net/forecast/{0}/{1},{2}?exclude=daily,alerts,flags?units={3}'.format(apikey,self.lat[x],self.lon[x],units)
            data = (requests.get(url).content)
            if writeF:
                if not os.path.exists('weatherData'):
                    os.makedirs('weatherData')
                file = open('weatherData/weatherdataDemoTCX{0}.json'.format(x),'wb')     
                file.write(data)
                file.close
            self.weatherData.append(json.loads(data))
        print('Gathered weather data')
    
    
    def loadExistingData(self,location):
        if hasattr(self,'weatherData'):
             raise Exception('Data already exists')
        self.weatherData = list()
                   
        for x in range(0,self.len):
            filename = '{0}{1}.json'.format(location,x)
            #print('Loading' filename)
            with open(filename) as data_file:  
                self.weatherData.append(json.load(data_file))

    def clearWeatherData(self):
        del self.weatherData
            
    def getForecast(self): #potentially make this its own class inheriting from tcxweather
        self.precipIntensity= list()
        self.windBearing = list()
        self.relWindBear = list()
        self.apparentTemperature = list()
        self.cloudCover=list()
        self.dewPoint=list()
        self.humidity=list()
        self.icon=list()
        self.ozone=list()
        self.precipIntensity=list()
        self.precipProbability=list()
        self.precipType=list()
        self.pressure=list()
        self.summary=list()
        self.temperature=list()
        self.visibility=list()
        self.windBearing=list()
        self.windSpeed=list()
        self.forecastTime=list()
        self.deltaTime=list()
        self.timeHr=list()
        self.timeMin=list()
        
        for x in range(0,self.len):
            #self..append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]][""])
           
            self.forecastTime.append(self.tZ.localize(datetime.fromtimestamp(int(self.weatherData[x]["currently"]["time"]))))
             
            self.deltaTime.append((self.time[x]-self.forecastTime[x]))
            self.timeMin.append((np.round((self.deltaTime[x]/timedelta(minutes=1)))).astype(int))
            self.timeHr.append((np.round((self.deltaTime[x]/timedelta(hours=1)))).astype(int))
            
                                  
                                
            
            self.windBearing.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windBearing"])
            self.apparentTemperature.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["apparentTemperature"])
            self.cloudCover.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["cloudCover"])
            self.dewPoint.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["dewPoint"])
            self.humidity.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["humidity"])
            self.icon.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["icon"])
            self.ozone.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["ozone"])
            
            self.pressure.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["pressure"])
            self.summary.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["summary"])
            self.temperature.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["temperature"])
            self.time.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["time"])
            self.visibility.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["visibility"])
            self.windBearing.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windBearing"])
            self.windSpeed.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["windSpeed"])
            self.relWindBear.append((self.windBearing[x]-self.bear[x])%360)
            
            if (self.timeMin[x])<60:
 
                self.precipProbability.append(self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipProbability"])
                self.precipIntensity.append(self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipIntensity"])
                if self.precipIntensity[x]>0:               
                    self.precipType.append(self.weatherData[x]["minutely"]["data"][self.timeMin[x]]["precipType"])
                else:
                    self.precipType.append("None")
            else:
                self.precipIntensity.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipIntensity"])
                self.precipProbability.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipProbability"])
                if self.precipIntensity[x]>0:               
                    self.precipType.append(self.weatherData[x]["hourly"]["data"][self.timeHr[x]]["precipType"])
                else:
                    self.precipType.append("None")
                    
                

            
           
            
    def setRideStartTime(self,**kwargs): #COMPLETE (Check is in range of forecast)
     
        if 'date' in kwargs:
            date = datetime.strptime(kwargs["date"], "%d/%m").date()
            date = date.replace(year=datetime.today().year)
        else:
            date= datetime.today().date()
        if 'time' in kwargs:
            time = datetime.strptime(kwargs["time"], "%H:%M").time()
        self.rideStartTime = datetime.combine(date, time)
        self.rideStartTime = self.tZ.localize(self.rideStartTime)   
     
            
    
            

