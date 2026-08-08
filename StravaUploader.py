#!/usr/bin/env python3
import os
import re
import json
import argparse
from html import unescape
from urllib.parse import urlparse, parse_qsl
from requests import Request, Session
from requests_toolbelt.multipart.encoder import MultipartEncoder

LOGIN_URL = "https://www.strava.com/login"
UPLOAD_URL = "https://www.strava.com/upload/files"
SELECT_URL = "https://www.strava.com/upload/select"

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument("email", nargs="?", help="Google account email for automated login")
parser.add_argument(
    "password", nargs="?", help="Google account password for automated login"
)
parser.add_argument(
    "--session", default="session.json", help="Path to saved session cookies JSON"
)
args = parser.parse_args()


def hidden_fields(html):
    fields = {}
    for tag in re.findall(r"<input[^>]*>", html):
        if not re.search(r'type="?hidden"?', tag):
            continue
        name = re.search(r'name="([^"]+)"', tag)
        if not name:
            continue
        value = re.search(r'value="([^"]*)"', tag)
        fields[name.group(1)] = unescape(value.group(1)) if value else ""
    return fields


def query_fields(url):
    return dict(parse_qsl(urlparse(url).query))


def google_login(s, email, password):
    login = s.get(LOGIN_URL)
    auth = next(
        (
            u
            for u in re.findall(
                r"(https://accounts\.google\.com/o/oauth2/auth[^\"'<>]+)", login.text
            )
            if "google_web_signin" in u
        ),
        None,
    )
    if not auth:
        print("Cannot find Google sign-in URL on login page")
        return False
    auth = auth.replace("\\u0026", "&").replace("&amp;", "&")

    r = s.get(auth)
    if "oauthchooseaccount" in r.url:
        m = re.search(
            r'href="([^"]*oauthchooseaccount[^"]*)"[^>]*>(?:(?!</li>).)*?'
            + re.escape(email),
            r.text,
            re.S,
        )
        if not m:
            print("Google account chooser shown; cannot pick account", email)
            return False
        r = s.get(m.group(1))
    if "v3/signin/identifier" not in r.url:
        print("Unexpected Google login page:", r.url)
        return False

    data = hidden_fields(r.text)
    data.update(query_fields(r.url))
    data.update({"bgresponse": "js_disabled", "pstMsg": "1", "identifier": email})
    r = s.post(r.url, data=data)

    if "challenge/password" in r.url or 'type="password"' in r.text:
        data = hidden_fields(r.text)
        data.update(query_fields(r.url))
        pwd = re.search(r'<input[^>]*type="?password"?[^>]*name="([^"]+)"', r.text)
        data.update(
            {"bgresponse": "js_disabled", pwd.group(1) if pwd else "password": password}
        )
        r = s.post(r.url, data=data)

    if "/signin/oauth/consent" in r.url:
        data = hidden_fields(r.text)
        data.update(query_fields(r.url))
        if "consent" in data or "consentContinue" in data:
            r = s.post(r.url, data=data)
        else:
            print("Google consent page shown but not understood:", r.url)
            return False

    if any(
        k in r.url
        for k in (
            "challenge/ipp",
            "challenge/totp",
            "challenge/gated",
            "captcha",
            "rejected",
            "notmyaccount",
        )
    ):
        print("Google presented a 2FA/security challenge:", r.url)
        print(
            "Automated login cannot continue. Export a session manually into session.json (see README)."
        )
        return False
    if "strava.com" in r.url:
        return True
    print("Login flow ended at unexpected URL:", r.url)
    return False


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


def save_session(s, path):
    cookies = [
        {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
        for c in s.cookies
        if "strava.com" in (c.domain or "")
    ]
    with open(path, "w") as f:
        json.dump({"cookies": cookies}, f, indent=2)


def valid_session(s):
    try:
        return "Upload and Sync Your Activities" in s.get(SELECT_URL).text
    except Exception:
        return False


def ImportToStrava(gpx, email, password, session_path):
    s = Session()
    s.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    baseDir = os.path.dirname(gpx) or "."
    file = os.path.basename(gpx)

    if load_session(s, session_path) and valid_session(s):
        print("Using saved session")
    elif email and password:
        if not google_login(s, email, password):
            return
        save_session(s, session_path)
        print("Logged in via Google")
    else:
        print("No valid session and no credentials given.")
        print(
            "Export a logged-in session to session.json (see README) or pass email and password arguments."
        )
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
    ImportToStrava(args.gpx, args.email, args.password, args.session)


if __name__ == "__main__":
    main()
