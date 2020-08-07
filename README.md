# pebble-hr-to-gpx
Pebble 2HR watch extract heart rate measurements and add HR data to a given GPX file

host accept-file.php on a webserver

make uploads/health.csv writable

In the watchface settings point to accept-file.php

The field is "key"

```
  usage: gpx-pebble-hr.py [-h] gpx csv out

  positional arguments:
    gpx         The gpx file to add heart rate data to
    csv         The pebble health csv, column 1 time YYYY-mm-ddTHH:MI:SSZ,
                column 8 hr value
    out         The output gpx file

  optional arguments:
    -h, --help  show this help message and exit
```

![](screenshots/strava_hr.jpg?raw=true)


The following script could be executed to take your latest GPX, add health data and upload to Strava
assuming you have synced your pebble-health
```
  STRAVAUSER=user
  STRAVAPASS=pass
  GPXDIR="/path/to/GPX/"
  FILE=`find ${GPXDIR} -maxdepth 1 -type f -iname "*.gpx" -mtime -1 | tail 1`
  PEBBLE_HEALTH="/var/www/localhost/htdocs/pebble-health/uploads/health.csv"
  OUTFILE=${GPXDIR}/HR/$(basename "${FILE}")
  if [[ -f "${FILE}" ]]; then
    if [[ ! -f "${OUTFILE}" ]]; then
      gpx-pebble-hr.py "${FILE}" "${PEBBLE_HEALTH}" "${OUTFILE}"
      ./StravaUploader.py "${OUTFILE}" ${STRAVAUSER} ${STRAVAPASS}
    fi
  fi
```
