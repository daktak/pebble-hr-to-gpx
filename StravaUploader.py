#!/usr/bin/env python3
import os
import re
import json
import time
import uuid
import argparse
from html import unescape
from requests import Session
from requests_toolbelt.multipart.encoder import MultipartEncoder

UPLOAD_URL = "https://www.strava.com/upload/files"
SELECT_URL = "https://www.strava.com/upload/select"
PROGRESS_URL = "https://www.strava.com/upload/progress.json"
PHOTO_METADATA_URL = "https://www.strava.com/photos/metadata"
EDIT_URL = "https://www.strava.com/activities/%s/edit"
ACTIVITY_URL = "https://www.strava.com/activities/%s"

SPORT_TYPES = {
    "AlpineSki": "Alpine Ski",
    "BackcountrySki": "Backcountry Ski",
    "Badminton": "Badminton",
    "Basketball": "Basketball",
    "Canoeing": "Canoe",
    "ClassicNordicSki": "Classic Nordic Ski",
    "Crossfit": "Crossfit",
    "Cricket": "Cricket",
    "Dance": "Dance",
    "EBikeRide": "E-Bike Ride",
    "EMountainBikeRide": "E-Mountain Bike Ride",
    "Elliptical": "Elliptical",
    "Golf": "Golf",
    "GravelRide": "Gravel Ride",
    "Handcycle": "Handcycle",
    "HighIntensityIntervalTraining": "HIIT",
    "Hike": "Hike",
    "IceSkate": "Ice Skate",
    "InlineSkate": "Inline Skate",
    "Kayaking": "Kayaking",
    "Kitesurf": "Kitesurf",
    "MountainBikeRide": "Mountain Bike Ride",
    "NordicSki": "Nordic Ski",
    "Padel": "Padel",
    "PhysicalTherapy": "Physical Therapy",
    "Pickleball": "Pickleball",
    "Pilates": "Pilates",
    "Racquetball": "Racquetball",
    "Ride": "Ride",
    "RockClimbing": "Rock Climb",
    "RollerSki": "Roller Ski",
    "Rowing": "Rowing",
    "Run": "Run",
    "Sail": "Sail",
    "SkateNordicSki": "Skate Nordic Ski",
    "Skateboard": "Skateboard",
    "Snowboard": "Snowboard",
    "Snowshoe": "Snowshoe",
    "Soccer": "Football (Soccer)",
    "Squash": "Squash",
    "StairStepper": "Stair-Stepper",
    "StandUpPaddling": "Stand Up Paddling",
    "Surfing": "Surfing",
    "Swim": "Swim",
    "TableTennis": "Table Tennis",
    "Tennis": "Tennis",
    "TrailRun": "Trail Run",
    "Velomobile": "Velomobile",
    "VirtualRide": "Virtual Ride",
    "VirtualRow": "Virtual Row",
    "VirtualRun": "Virtual Run",
    "Volleyball": "Volleyball",
    "Walk": "Walk",
    "WeightTraining": "Weight Training",
    "Wheelchair": "Wheelchair",
    "Windsurf": "Windsurf",
    "Workout": "Workout",
    "Yoga": "Yoga",
}

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument(
    "--session", default="session.json", help="Path to saved session cookies JSON"
)
parser.add_argument("--name", help="Name to set on the uploaded activity")
parser.add_argument(
    "--type",
    choices=sorted(SPORT_TYPES),
    metavar="TYPE",
    help="Activity type to set on the uploaded activity. "
    "Valid values: " + ", ".join(sorted(SPORT_TYPES)),
)
parser.add_argument(
    "--photos",
    nargs="*",
    default=[],
    metavar="PHOTO",
    help="Image files to attach to the uploaded activity",
)
parser.add_argument(
    "--tags",
    help="Comma/space separated tags to set on the uploaded activity",
)
parser.add_argument(
    "--private",
    choices=["everyone", "followers", "only_me"],
    metavar="PRIVACY",
    help="Activity visibility: everyone, followers, or only_me",
)
parser.add_argument(
    "--mute",
    action="store_true",
    help="Mute the activity from home and club feeds",
)
args = parser.parse_args()


def load_session(s, path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False
    for c in data.get("cookies", []):
        s.cookies.set(
            c["name"],
            c["value"],
            domain=c.get("domain", ".strava.com"),
            path=c.get("path", "/"),
        )
    return True


def valid_session(s):
    try:
        return "Upload and Sync Your Activities" in s.get(SELECT_URL).text
    except Exception:
        return False


def wait_ready(s, upload_id):
    for _ in range(60):
        r = s.get(PROGRESS_URL, params={"ids[]": upload_id})
        item = r.json()[0]
        if item.get("workflow") == "success":
            return item
        if item.get("workflow") in ("error", "empty"):
            return None
        time.sleep(1)
    return None


def key_for(data, *cands):
    for c in cands:
        if c in data:
            return c
    return cands[0]


def parse_form(form):
    data = {}
    for m in re.finditer(r"<input\b[^>]*>", form):
        tag = m.group(0)
        if re.search(r"\bdisabled\b|\btype=[\"'](?:submit|button|file)[\"']", tag):
            continue
        name = re.search(r'name="([^"]+)"', tag)
        if not name:
            continue
        name = unescape(name.group(1))
        val = re.search(r'value="([^"]*)"', tag)
        val = unescape(val.group(1)) if val else ""
        if re.search(r'type="checkbox"', tag):
            if re.search(r"\bchecked\b", tag):
                data[name] = val or "1"
        else:
            data[name] = val
    for m in re.finditer(r"<select\b[^>]*>.*?</select>", form, re.S):
        tag = m.group(0)
        if re.search(r"\bdisabled\b", tag):
            continue
        name = re.search(r'name="([^"]+)"', tag)
        if not name:
            continue
        opts = re.findall(r"<option\b([^>]*)>(.*?)</option>", tag, re.S)
        if not opts:
            continue

        def optval(attrs, text):
            m = re.search(r'value="([^"]*)"', attrs)
            return unescape(m.group(1)) if m else unescape(text)

        chosen = [o for o in opts if "selected" in o[0]]
        data[unescape(name.group(1))] = optval(*(chosen or opts)[0])
    for m in re.finditer(r"<textarea\b[^>]*>.*?</textarea>", form, re.S):
        tag = m.group(0)
        name = re.search(r'name="([^"]+)"', tag)
        if not name:
            continue
        val = re.search(r">(.*)</textarea>", tag, re.S)
        data[unescape(name.group(1))] = unescape(val.group(1)) if val else ""
    return data


def find_field(form, *cands):
    for c in cands:
        if re.search(r'name="%s"' % re.escape(c), form):
            return c
    return None


def upload_photo(s, token, athlete_id, photo):
    uid = str(uuid.uuid4())
    taken_at = int(os.path.getmtime(photo) * 1000)
    r = s.put(
        PHOTO_METADATA_URL,
        data={"athlete_id": athlete_id, "uuid": uid, "taken_at": taken_at},
        headers={"X-CSRF-Token": token},
    )
    if not r.ok:
        print("Photo metadata failed: " + photo)
        return None
    with open(photo, "rb") as f:
        raw = f.read()
    r = s.put(r.json()["uri"], data=raw, headers=r.json()["header"])
    if not r.ok:
        print("Photo upload failed: " + photo)
        return None
    return uid


def update_activity(
    s, aid, name=None, sport_type=None, photos=None, tags=None, private=None, mute=False
):
    edit = s.get(EDIT_URL % aid)
    if not edit.ok:
        print("Unable to get activity edit page")
        return
    m = re.search(r'name="authenticity_token" value="([^"]+)"', edit.text)
    if not m:
        print("Cannot find authenticity token on edit page")
        return
    token = unescape(m.group(1))
    m = re.search(r"var athleteId = (\d+);", edit.text)
    if not m:
        print("Cannot find athlete id on edit page")
        return
    athlete_id = int(m.group(1))
    m = re.search(r'<form class="edit_activity".*?</form>', edit.text, re.S)
    if not m:
        print("Cannot find edit form on edit page")
        return
    data = parse_form(m.group(0))
    data.setdefault("_method", "patch")
    if name:
        data[key_for(data, "activity[name]", "name")] = name
        print("Setting activity name to: " + name)
    if sport_type:
        key = key_for(
            data, "activity[sport_type]", "sport_type", "activity[type]", "type"
        )
        data[key] = sport_type
    count = 0
    for photo in photos or []:
        uid = upload_photo(s, token, athlete_id, photo)
        if not uid:
            continue
        data["photos[%s][caption]" % uid] = ""
        data["photos[%s][rank]" % uid] = str(count)
        data["photos[%s][media_type]" % uid] = "1"
        count += 1
    if count:
        print("Attaching " + str(count) + " photo(s)")
    mute_key = None
    if tags:
        tlist = [t for t in re.split(r"[,\s]+", tags.strip()) if t]
        data["activity[tag_list]"] = ",".join(tlist)
        print("Setting tags: " + ", ".join(tlist))
    privacy_values = {
        "everyone": "everyone",
        "followers": "followers_only",
        "only_me": "only_me",
    }
    if private:
        data["activity[visibility]"] = privacy_values[private]
        print("Setting privacy to: " + private)
    if mute:
        mute_key = find_field(m.group(0), "activity[hide_from_home]", "hide_from_home")
        if mute_key:
            data[mute_key] = "true"
            print("Muting activity")
        else:
            print("Mute checkbox not found in edit form; skipping")
    if (
        not name
        and not sport_type
        and not count
        and not tags
        and not private
        and not mute
    ):
        return
    r = s.post(ACTIVITY_URL % aid, data=data)
    if r.ok:
        if name:
            print("Activity name updated")
        if sport_type:
            print("Activity type updated")
        if count:
            print("Attached " + str(count) + " photo(s) to activity")
        if tags:
            print("Tags updated")
        if private:
            print("Privacy updated")
        if mute and mute_key:
            print("Mute updated")
    else:
        print("Failed to save activity: " + r.text[:200])


def ImportToStrava(
    gpx,
    session_path,
    name=None,
    sport_type=None,
    photos=None,
    tags=None,
    private=None,
    mute=False,
):
    s = Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    baseDir = os.path.dirname(gpx) or "."
    file = os.path.basename(gpx)

    if load_session(s, session_path) and valid_session(s):
        print("Using saved session")
    else:
        print("No valid session found.")
        print("Export a logged-in session to session.json (see README).")
        return

    response = s.get(SELECT_URL)
    if "Upload and Sync Your Activities" in response.text:
        print("Successfully got upload page")
    else:
        print("Unable to get upload page")
        return

    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', response.text)
    if not m:
        m = re.search(r'name="authenticity_token" value="([^"]+)"', response.text)
    if not m:
        print("Cannot find authenticity token on upload page")
        return
    token = unescape(m.group(1))

    mp_encoder = MultipartEncoder(
        fields={
            "_method": "post",
            "authenticity_token": token,
            "files[]": (file, open(baseDir + "/" + file, "rb"), "text/xml"),
        }
    )

    try:
        response = s.post(
            UPLOAD_URL,
            data=mp_encoder,
            headers={"Content-Type": mp_encoder.content_type},
        )
    except Exception:
        print("unknown error: " + baseDir + file)
    else:
        if "workflow" not in response.text:
            print(response.text)
            return
        print("Successfully uploaded file -->" + baseDir + "/" + file)
        if not name and not photos and not tags and not private and not mute:
            return
        for upload in response.json():
            item = wait_ready(s, upload.get("id"))
            if not item:
                print("Upload did not finish processing: " + file)
                return
            act = item.get("activity") or item
            aid = act.get("id")
            if not aid:
                print("No activity id in upload response")
                return
            if name or photos or tags or private or mute:
                update_activity(s, aid, name, sport_type, photos, tags, private, mute)


def main():
    ImportToStrava(
        args.gpx,
        args.session,
        args.name,
        args.type,
        args.photos,
        args.tags,
        args.private,
        args.mute,
    )


if __name__ == "__main__":
    main()
