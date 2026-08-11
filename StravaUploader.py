#!/usr/bin/env python3
import os
import re
import json
import time
import argparse
from html import unescape
from requests import Session
from requests_toolbelt.multipart.encoder import MultipartEncoder

UPLOAD_URL = "https://www.strava.com/upload/files"
SELECT_URL = "https://www.strava.com/upload/select"
PROGRESS_URL = "https://www.strava.com/upload/progress.json"
BULK_UPDATE_URL = "https://www.strava.com/athlete/training_activities/bulk_update"

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument(
    "--session", default="session.json", help="Path to saved session cookies JSON"
)
parser.add_argument("--name", help="Name to set on the uploaded activity")
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


def rename_fields(act, aid, name):
    data = {"id": aid, "name": name}
    for key in (
        "description",
        "commute",
        "trainer",
        "workout_type",
        "bike_id",
        "athlete_gear_id",
    ):
        if key in act:
            data[key] = act[key]
    if "type" in act:
        data["sport_type"] = act["type"]
    return data


def rename(s, act, aid, name, token):
    r = s.post(
        BULK_UPDATE_URL,
        json={"activities": [rename_fields(act, aid, name)]},
        headers={"X-CSRF-Token": token},
    )
    if r.ok:
        print("Set activity name to: " + name)
    else:
        print("Failed to set name: " + r.text)


def ImportToStrava(gpx, session_path, name=None):
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
        if not name:
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
            rename(s, act, aid, name, token)


def main():
    ImportToStrava(args.gpx, args.session, args.name)


if __name__ == "__main__":
    main()
