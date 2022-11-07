#!/usr/bin/env python3
import os
import time
import subprocess
import json
import tempfile
import tweepy
import requests

def do_diff(prev, curr):
	_, prev_file = tempfile.mkstemp()
	with open(prev_file, 'w+t') as fp:
		fp.write(prev)

	_, curr_file = tempfile.mkstemp()
	with open(curr_file, 'w+t') as fp:
		fp.write(curr)

	return subprocess.run(['diff', '-Naur', prev_file, curr_file], capture_output=True, text=True).stdout

def do_gist(data, token):
	headers={
		'Authorization':'token %s' % token
	}
	params={'scope':'gist'}
	payload={
		"description": "Twitter ToS change",
		"public": True,
		"files": {'twitter_tos.patch': {'content': data}}}

	res = requests.post( gists_page, headers=headers, params=params, data=json.dumps(payload) )
	return res.json()

# get API authentication data via environment variables
consumer_key = os.getenv('TOSBOT_CONSUMER_KEY')
consumer_secret = os.getenv('TOSBOT_CONSUMER_SECRET')
access_token = os.getenv('TOSBOT_ACCESS_TOKEN')
access_token_secret = os.getenv('TOSBOT_ACCESS_TOKEN_SECRET')
# get github personal access token
github_token = os.getenv('TOSBOT_GITHUB_TOKEN')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
auth.set_access_token(access_token, access_token_secret) 
api = tweepy.API(auth)

# github api to create gists
gists_page = 'https://api.github.com/gists'
# twitter tos page to monitor
tos_page = 'https://twitter.com/en/tos'
# check every 'period' seconds
period = 30
# tweet text
status_text = 'Detected Twitter ToS changes.'

print("Twitter Terms of Service monitor bot.\n")

# check if we have a saved state
try:
	with open ('state.json', 'rt') as fp:
		prev = json.load(fp)
	
	print("[%d] loaded state.json" % int(time.time()))
except:
	prev = None

while True:
	now = int(time.time())
	resp = requests.get(tos_page)
	if resp.status_code != 200:
		print("[%d] got response %d, trying again in %d seconds ..." % (now, resp.status_code, period))

	else:
		data = resp.text
		# compare to previous state if this is not the first iteration
		if prev is not None and data != prev['data']:
			print("[%d] found differences!" % int(time.time()))
			# generate diff
			diff = do_diff(prev['data'], data)
			# create gist
			gist = do_gist(diff, github_token)
			
			if 'html_url' in gist:
				print("[%d] gist posted to %s" % (int(time.time()), gist['html_url']))
				# tweet
				api.update_status( status = '%s\n%s' % (status_text, gist['html_url']) )
				print("[%d] tweeted!" % int(time.time()))
			else:
				print("[%d] could not create gist: %s" % (int(time.time()), gist))
		else:
			print("[%d] same same ..." % now)
		
		# set previous state and save
		prev = {
			'time': now,
			'data': data
		}
		with open('state.json', 'w+t') as fp:
			json.dump(prev, fp)

	time.sleep(period)