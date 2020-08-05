#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import csv
from xml.etree.ElementTree import Element, tostring
from datetime import datetime, timedelta
tree = ET.parse('track.gpx')
root = tree.getroot()

ns = dict([
    node for _, node in ET.iterparse(
        'track.gpx', events=['start-ns']
    )
])
#register namespaces for writing the file
for k in ns:
    ET.register_namespace(k,ns[k])

hr_times = {}

with open('pebble.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        time = row[0]
        #2016-05-25T21:22:00Z
        hr_times[time] = row[7]

#set default for find
ns['default']=ns['']

hr_rate = ''

for trk in root:
    for trkseg in trk:
        for trkpt in trkseg.findall("default:trkpt", ns):
            time = trkpt.find("default:time", ns)
            #2020-08-03T13:03:32+10:00
            dttm = datetime.strptime(time.text, "%Y-%m-%dT%H:%M:%S%z")
            extensions = trkpt.find("default:extensions", ns)
            for hr_time in hr_times:
                hr_dttm = datetime.strptime(hr_time,"%Y-%m-%dT%H:%M:%SZ")
                if hr_dttm <= dttm.replace(tzinfo=None):
                    minutes_ago = dttm.replace(tzinfo=None) - timedelta(minutes = 3)
                    if hr_dttm >= minutes_ago:
                        hr_rate = hr_times[hr_time] 
                    else:
                        hr_rate = ''
            #If we have a HR beet for this this point
            if hr_rate:
                tpe = ET.SubElement(extensions, "gpxtpx:TrackPointExtension")
                hr = ET.SubElement(tpe, "gpxtpx:hr")
                #set the hr
                hr.text = hr_rate

tree.write('output.xml', xml_declaration = True, encoding = 'utf-8', method = 'xml')
