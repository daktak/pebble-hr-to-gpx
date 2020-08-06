#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import argparse
import csv
from xml.etree.ElementTree import Element, tostring
from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to add heart rate data to")
parser.add_argument("csv", help="The pebble health csv, column 1 time YYYY-mm-ddTHH:MI:SSZ, column 8 hr value")
parser.add_argument("out", help="The output gpx file")
args = parser.parse_args()

tree = ET.parse(args.gpx)
root = tree.getroot()

ns = dict([
    node for _, node in ET.iterparse(
        args.gpx, events=['start-ns']
    )
])
ns['gpxtpx'] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
#register namespaces for writing the file
for k in ns:
    ET.register_namespace(k,ns[k])

hr_times = {}

with open(args.csv) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        time = row[0]
        #2016-05-25T21:22:00Z
        if row[7]:
            if row[7] != "0":
                hr_times[time+"+00:00"] = row[7]

#set default for find
ns['default']=ns['']

hr_rate = ''

for trk in root:
    for trkseg in trk:
        for trkpt in trkseg.findall("default:trkpt", ns):
            time = trkpt.find("default:time", ns)
            #2020-08-03T13:03:32+10:00
            dttm = datetime.strptime(time.text, "%Y-%m-%dT%H:%M:%S%z")
            for hr_time in hr_times:
                hr_dttm = datetime.strptime(hr_time,"%Y-%m-%dT%H:%M:%SZ%z")
                if hr_dttm <= dttm:
                    minutes_ago = dttm - timedelta(minutes = 3)
                    if hr_dttm >= minutes_ago:
                        hr_rate = hr_times[hr_time]
                    else:
                        hr_rate = ''
            #If we have a HR beet for this this point
            if hr_rate:
                extensions = trkpt.find("default:extensions", ns)
                if not extensions:
                    extensions = ET.SubElement(trkpt, "extensions")
                tpe = ET.SubElement(extensions, "gpxtpx:TrackPointExtension")
                hr = ET.SubElement(tpe, "gpxtpx:hr")
                #set the hr
                hr.text = hr_rate
root.set("xmlns:gpxtpx", ns['gpxtpx'])
tree.write(args.out, xml_declaration = True, encoding = 'utf-8', method = 'xml', short_empty_elements = True)
