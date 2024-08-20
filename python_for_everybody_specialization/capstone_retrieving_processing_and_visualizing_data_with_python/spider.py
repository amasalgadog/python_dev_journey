import sqlite3
import urllib.error
import ssl
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS Pages
    (id INTEGER PRIMARY KEY, url TEXT UNIQUE, html TEXT,
     error INTEGER, old_rank REAL, new_rank REAL)''')
# when doing page rank work we're going to have old rank and new rank
# take the old rank then computes the new rank and replace it

cur.execute('''CREATE TABLE IF NOT EXISTS Links
    (from_id INTEGER, to_id INTEGER, UNIQUE(from_id, to_id))''')
# many-2-many table poiting to other tables, inbound outbound

cur.execute('''CREATE TABLE IF NOT EXISTS Webs (url TEXT UNIQUE)''')
# in case we have more than one web

# Check to see if we are already in progress...
cur.execute('SELECT id,url FROM Pages WHERE html is NULL and error is NULL ORDER BY RANDOM() LIMIT 1')
# NULL serves as indicator when a page has not yet been retrieve

row = cur.fetchone()
# when fetching a row, if there's None then try again by asking for an url
if row is not None:
    print("Restarting existing crawl.  Remove spider.sqlite to start a fresh crawl.")
else :
    # asking for a website
    starturl = input('Enter web url or enter: ')

    # if no web was given then do dr-chuck.com
    if ( len(starturl) < 1 ) : starturl = 'http://www.dr-chuck.com/'

    # if the website ends with / , delete it from the url
    if ( starturl.endswith('/') ) : starturl = starturl[:-1]
    web = starturl

    if ( starturl.endswith('.htm') or starturl.endswith('.html') ) :
        # if the website ends with .htm or .html (a webpage within the website)
        # then retrieved the website from where it's located
        pos = starturl.rfind('/')
        # retrieved the position of the last occurrence of the placeholder /
        # then cut down the website url up to this position
        web = starturl[:pos]

    # insert the processed website into Webs table and the initial website in Pages table
    if ( len(web) > 1 ) :
        cur.execute('INSERT OR IGNORE INTO Webs (url) VALUES ( ? )', ( web, ) )
        cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES ( ?, NULL, 1.0 )', ( starturl, ) )
        conn.commit()

# Get the current webs and put them inside a list, then print them
cur.execute('''SELECT url FROM Webs''')
webs = list()
for row in cur:
    webs.append(str(row[0]))

print(webs)


many = 0
while True:
    # first while loop iteration - ask for how many pages
    if ( many < 1 ) :
        sval = input('How many pages:')
        if ( len(sval) < 1 ) : break
        many = int(sval)
    many = many - 1

    # look for a null html from Pages table and fetch the id and url from a random one
    cur.execute('SELECT id,url FROM Pages WHERE html is NULL and error is NULL ORDER BY RANDOM() LIMIT 1')
    try:
        row = cur.fetchone()
        # print row
        fromid = row[0]
        url = row[1]
    except:
        print('No unretrieved HTML pages found')
        many = 0
        break

    print(fromid, url, end=' ')

    # If we are retrieving this page, there should be no links from it
    # Wipe out all of the links because it's unretrieved
    # Links is the connection table that connects from pages back to pages
    cur.execute('DELETE from Links WHERE from_id=?', (fromid, ) )
    try:
        document = urlopen(url, context=ctx)
        # grab the url and read it
        html = document.read()
        if document.getcode() != 200 :
            print("Error on page: ",document.getcode())
            cur.execute('UPDATE Pages SET error=? WHERE url=?', (document.getcode(), url) )
        # if we get an error then we don't retrieved the page anymore

        if 'text/html' != document.info().get_content_type() :
            print("Ignore non text/html page")
            cur.execute('DELETE FROM Pages WHERE url=?', ( url, ) )
            # cur.execute('UPDATE Pages SET error=0 WHERE url=?', (url, ))
            conn.commit()
            continue
        # if the content type is not text/html the wipe out from the Pages tables
        # content such JPEG or so. Then we commit and continue

        print('('+str(len(html))+')', end=' ')

        soup = BeautifulSoup(html, "html.parser")
    except KeyboardInterrupt:
        # this will jump if you press Ctrl C or Ctrl Z (windows)
        print('')
        print('Program interrupted by user...')
        break
    except:
        # we set an error equals to -1 for the page if any other error occur so we don't retrieve it again
        print("Unable to retrieve or parse page")
        cur.execute('UPDATE Pages SET error=-1 WHERE url=?', (url, ) )
        # commit it
        conn.commit()
        continue

    # at this point, we finally got the html for the url, so we insert it (or ignore it in the case it's already there) in the table
    # and setting the Page Rank to 1
    cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES ( ?, NULL, 1.0 )', ( url, ) )
    # update the Pages table for making sure to retain it
    cur.execute('UPDATE Pages SET html=? WHERE url=?', (memoryview(html), url ) )
    # commit it
    conn.commit()

    # Retrieve all of the anchor tags
    tags = soup('a')
    count = 0
    for tag in tags:
        href = tag.get('href', None)
        if ( href is None ) : continue
        # Resolve relative references like href="/contact"
        up = urlparse(href)
        if ( len(up.scheme) < 1 ) :
            href = urljoin(url, href)
        ipos = href.find('#')
        if ( ipos > 1 ) : href = href[:ipos]
        if ( href.endswith('.png') or href.endswith('.jpg') or href.endswith('.gif') ) : continue
        if ( href.endswith('/') ) : href = href[:-1]
        # print href
        if ( len(href) < 1 ) : continue

		# Check if the URL is in any of the webs
        found = False
        for web in webs:
            if ( href.startswith(web) ) :
                found = True
                break
        if not found : continue
        # if the link left the site, skip it

        cur.execute('INSERT OR IGNORE INTO Pages (url, html, new_rank) VALUES ( ?, NULL, 1.0 )', ( href, ) )
        count = count + 1
        conn.commit()

        cur.execute('SELECT id FROM Pages WHERE url=? LIMIT 1', ( href, ))
        try:
            row = cur.fetchone()
            toid = row[0]
        except:
            print('Could not retrieve id')
            continue
        # print fromid, toid
        cur.execute('INSERT OR IGNORE INTO Links (from_id, to_id) VALUES ( ?, ? )', ( fromid, toid ) )


    print(count)

cur.close()
