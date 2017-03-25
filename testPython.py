from tcxWeather import  RideWeather as RdWth
from pprint import pprint
from matplotlib import pyplot as plt
import numpy as np
plt.close("all")
steve= RdWth(loadPrev='weatherTAKCROW2/CrowTakPickle.pkl')
# steve = RdWth(xmlfile='TakCrowPopularityCreated.tcx')print(steve.length)
steve.speed(kph=25)
steve.setRideStartTime(date ="25/03", time = "20:00")
steve.decimate(Points=10)

# steve.getWeatherData('apiremoved', fileDirectory='weatherTAKCROW2', fileName='weatherdataDemoTCX',units='si')
# steve.loadExistingData('weatherTAKCROW2/weatherdataDemoTCX')
# steve.getForecast(fileDirectory='weatherTAKCROW2', fileName='CrowTakPickle')

'''
pprint(steve.precipIntensity)
print('Wind bearing:' ,steve.windBearing[3])
print('Rider bearing:' ,steve.bear[3])
print('Rel bearing:',steve.relWindBear[3])
'''

myBear = list()
# -180:180 plots nicer
for x in steve.relWindBear:
    myBear.append(x - 180)
fig = plt.figure()
ax = fig.gca()


plt.stem(steve.dist,steve.relWindBear)
plt.xlabel('Distance [m]')
plt.ylabel('Relative Wind Bearing [degrees]')
plt.title('Relative Wind Bearing')
plt.grid()


fig2 = plt.figure()
ax2 = fig.gca()
plt.plot(steve.dist,steve.windSpeed)
plt.xlabel('Distance [m]')
plt.ylabel('Wind Speed [kph]')
plt.title('Wind Speed')
plt.grid()



fig3 = plt.figure()
ax3 = fig.gca()
plt.plot(steve.dist,steve.precipProbability)
plt.xlabel('Distance [m]')
plt.ylabel('Probability')
plt.title('Precipitation Probability')
plt.grid()


fig4 = plt.figure()
ax4 = fig.gca()
plt4,plt5 = plt.plot(steve.dist, steve.apparentTemperature, steve.dist, steve.temperature)
plt.xlabel('Distance [m]')
plt.ylabel(r"Temperature ""$^oC$")
plt.title('Temperature')
plt.legend([plt4,plt5], ['Apparent Temperature', 'Actual Temperature'])
plt.grid()
plt.show()
