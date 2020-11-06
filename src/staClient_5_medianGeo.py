# -*- coding: UTF-8 -*-
#staClient_5_medianGeo.py
from __future__ import absolute_import, division, print_function, unicode_literals
import requests
import json
import sys
import pandas as pd
#import matplotlib.pyplot as plt

def getObservations(linkObserv: str, proxies: dict) -> pd.Series:
    """Methode getObservations gibt eine pandas series fuer die Zeitreihe zurueck.
    
    Args:
        linkObserv: str with url observations
        proxies: dict with proxies
        
    Returns:
        pd.Series mit Zeitreihe
        
    Raises:
        ConnectionError for Service is down
    """
    resultDict = {}
    zaehler = 0; count = 100; skip = 100
    
    while zaehler < count:   
        jsonData = None
        url = '%s%s%s' % (linkObserv, '?$orderBy=phenomenonTime asc&$count=true&$top=100&$skip=', zaehler)
        r = requests.get(url, proxies=proxies)
        
        if r.status_code == 200:
            jsonData = json.loads(r.text)
            count = jsonData['@iot.count']
            zaehler += skip
            
            for o in jsonData['value']:
                tmpTime = o['phenomenonTime'].split('T')[0]
                resultDict.update({tmpTime: o['result']})
        else:
            message = '%s: %s' % (r.status_code, 'Service is down')
            raise ConnectionError(message)
        
    s = pd.Series(resultDict)
    s.name = 'Observations:', linkObserv
    return s
    
def main():
    """
    1. Nehme alle Things mit 'name' == 'Verkehrszählstelle ...'.
    2. Fuer diese Things nehme jeweils den Datastream mit 'name' == '... 1-Tag-Intervall'.
    3. Fuer jeden dieser Datastreams hole alle Observations und
       a) ermittle fuer jede Zeitreihe den Median
       b) write to csv (location;x;y;thing;stream;observations;count;median)
    """
    fileDir = r'D:\IoT\output\radzaehlung_download.csv'
    
    proxies = {
        'http': 'http://111.11.111.111:80',
        'https': 'http://111.11.111.111:80',
        }
    
    #1. Things with filter
    jsonDataThings = None
    urlStaThings = 'https://iot.hamburg.de/v1.1/Things?$count=true&$filter=startswith(name,\'Verkehrszählstelle\')&$select=name,@iot.id,@iot.selfLink,Datastreams&$expand=Locations($select=name,location)'
    rThings = requests.get(urlStaThings, proxies=proxies)
    
    if rThings.status_code == 200:
        jsonDataThings = json.loads(rThings.text)
        
        with open(fileDir, 'w', encoding='utf-8') as f:
            f.write('location;x;y;thing;stream;observations;count;median\n')
            
            for element in jsonDataThings['value']:
                thingLink = element['@iot.selfLink']
                locationName = element['Locations'][0]['name']
                x = element['Locations'][0]['location']['geometry']['coordinates'][0]
                y = element['Locations'][0]['location']['geometry']['coordinates'][1]
                
                #2. DataStream with filter
                jsonDataStream = None    
                urlStream = '%s%s' % (element['Datastreams@iot.navigationLink'], '?$count=true&$filter=endswith(name,\'1-Tag-Intervall\')&$select=name,@iot.id,@iot.selfLink,Observations,properties')
                rStream = requests.get(urlStream, proxies=proxies)
                
                if rStream.status_code == 200:
                    jsonDataStream = json.loads(rStream.text)
                    streamLink = jsonDataStream['value'][0]['@iot.selfLink']
                    
                    #3. Observations
                    try:
                        s = getObservations(jsonDataStream['value'][0]['Observations@iot.navigationLink'], proxies)
                        f.write('%s;%s;%s;%s;%s;%s;%s;%s\n' % (locationName, x, y, thingLink, streamLink, jsonDataStream['value'][0]['Observations@iot.navigationLink'], s.size, s.median()))
                        print(locationName)
                        
                        #if thingLink == 'https://iot.hamburg.de/v1.1/Things(5564)' or thingLink == 'https://iot.hamburg.de/v1.1/Things(5565)' or thingLink == 'https://iot.hamburg.de/v1.1/Things(5566)':
                        ##if thingLink == 'https://iot.hamburg.de/v1.1/Things(5576)' or thingLink == 'https://iot.hamburg.de/v1.1/Things(5575)' or thingLink == 'https://iot.hamburg.de/v1.1/Things(5577)':
                            #s.plot.line()
                    except ConnectionError:
                        print('%s; %s' % (sys.exc_info()[0], sys.exc_info()[1]))
                else:
                    print('%s: %s' % (rStream.status_code, 'Service is down'))
                    
            #plt.title('Observations 1Tag Intervall')
            #plt.ylabel('Fahrradaufkommen (Anzahl)')
            #plt.xlabel('Zeitintervall (Tag)')
            #plt.legend()
            #plt.show()
    else:
        print('%s: %s' % (rThings.status_code, 'Service is down'))
        sys.exit()
        
if __name__ == '__main__':
    main()
    