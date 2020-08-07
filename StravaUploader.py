#!/usr/bin/env python3
import os
import json
import http.cookiejar
import re
import argparse
import binascii
from requests import Request, Session
import urllib.parse


parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument("username", help="Strava Username")
parser.add_argument("password", help="Strava Password")
args = parser.parse_args()

def ImportToStrava(url, username, password, baseDir, file) :
    s = Session()

    # acquire cookie
    response = s.get(url);
    text = response.text

    # Get authenticity_token
    try:
        token = re.search(r'type="hidden" name="authenticity_token" value="(.+?)"', text).group(1)
    except AttributeError as e:
        print('Cannot find token')
        return

    #print ('found token:' + token)

    # Login
    loginData = urllib.parse.urlencode({
        'utf8' : '&#x2713;',
        'authenticity_token' : token,
        'plan' : '',
        'email' : username, 
        'password' : password})
    binary_data = loginData.encode('utf-8')
    try:
        #response = opener.open("https://www.strava.com/session", binary_data);
        response = s.post("https://www.strava.com/session", data=loginData);
    except Exception as e:
        print('unknown error: ')
        return
    else:
        print('Successfully logged in')

    # Get upload file page
    try:
        #response = opener.open("http://www.strava.com/upload/select");
        response = s.get("http://www.strava.com/upload/select");
    except Exception as e:
        print('unknown error: ')
        return
    else:
        print('Successfully got upload page')

    files = {
        "_method" : (None, "post"),
        "authenticity_token" : (None,token) ,
        "files[]": (file,open(baseDir + "/" + file, 'rb'), 'text/xml')
    }

    req = Request('POST', 'http://www.strava.com/upload/files', files=files).prepare()
    #print(req.body.decode('utf8'))

    try:
        #response = s.post("http://www.strava.com/upload/files", data=files)
        response = s.send(req)
    except Exception as e:
        print('unknown error: ' + baseDir + file)
    else:
        print('Successfully uploaded file -->' + baseDir + file)
        #print(response.content.decode('utf-8'))
        print(response.status_code)
        print(response.text)

    print('imported all files')

def main() :
    # login to strava and upload file.
    ImportToStrava(
                "https://www.strava.com/login",
        args.username,
        args.password,
                os.path.dirname(args.gpx),
                os.path.basename(args.gpx))

if __name__ == "__main__":
    main()
