# -*- coding: utf-8 -*-
"""
@author: Ivan
"""
import gpxpy
import gpxpy.gpx
from subprocess import check_output
from os.path import isfile
from os import listdir
from datetime import datetime,timedelta
import numpy as np
from haversine import haversine
import calendar

#%% Get GPS coordinates of photos in a directory
filedir = r'C:\GPS tagged photos'
lats,lons,elevs,times = ([],[],[],[])
for file in listdir(filedir):
    print(file)
    filepath = filedir + '\\' + file
    GPS = check_output('exiftool -GPSLatitude -GPSLongitude -GPSAltitude -GPSDateTime -n "%s"'
                 %filepath).decode()
    if isfile(filepath) and GPS: #If not empty string
        GPS = GPS.split('\r\n')
        lats.append(float(GPS[0].split(': ')[1]))
        lons.append(float(GPS[1].split(': ')[1]))
        elevs.append(float(GPS[2].split(': ')[1]))
        times.append(datetime.strptime(GPS[3].split(': ')[1], '%Y:%m:%d %H:%M:%SZ'))
        
#%% Filter GPS data
arc = np.array([haversine((lats[i], lons[i]),(lats[i+1], lons[i+1])) for i in range(len(lats)-1)]) #Distance between 2 points in km
arc = np.append(0.01, arc)

delta_t = np.array([(times[i+1]-times[i]).total_seconds()/3600 for i in range(len(lats)-1)])
delta_t = np.append(1, delta_t)

velocity = arc/delta_t

ind = np.array(velocity<30) * np.array(arc>0) #filter by speed less than 30km/hr and photos with no diplacement
lats,lons,elevs,times = (np.array(lats)[ind],
                         np.array(lons)[ind],
                         np.array(elevs)[ind],
                         np.array(times)[ind])

#%% GPX file of photo routes
gpx = gpxpy.gpx.GPX()
gpx_track = gpxpy.gpx.GPXTrack() #GPX track
gpx.tracks.append(gpx_track)
gpx_segment = gpxpy.gpx.GPXTrackSegment() #Segment of GPX track
gpx_track.segments.append(gpx_segment)

# Create points for track
for lat,lon,elev,time,vel,d in zip(lats,lons,elevs,times,velocity,arc):
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=elev, time=time))

with open("Tracks_from_photos.gpx","w") as f:
    f.write(gpx.to_xml())
    
#%% Use "GPX to Strava Route" (https://labs.strava.com/gpx-to-route/)
input("Press Enter to proceed")

#%% Append interpolated times to the Strava generated GPX track
def getclosestpoint(trk_lat,trk_lon,lat,lon):
    return np.argmin(np.sqrt((np.array(trk_lon)-lon)**2 + (np.array(trk_lat)-lat)**2))
    
def toTimestamp(d):
    return calendar.timegm(d.timetuple())

def toDateTime(ts):
    return datetime.fromtimestamp(ts)-timedelta(hours=9) #Subtracting by JST

TimSt = [toTimestamp(d) for d in times]

# Get lat lon of Strava GPX file
gpx_file = open('Strava_gpx.gpx', 'r')
gpx = gpxpy.parse(gpx_file)
trk_lat, trk_lon = ([],[])
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            trk_lat.append(point.latitude) 
            trk_lon.append(point.longitude) 
keypoint = [getclosestpoint(trk_lat,trk_lon,lat_i,lon_i) for lat_i,lon_i in zip(lats,lons)] #Keypoints of track matching the defined waypoints

# Interpolate the datetimes for the track between the waypoints
trk_date = list(map(toDateTime,np.interp(np.arange(keypoint[0],keypoint[1]+1),keypoint,TimSt))) #Interpolate time between keypoints
for ind in range(len(keypoint)-2):
    trk_date = trk_date + list(map(toDateTime,np.interp(np.arange(keypoint[ind+1]+1,keypoint[ind+2]+1),keypoint,TimSt)))
    
for point,d in zip(gpx.tracks[0].segments[0].points,trk_date):
    point.time = d
    
with open("Strava_gpx_with_timestamp.gpx",'w') as f:
    f.write(gpx.to_xml())
