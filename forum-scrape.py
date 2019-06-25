#!/usr/bin/env python3

import boto3
import json
import requests
import datetime
import urllib3

# hate doing this but the RI's CA is strangely not lining up, even though the CA is found
urllib3.disable_warnings()

# using the JSON feed spec: https://jsonfeed.org/version/1
#SITE_URL = "https://www.robotic.industries/community/"
BASE_URL = "https://www.robotic.industries/community/"
S3_KEY = 'rss/buildone.json'

def write_json_feed(items):
  feed = {
    'version': 'https://jsonfeed.org/version/1',
    'title': 'Robotic Industries Buildone Community Feed',
    'user_comment': "parsed from robotic.industries because I won't visit a forum without notifications.",
    'author': { 'name': 'tedder', 'url': 'https://tedder.me' },
    'home_page_url': BASE_URL,
    'feed_url': 'https://dyn.tedder.me/' + S3_KEY,
    'items': items
    # expired <- true when this feed is dead
  }

  s3 = boto3.client('s3')
  s3.put_object(
    ACL='public-read',
    Body=json.dumps(feed),
    Bucket='dyn.tedder.me',
    Key=S3_KEY,
    ContentType='application/json',
    CacheControl='public, max-age=30' # todo: 3600
  )


r = requests.get(BASE_URL + "api/discussions", verify=False)
threads = r.json()
users = {}
posts = {}
items = []
for i in threads.get('included', []):
  if i.get('type') == 'users':
    _id = i['id']
    users[_id] = {'name': i['attributes']['username']}
for i in threads.get('included', []):
  if i.get('type') == 'posts' and i['attributes']['number'] == 1:
    _id = i['id']
    posts[_id] = {'html': i['attributes']['contentHtml']}
for i in threads.get('data', []):
  if i.get('type') == 'discussions':
    thread_time_str = i['attributes']['startTime']
    thread_time = datetime.datetime.strptime(thread_time_str, '%Y-%m-%dT%H:%M:%S+00:00')
    thread_author_id = i['relationships']['startUser']['data']['id']
    thread_author = users.get(thread_author_id, {'name': 'unknown'})['name']
    post_txt_id = i['relationships']['startPost']['data']['id']
    post_txt = posts[post_txt_id]

    items.append({
      'title': i['attributes']['title'],
      'id': i['attributes']['slug'] + i['id'],
      'url': BASE_URL + 'd/' + i['id'],
      'date_published': thread_time.isoformat(),
      'author': { 'name': thread_author },
      'content_html': post_txt['html'],
    })


write_json_feed(items)

