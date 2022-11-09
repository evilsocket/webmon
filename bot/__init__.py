import requests
import json
from mastodon import Mastodon

def create_gist(data, token):
	# github api to create gists
	gists_page = 'https://api.github.com/gists'
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

mastodon = None

def status_update(cfg, message):
	global mastodon	

	if mastodon is None:
		mastodon = Mastodon(
			access_token = cfg['access_token'],
			api_base_url = cfg['api_base_url']
		)

	mastodon.toot(message)
