import subprocess
import tempfile
import requests
import time
import json
import os

def request_page(page):
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
	return requests.get(page, headers=headers)

def load_state(filename):
	try:
		with open(filename, 'rt') as fp:
			state = json.load(fp)
		
		print("[%d] loaded state.json" % int(time.time()))
	except:
		state = None

	return state

def save_state(filename, data, diff = None):
	state = {
		'time': int(time.time()),
		'data': data,
		'diff': diff
	}

	with open(filename, 'w+t') as fp:
		json.dump(state, fp)

	return state

def is_meaningful_diff(ignore, diff):
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
				# print("MEANINGFUL '%s'" % line)
				# this is a meaningful change
				return True

		return False

def do_diff(ignore, prev, curr):
	fd, prev_file = tempfile.mkstemp()
	with os.fdopen(fd, 'w') as tmp:
		tmp.write(prev)

	fd, curr_file = tempfile.mkstemp()
	with os.fdopen(fd, 'w') as tmp:
		tmp.write(curr)

	diff = subprocess.run(['diff', '-Naur', prev_file, curr_file], capture_output=True, text=True).stdout

	os.remove(prev_file)
	os.remove(curr_file)

	return diff if is_meaningful_diff(ignore, diff) else None