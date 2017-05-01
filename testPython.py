from tcxweather import RideWeather as RdWth
from pprint import pprint
#from matplotlib import pyplot as plt
import stravalib
import numpy as np
#plt.close("all")
#steve= RdWth(loadPrev='weatherTAKCROW2/CrowTakPickle.pkl')
token = 'no'
client = stravalib.client.Client()
client.access_token = token
stream_memes = client.get_route_streams(8079319)

steve = RdWth(strava_course=stream_memes)
#print(steve.length)
steve.speed(kph=25)
steve.set_ride_start_time(date ="12/03", time = "15:00",test_date = '12/03/17',test_time = "10:00")
steve.decimate(Points=10)

# steve.getWeatherData('apiremoved', fileDirectory='weatherTAKCROW2', fileName='weatherdataDemoTCX',units='si')
steve.load_existing_data('weatherData/weatherdataDemoTCX')
# steve.getForecast(fileDirectory='weatherTAKCROW2', fileName='CrowTakPickle')
steve.get_forecast()
'''
pprint(steve.precip_intensity)
print('Wind bearing:' ,steve.wind_bearing[3])
print('Rider bearing:' ,steve.bear[3])
print('Rel bearing:',steve.rel_wind_bear[3])
'''

WIND_BEARING = list()
# -180:180 plots nicer
for x in steve.rel_wind_bear:
    WIND_BEARING.append(x - 180)
#fig = plt.figure()
#ax = fig.gca()
pprint(WIND_BEARING)
"""
plt.stem(steve.dist,steve.rel_wind_bear)
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
"""
