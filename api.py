import os
import requests
import pprint
import json
import logging

from pymongo import MongoClient
from time import time
from collections import deque


class RateLimiter:
	'''
	As we have a limited number of API tokens, we want to call the API only if the rate limit is not being exceeded.  This class maintains a queue of call timestamps so that we can detect if we're going over a specified limit.
	'''
	def __init__(self, requestLimit, timeLimit):
		self.requestLimit = requestLimit
		self.timeLimit = timeLimit
		self.rQueue = deque()

	def _clean_queue(self):
		'''
		Pops from the timestamp queue until everything further from the current time the imposed time limit is removed.  For internal use only.
		'''
		t = time()
		while len(self.rQueue) > 0 and self.rQueue[0] < t - self.timeLimit:
			rQueue.popleft()

	def is_available(self):
		'''
		Availability check.  First clear everything from the queue that is older than the current window, then check to see if the number of requests we've seen in this window is smaller than the number of requests were allowed.  
		'''
		self._clean_queue()
		return len(self.rQueue) < self.requestLimit

	def request(self):
		self.rQueue.append(time())


class RiotAPI:
	'''
	End user API. 
	'''
	def __init__(self):
		self.api_key = os.environ.get('RIOT_API_KEY')
		self.client = MongoClient()
		self.db = self.client.ireliaDB
		self.playersCollection = self.db.playersCollection
		self.playersMatches = self.db.playersMatches
		self.matches = self.db.matches
		self.updateFrequency = 36000000
		self.limits = [RateLimiter(5,5), RateLimiter(250, 600)]

		logging.basicConfig(filename = 'RiotAPI.log', level = logging.DEBUG)

	def _base_query_old(self, db_collection, url, items):
		data = db_collection.find_one( { item : {'$exists' : True } } )
		if not data or time() - data['lastUpdate'] >= self.updateFrequency:
			r = self._call_API(self, 'https://na.api.pvp.net/api/lol/na' + url)
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			db_collection.insert_one(data)
		return data


	def _base_query(self, db_collection, url_left, url_right, items):
		data = []
		call_items = []
		dbUpdate = []

		for item in items:
			db_item = db_collection.find_one( { item : {'$exists' : True } } )
			# print(db_item['_id'])
			if not db_item:
				call_items.append(item)
			elif db_item and time() - db_item[item]['lastUpdate'] >= self.updateFrequency:
				db_collection.remove({'_id': db_item['_id']})
				call_items.append(item)
			else:
				data.append(db_item)
		url_variable = ','.join(call_items)
		if url_variable:
			r = self._call_API('https://na.api.pvp.net/api/lol/na' + url_left + url_variable + url_right)
			call_data = json.loads(r.content)
			t = time()
			for d in call_data:
				x = {'info': call_data[d], 'lastUpdate': t}
				data.append({d:x})
				dbUpdate.append({d:x})
			db_collection.insert(dbUpdate)
		return data


	def _call_API(self, url):
		if all([limit.is_available for limit in self.limits]):
			r = requests.get(url, params = {'api_key' : self.api_key})
			for limit in self.limits:
				limit.request()
		else:
			logging.warning('Rate limit exceeded for RiotAPI class.  Last call: ' + url)
		return r


	def get_player_info(self, players):
		'''
		Given a list of player names, returns a json object containing player info

		input: 
		List[Player Name]

		output:
		List[
		{ player name :
			{
			id
			name
			profileIconId
			revisionDate
			summonerLevel
			}
		}
		]
		'''
		db_collection = self.playersCollection
		url_left = '/v1.4/summoner/by-name/'
		url_right = ''
		return self._base_query(db_collection, url_left, url_right, players)


	def get_player_info_id(self, playerid):
		'''
		Given a player id, returns a json object containing player info

		input: 
		player id

		output:
		{ player name :
			{
			id
			name
			profileIconId
			revisionDate
			summonerLevel
			}
		}
		'''
		db_collection = self.playersCollection
		url = '/v1.4/summoner/' + playerid
		return self.base_query(db_collection, url, playerid)

	def get_match(self, matchid):
		'''
		Given a match id, returns a json object containing match info
		'''
		db_collection = self.matches
		url = '/v2.2/match/' + matchid
		return self.base_query(db_collection, url, playerid)

	def get_matchlist(self, playerid):
		'''
		Given a player id, returns a json object containing all the matches they've played
		'''
		db_collection = self.playersMatches
		url = '/v2.2/matchlist/by-summoner/' + playerid
		return self.base_query(db_collection, url, playerid)

	def get_matchlist_by_name(self, player):
		player_info = self.get_player_info(player)
		return self.get_matchlist(str(player_info[player]['id']))
