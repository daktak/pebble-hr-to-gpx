#!/usr/bin/env python3
import os
import json
import re
import argparse
import binascii
from requests import Request, Session
import urllib.parse
from requests_toolbelt.multipart.encoder import MultipartEncoder


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
        m = re.search('Log Out', response.text)
        if m:
            print('Successfully logged in')
        else:
            print('Unsuccessfull login')
            return

    # Get upload file page
    try:
        response = s.get("https://www.strava.com/upload/select");
    except Exception as e:
        print('unknown error: ')
        return
    else:
        m = re.search('Upload and Sync Your Activities', response.text)
        if m:
            print('Successfully got upload page')
        else:
            print('Unable to get upload page')
            return

    mp_encoder = MultipartEncoder(fields={
        "_method" : "post",
        "authenticity_token" : token,
        "files[]": (file,open(baseDir + "/" + file, 'rb'), 'text/xml')
    })

    try:
        response = s.post('https://www.strava.com/upload/files',data=mp_encoder,headers={'Content-Type': mp_encoder.content_type})
    except Exception as e:
        print('unknown error: ' + baseDir + file)
    else:
        m = re.search('workflow', response.text)
        if m:
            print('Successfully uploaded file -->' + baseDir +"/"+ file)
        else:
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
