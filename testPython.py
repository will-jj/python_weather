from pprint import pprint
import tcxWeather


steve=tcxWeather.tcxWeather()
steve.speed(kph=25)
steve.setRideStartTime(date ="12/03",time = "15:32")
steve.decimate(Time=1000)
steve.loadExistingData('weatherData/weatherdataDemoTCX')
steve.getForecast()
pprint(steve.precipIntensity)
print('Wind bearing:',steve.windBearing[3])
print('Rider bearing:',steve.bear[3])
print('Rel bearing:',steve.relWindBear[3])
##steve.getWeatherData(apikey='XXXXXXXXXX',units='si',writeF=True)