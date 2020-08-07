#!/usr/bin/env python3
import os
import json
import http.cookiejar
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import re
import zipfile
import glob
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("gpx", help="The gpx file to upload")
parser.add_argument("username", help="Strava Username")
parser.add_argument("password", help="Strava Password")
args = parser.parse_args()

def ImportToStrava(url, username, password, baseDir, file) :
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # acquire cookie
    home = opener.open(url)
    text = home.read().decode('utf-8')

    # Get authenticity_token
    try:
        token = re.search(r'type="hidden" name="authenticity_token" value="(.+?)"', text).group(1)
    except AttributeError as e:
        print('Cannot find token')
        return
    
    # print 'found token:' + token

    # Login
    loginData = urllib.parse.urlencode({
        'utf8' : '&#x2713;',
        'authenticity_token' : token,
        'plan' : '',
        'email' : username, 
        'password' : password})
    binary_data = loginData.encode('utf-8')
    try:
        response = opener.open("https://www.strava.com/session", binary_data);
    except urllib.error.HTTPError as e:
        print('unknown error: ')
        return
    else:
        print('Successfully logged in')

    # Get upload file page
    try:
        response = opener.open("http://www.strava.com/upload/select");
    except urllib.error.HTTPError as e:
        print('unknown error: ')
        return
    else:
        print('Successfully got upload page')
    
    params = { "_method" : "post", "authenticity_token" : token,
             "files[]" : open(baseDir + "/" + file, "r").read() }

    try:
        response = opener.open("http://www.strava.com/upload/files", data=bytes(json.dumps(params), encoding="utf-8"))
    except urllib.error.HTTPError as e:
        print('unknown error: ' + baseDir + file)
    else:
        print('Successfully uploaded file -->' + baseDir + file)
    
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
