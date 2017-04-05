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
		'''
		requestLimit: the number of requests that we're limited to seeing over a window of size timeLimit
		'''
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
		Availability check.  First clear everything from the queue that is older than the current window, then check to see if the number of requests we've seen in this window is smaller than the number of requests we're allowed.  
		'''
		self._clean_queue()
		return len(self.rQueue) < self.requestLimit

	def request(self):
		self.rQueue.append(time())


class RiotAPI:

	def __init__(self):
		'''
		Some parameters worth mentioning

		client: The MongoDB client 
		db: The name of the database within MongoDB.  I call it "ireliaDB"
		playersCollection, playersMatches, matches: three collections (analogous to tables) with ireliaDB
		updateFrequency: time period to decide when stale data gets updated
		limits: instances of the RateLimiter class, which limit the number of API calls we can make
		'''
		self.api_key = os.environ.get('RIOT_API_KEY')
		self.client = MongoClient()
		self.db = self.client.ireliaDB
		self.playersCollection = self.db.playersCollection
		self.playersMatches = self.db.playersMatches
		self.matches = self.db.matches
		self.updateFrequency = 36000000
		self.limits = [RateLimiter(5,5), RateLimiter(250, 600)]

		logging.basicConfig(filename = 'RiotAPI.log', level = logging.DEBUG)

	def _base_query_multi(self, db_collection, url_left, url_right, items):
		'''
		Base query for our API, for the external API calls that allow 
		comma-separated lists of queries.  

		Input: 


		db_collection : MongoClient.db.collection
		the collection (analogous to a SQL table) that we're reading and 
		writing to for this query

		url_left, url_right : str, str

		the url of the external API that we need to make a GET request to.  
		The left and right sides of this are because the variable part of the 
		URL that we're getting the data from may occur in the middle of the 
		URL, e.g. /championmastery/location/na/player/{playerid}/champions.  
		Here url_left is everything before {playerid} and url_right is 
		everything after.  NB: There are more sophisticated ways of doing this

		items : List[str]

		A list of items that the query wants to get (up to 40), e.g. info for 
		a list of 40 different usernames.  Some calls to the external Riot API 
		permit comma-separated lists to retrieve multiple values at once; I 
		replicate this functionality but allowing the items here to be a 
		list.  


		Output:

		data: List[json objects]

		A list of the requested data.  
		'''
		dbUpdate = []

		call_items, data = self._get_call_items(db_collection, items)
		url_variable = ','.join(call_items)
		if url_variable:
			r = self._call_API('https://na.api.pvp.net/api/lol/na' + url_left + url_variable + url_right)
			call_data = json.loads(r.content)
			t = time()
			for d in call_data:
				# slight change to the json to keep track of when we last called the external API for this data
				x = {'info': call_data[d], 'lastUpdate': t}
				data.append( {d:x} )
				dbUpdate.append({d:x})
			db_collection.insert(dbUpdate)
		return data

	def _base_query_single(self, db_collection, url_left, url_right, item):
		'''
		Base query for our API, for the external API calls that only allow a 
		single value

		Input: 


		db_collection : MongoClient.db.collection
		the collection (analogous to a SQL table) that we're reading and 
		writing to for this query

		url_left, url_right : str, str

		the url of the external API that we need to make a GET request to.  
		The left and right sides of this are because the variable part of the 
		URL that we're getting the data from may occur in the middle of the 
		URL, e.g. /championmastery/location/na/player/{playerid}/champions.  
		Here url_left is everything before {playerid} and url_right is 
		everything after.  NB: There are more sophisticated ways of doing this

		item : str

		An item that the query wants to get, e.g. info about a match with a 
		given id.  Most calls to the external Riot API only permit a single 
		input; this function handles those cases.
		'''
		call_item, data = self._get_call_item_single(db_collection, item)
		if call_item:
			r = self._call_API('https://na.api.pvp.net/api/lol/na' + url_left + item + url_right)
			call_data = json.loads(r.content)
			t = time()
			x = {'info': call_data, 'lastUpdate': t}
			data = {item : x}
			db_collection.insert(data)
		return data

	def _get_call_items(self, db_collection, items):
		'''
		Given a list of multiple pieces of data the user wants, some of these 
		may already exist in the DB and some may not.  This function sorts the 
		incoming requests into three categories: data not in the DB, data that 
		is in the DB but determined to be stale, and data that is in the DB 
		and determined to not be stale.  The former two categories are 
		returned to the base query to become an API call, while the latter is 
		just returned as data.  

		Input:


		db_collection : MongoClient.db.collection
		the collection (analogous to a SQL table) that we're reading and writing to for this query

		items : List[str]

		A list of items that the query wants to get (up to 40), e.g. info for 
		a list of 40 different usernames.  Some calls to the external Riot API 
		permit comma-separated lists to retrieve multiple values at once; I 
		replicate this functionality but allowing the items here to be a 
		list.  


		Output: 

		call_items : List[str]

		A list of strings corresponding to data that does not exist in the DB  
		(or does exist and is stale) and needs to be handed off to the 
		external API.

		data : List[json objects]

		A list of json objects corresponding to data that does exist in the DB 
		and isn't stale.
		'''
		data = []
		call_items = []
		for item in items:
			db_item = db_collection.find_one( { item : {'$exists' : True } } )
			# if the requested data isn't in the db, add it to list of things we need to make api calls for
			if not db_item: 
				call_items.append(item)
			# if it's in the db but the data is stale, add it to the call list and remove it from the db
			elif db_item and time() - db_item[item]['lastUpdate'] >= self.updateFrequency:
				db_collection.remove({'_id': db_item['_id']})
				call_items.append(item)
			else:
			# if it's in the db, add it to the return list
				data.append(db_item)
		return call_items, data

	def _get_call_item_single(self, db_collection, item):
		'''
		Analogous to _get_call_items, but for only one item, which simplifies 
		the task considerably.  Given a request for data, this may already 
		exist in the DB or it may not.  This function places the incoming 
		request into one of three categories: data not in the DB, data that is 
		in the DB but determined to be stale, and data that is in the DB and 
		determined to not be stale.  The former two categories are returned to 
		the base query to become an API call, while the latter is just 
		returned as data.  

		Input:


		db_collection : MongoClient.db.collection
		the collection (analogous to a SQL table) that we're reading and 
		writing to for this query

		item : str

		An item that the query wants to get, e.g. info about a match with a 
		given id.  Most calls to the external Riot API only permit a single 
		input; this function handles those cases.


		Output: 

		NB: Only one return value for this function will be meaningful for any 
		particular call.  This makes the code structure parallel to the 
		multiple-query case at the cost of being much less intuitive in the 
		single-query case.  Given more time, this is something that I'd work 
		on.

		call_item : str

		A string corresponding to data that does not exist in the DB  (or does 
		exist and is stale) and needs to be handed off to the external API.

		data : json object

		A json object corresponding to data that does exist in the DB and 
		isn't stale.
		'''
		call_item, data = 0, 0
		db_item = db_collection.find_one( { item : {'$exists': True } } )
		# if the requested data isn't in the db, add it to list of things we 
		# need to make api calls for
		if not db_item:
			call_item = item
		# if it's in the db but the data is stale, add it to the call list and 
		# remove it from the db
		elif db_item and time() - db_item[item]['lastUpdate'] >= self.updateFrequency:
			db_collection.remove({'_id': db_item['_id']})
			call_item = item
		# if it's in the db, add it to the return list
		else:
			data = db_item
		return call_item, data


	def _call_API(self, url):
		'''
		Calls the API if we're not rate-limited.  
		'''
		if all([limit.is_available for limit in self.limits]):
			r = requests.get(url, params = {'api_key' : self.api_key})
			for limit in self.limits:
				limit.request()
		else:
			logging.warning('Rate limit exceeded for RiotAPI class.  Last call: ' + url)
		return r


	def get_player_info(self, players):
		'''
		Given a list of player names, returns a json object containing player 
		info

		input: 
		List[str: Player Name]

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
		return self._base_query_multi(db_collection, url_left, url_right, players)


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
		url_left = '/v2.2/match/'
		url_right = ''
		return self._base_query_single(db_collection, url_left, url_right, matchid)

	def get_matchlist(self, playerid):
		'''
		Given a player id, returns a json object containing all the matches 
		they've played
		'''
		db_collection = self.playersMatches
		url_left = '/v2.2/matchlist/by-summoner/'
		url_right = ''
		return self._base_query_single(db_collection, url_left, url_right, playerid)

	def get_matchlist_by_name(self, player):
		player_info = self.get_player_info(player)
		return self.get_matchlist(str(player_info[0][player[0]]['info']['id']))

	def get_all_matches_by_name(self,player):
		'''
		TODO: figure out rate throttling to make this work nicely with API 
		tokens
		'''
		player_info = self.get_player_info([player])
		player_id = player_info[0][player]['info']['id']
		match_list = self.get_matchlist(str(player_id))
		return [self.get_match(str(match['matchId'])) for match in match_list[str(player_id)]['info']['matches']]