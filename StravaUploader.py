#!/usr/bin/env python3
import os
import re
import json
import argparse
from html import unescape
from requests import Session
from requests_toolbelt.multipart.encoder import MultipartEncoder

UPLOAD_URL = "https://www.strava.com/upload/files"
SELECT_URL = "https://www.strava.com/upload/select"

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument(
    "--session", default="session.json", help="Path to saved session cookies JSON"
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


def ImportToStrava(gpx, session_path):
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
        if "workflow" in response.text:
            print("Successfully uploaded file -->" + baseDir + "/" + file)
        else:
            print(response.text)


def main():
    ImportToStrava(args.gpx, args.session)


if __name__ == "__main__":
    main()
