#!/usr/bin/env python3
import os
import time
import subprocess
import json
import tempfile
import requests
import sys
import yaml
from mastodon import Mastodon
import html2text

def do_diff(ignore, prev, curr):
	_, prev_file = tempfile.mkstemp()
	with open(prev_file, 'w+t') as fp:
		fp.write(prev)

	_, curr_file = tempfile.mkstemp()
	with open(curr_file, 'w+t') as fp:
		fp.write(curr)

	diff = subprocess.run(['diff', '-Naur', prev_file, curr_file], capture_output=True, text=True).stdout
	for line in diff.split('\n'):
		line = line.strip()
		# skip first lines
		if line.startswith('+++') or line.startswith('---'):
			continue

		# is this line a change?
		if line.startswith('+') or line.startswith('-'):
			if len(line) == 1:
				# empty line, not meaningful
				continue
			
			# ignore tokens
			ignored = False
			for token in ignore:
				if token.lower() in line.lower():
					ignored = True
					break
				
			if not ignored:
				# this is a meaningful change
				return diff

	return None

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

config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.yml'

with open(config_file, "r") as stream:
	try:
		cfg = yaml.safe_load(stream)
	except yaml.YAMLError as exc:
		print(exc)
		quit()

# page to monitor
page_to_monitor = cfg['main']['page']
# output folder
output =  cfg['main']['output']
curr_state_file = os.path.join(output, 'state.json')
# github api to create gists
gists_page = 'https://api.github.com/gists'
# check every 'period' seconds
period = cfg['main']['period']
# get github personal access token
github_token = cfg['github']['token']
# status text
status_text = cfg['mastodon']['status']

mastodon = Mastodon(
    access_token = cfg['mastodon']['access_token'],
    api_base_url = cfg['mastodon']['api_base_url']
)

html_converter = html2text.HTML2Text()

print("web page monitor bot started for %s ...\n" % page_to_monitor)

try:
    os.makedirs(output)
except OSError:
    pass

# check if we have a saved state
try:
	with open (curr_state_file, 'rt') as fp:
		prev = json.load(fp)
	
	print("[%d] loaded state.json" % int(time.time()))
except:
	prev = None

# set request headers
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-control": "no-cache",
    "Pragma": "no-cache",
    "sec-ch-ua": "\"Google Chrome\";v=\"107\", \"Chromium\";v=\"107\", \"Not=A?Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "Upgrade-insecure-requests": "1"
}

while True:
	now = int(time.time())
	resp = requests.get(page_to_monitor, headers=headers)
	if resp.status_code != 200:
		# http error
		print("[%d] got response %d, trying again in %d seconds ..." % (now, resp.status_code, period))
	elif prev is None:
		# first iteration
		data = html_converter.handle(resp.text)
		# update current state.json time
		prev = {
			'time': now,
			'data': data,
			'diff': None
		}
		with open(curr_state_file, 'w+t') as fp:
			json.dump(prev, fp)
	else:
		data = html_converter.handle(resp.text)
		# compare to previous state
		diff = do_diff(cfg['main']['ignore'], prev['data'], data)
		if diff is not None:
			print("[%d] found differences!" % int(time.time()))
			# move current state.json to state.<timestamp>.json
			os.rename(curr_state_file, os.path.join(output, 'state.%d.json' % prev['time']))

			# save new state as state.json
			prev = {
				'data': data,
				'diff': diff,
				'time': now
			}
			with open(curr_state_file, 'w+t') as fp:
				json.dump(prev, fp)

			"""
			# create gist
			gist = do_gist(diff, github_token)
			
			if 'html_url' in gist:
				print("[%d] gist posted to %s" % (int(time.time()), gist['html_url']))
				# share on mastodon
				mastodon.toot('%s\n%s' % (status_text, gist['html_url']))
			else:
				print("[%d] could not create gist: %s" % (int(time.time()), gist))
			"""

			print(diff)
		else:
			print("[%d] same same ..." % now)
		
			# update current state.json time
			prev = {
				'time': now,
				'data': data,
				'diff': None
			}
			with open(curr_state_file, 'w+t') as fp:
				json.dump(prev, fp)


	time.sleep(period)