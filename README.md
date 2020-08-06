# pebble-hr-to-gpx
Pebble 2HR watch extract heart rate measurements and add HR data to a given GPX file

host accept-file.php on a webserver

make uploads/health.csv writable

In the watchface settings point to accept-file.php

The field is "key"


  usage: gpx-pebble-hr.py [-h] gpx csv out

  positional arguments:
    gpx         The gpx file to add heart rate data to
    csv         The pebble health csv, column 1 time YYYY-mm-ddTHH:MI:SSZ,
                column 8 hr value
    out         The output gpx file

  optional arguments:
    -h, --help  show this help message and exit
