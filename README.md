# pebble-hr-to-gpx

Pebble 2HR watch extract heart rate measurements and add HR data to a given GPX file

host accept-file.php on a webserver

make uploads/health.csv writable

In the watchapp settings point to accept-file.php

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
  STRAVAUSER=user@email.com
  STRAVAPASS=pass
  GPXDIR="/path/to/GPX/"
  FILE=`find ${GPXDIR} -maxdepth 1 -type f -iname "*.gpx" -mtime -1 | tail -1`
  PEBBLE_HEALTH="/var/www/localhost/htdocs/pebble-health/uploads/health.csv"
  OUTFILE=${GPXDIR}/HR/$(basename "${FILE}")
  if [[ -f "${FILE}" ]]; then
    if [[ ! -f "${OUTFILE}" ]]; then
      gpx-pebble-hr.py "${FILE}" "${PEBBLE_HEALTH}" "${OUTFILE}"
      ./StravaUploader.py "${OUTFILE}" ${STRAVAUSER} ${STRAVAPASS}
    fi
  fi
```

## Python requirements

```
pip install -r requirements.txt
```

Or directly:

```
pip install requests requests-toolbelt python-dateutil
```

On Debian/Ubuntu where system Python is externally managed (PEP 668), use a virtual
environment instead:

```
python3 -m venv .venv
.venv/bin/pip install requests requests-toolbelt python-dateutil
.venv/bin/python ./StravaUploader.py test.gpx
```

## StravaUploader login

`StravaUploader.py` uploads to Strava using your Google login. Credentials are your Google
account email/password:

```
  ./StravaUploader.py out.gpx you@gmail.com your-google-password
```

If you prefer not to type your Google password on the command line, or your account has
two-step verification (which the automated login cannot handle), export a logged-in session
once and reuse it:

1. Log in to https://www.strava.com in a browser (via Google or otherwise).
2. Open DevTools (F12) -> Console and run `document.cookie`.
3. Copy the value of `_strava4_session=...` into `session.json` next to the script:

```json
{
  "cookies": [
    {
      "name": "_strava4_session",
      "value": "PASTE_VALUE_HERE",
      "domain": ".strava.com",
      "path": "/"
    }
  ]
}
```

4. Run `./StravaUploader.py out.gpx` (no credentials needed while the session is valid).
   A fresh session is saved back to `session.json` after each automated Google login.
