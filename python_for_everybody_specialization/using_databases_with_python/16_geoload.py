import urllib.request, urllib.parse, urllib.error
import http
import sqlite3
import json
import time
import ssl
import sys

serviceurl = 'http://py4e-data.dr-chuck.net/opengeo?'

conn = sqlite3.connect('using_databases_with_python/opengeo.sqlite')
cur = conn.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS Locations (address TEXT, geodata TEXT)')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

location = 'using_databases_with_python/where.data'
handle = open(location)

count = 0
nofound = 0
for line in handle:
    if count > 270:
        print('Retrieved 270 locations, restart to retrieve more')
        break

    address = line.strip()
    print('')
    cur.execute('SELECT geodata FROM Locations WHERE address=?', (memoryview(address.encode()),))

    try:
        data = cur.fetchone()[0]
        print('Found in database', address)
        continue
    except:
        pass

    params = dict()
    params['q'] = address

    url = serviceurl + urllib.parse.urlencode(params)

    print('Retrieving', url)
    urlhandle = urllib.request.urlopen(url, context=ctx)
    data = urlhandle.read().decode()
    print('Retrieved', len(data), 'characters', data[:20].replace('\n', ' '))
    count += 1

    try:
        js = json.loads(data)
    except:
        print(data)
        continue

    if not js or 'features' not in js:
        print('=== Download error ===')
        print(data)
        break

    if len(js['features']) == 0:
        print('=== Object not found ===')
        nofound += 1

    cur.execute('INSERT INTO Locations (address, geodata) VALUES (?, ?)', (memoryview(address.encode()), memoryview(data.encode()),))

    conn.commit()
    
    if count % 10 == 0:
        print('Pausing for a bit...')
        # time.sleep(5)

if nofound > 0:
    print('Number of features for which the location could not be found,', nofound)

print('Run geodump.py to read the data from the database so you visualize it on a map.')