import tcxWeather
from pprint import pprint
from matplotlib import pyplot as plt
import numpy as np



plt.close("all")
steve= tcxWeather.RideWeather()
steve.speed(kph=25)
steve.setRideStartTime(date ="12/03", time = "15:32")
steve.decimate(Time=1000)
steve.loadExistingData('weatherData/weatherdataDemoTCX')
steve.getForecast()
pprint(steve.precipIntensity)
print('Wind bearing:' ,steve.windBearing[3])
print('Rider bearing:' ,steve.bear[3])
print('Rel bearing:',steve.relWindBear[3])
##steve.getWeatherData(apikey='XXXXXXXXXX',units='si',writeF=True)

myBear = list()
# -180:180 plots nicer
for x in steve.relWindBear:
    myBear.append(x - 180);
fig = plt.figure()
ax = fig.gca()

# ax.set_xticks(numpy.arange(0,1,0.1))
# ax.set_yticks(numpy.arange(0,1.,0.1))
plt.plot(steve.timeMin,myBear,'r--')
plt.xlabel('Delta Weather Time [mins]')
plt.ylabel('Relative Wind Bearing [degrees]')
plt.title('Relative Wind Bearing')
plt.grid()
plt.show()
