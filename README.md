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
  GPXDIR="/path/to/GPX/"
  FILE=`find ${GPXDIR} -maxdepth 1 -type f -iname "*.gpx" -mtime -1 | tail -1`
  PEBBLE_HEALTH="/var/www/localhost/htdocs/pebble-health/uploads/health.csv"
  OUTFILE=${GPXDIR}/HR/$(basename "${FILE}")
  if [[ -f "${FILE}" ]]; then
    if [[ ! -f "${OUTFILE}" ]]; then
      gpx-pebble-hr.py "${FILE}" "${PEBBLE_HEALTH}" "${OUTFILE}"
      ./StravaUploader.py "${OUTFILE}"
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

`StravaUploader.py` uploads to Strava using a saved session cookie. Login is only supported via a
session file; automated Google email/password login is not available.

Export a logged-in session once and reuse it:

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

## Setting the activity name

`StravaUploader.py` names the activity after the uploaded file by default. To override it, pass
`--name`; after the file finishes processing the activity is renamed on Strava:

```
./StravaUploader.py out.gpx --name "Morning Ride"
```

## Setting the activity type

Pass `--type` to change the activity type after upload (e.g. `GravelRide`, `VirtualRide`, `Run`).
Run `./StravaUploader.py --help` to list all valid types:

```
./StravaUploader.py out.gpx --type GravelRide --name "Gravel Ride"
```

## Attaching photos

Pass one or more image files with `--photos` to attach them to the uploaded activity. Images are
uploaded through Strava's photo endpoint and then attached by submitting the activity edit form:

```
./StravaUploader.py out.gpx --photos screenshot1.jpg screenshot2.jpg
```

The name, type and photos are all applied in a single edit-form submission, so when
`--name`/`--type` are combined with `--photos` they are saved together in one transaction.

Photo attachment is best-effort: if an individual image fails to upload or the final save fails,
the already-uploaded activity is left untouched and the script just prints what went wrong.

## Setting tags, privacy and mute

These are also applied via the activity edit form (the same `/activities/<id>/edit` submission used
for name/type/photos), so they can be combined with any of the other options in one transaction.

- `--tags` — comma or space separated tags, e.g. `--tags "ride, commute"` or `--tags ride commute`.
- `--private` — activity visibility: `everyone`, `followers`, or `only_me`.
- `--mute` — mute the activity from home and club feeds.

```
./StravaUploader.py out.gpx --tags "ride, commute" --private followers --mute
```

These map to Strava's edit-form fields: tags → `activity[tag_list]`, privacy → `activity[visibility]`
(`everyone` / `followers_only` / `only_me`), and mute → `activity[hide_from_home]`. If the mute
checkbox is not present in the form (e.g. Strava changes its UI), the script prints a warning and
skips that part of the update rather than failing.
