#!/usr/bin/env python3
import os
import time
import json
import sys
import yaml
import html2text

import monitor
import bot

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

# check every 'period' seconds
period = cfg['main']['period']
# get github personal access token
github_token = cfg['github']['token']
# status text
status_text = cfg['mastodon']['status']
# used to clean the html response into something less false positives prone when diffing
html_converter = html2text.HTML2Text()

print("web page monitor bot started for %s ...\n" % page_to_monitor)

try:
    os.makedirs(output)
except OSError:
    pass

# check if we have a saved state
prev = monitor.load_state(curr_state_file)

while True:
	resp = monitor.request_page(page_to_monitor)
	if resp.status_code != 200:
		# http error
		print("[%d] got response %d, trying again in %d seconds ..." % (int(time.time()), resp.status_code, period))
	elif prev is None:
		# first iteration
		data = html_converter.handle(resp.text)
		# update current state.json time
		prev = monitor.save_state(curr_state_file, data)
	else:
		data = html_converter.handle(resp.text)
		# compare to previous state
		diff = monitor.do_diff(cfg['main']['ignore'], prev['data'], data)
		if diff is not None:
			print("[%d] found differences:" % int(time.time()))
			print(diff)

			# move current state.json to state.<timestamp>.json
			os.rename(curr_state_file, os.path.join(output, 'state.%d.json' % prev['time']))

			# save new state as state.json
			prev = monitor.save_state(curr_state_file, data, diff)

			if 'dry_run' not in cfg['main'] or not cfg['main']['dry_run']:
				# create gist
				gist = bot.create_gist(diff, github_token)
				if 'html_url' in gist:
					print("[%d] gist posted to %s" % (int(time.time()), gist['html_url']))
					# share on mastodon
					bot.status_update(cfg['mastodon'], '%s\n%s' % (status_text, gist['html_url']))
				else:
					print("[%d] could not create gist: %s" % (int(time.time()), gist))
			else:
				print("dry run")

		else:
			# print("[%d] same same ..." % int(time.time()))
			# update current state.json time
			prev = monitor.save_state(curr_state_file, data)

	time.sleep(period)