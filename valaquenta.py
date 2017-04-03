import os
import requests
from pymongo import MongoClient
import pprint
import json
from time import time

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

	def base_query(self, db_collection, url, item):
		data = db_collection.find_one( { item : {'$exists' : True } } )
		if data:
			return data
		else:
			r = requests.get('https://na.api.pvp.net/api/lol/na' + url, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			db_collection.insert_one(data)
			return data

	def get_player_info_r(self,player):
		'''
		Given a player name, returns a json object containing player info

		input: 
		player name 

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
		url = '/v1.4/summoner/by-name/' + player
		return self.base_query(db_collection, url, player)

	def get_player_info(self, player):
		'''
		Given a player name, returns a json object containing player info

		input: 
		player name 

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
		data = self.playersCollection.find_one( { player : {'$exists' : True} } )
		if data and time() - data['lastUpdate'] < self.updateFrequency: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/' + player
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			self.playersCollection.insert_one(data)
			return data
	
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
		data = self.playersCollection.find_one( { playerid : {'$exists' : True} } )
		if data and time() - data['lastUpdate'] < self.updateFrequency: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/' + playerid
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			self.playersCollection.insert_one(data)
			return data

	# def get_match(self, matchid):
	# 	data = self.

	def get_matchlist(self, playerid):
		data = self.playersMatches.find_one( { playerid : {'$exists' : True} } )
		if data and time() - data['lastUpdate'] < self.updateFrequency: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/' + playerid
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			# self.playersMatches.insert_one(data)
			return data

	def get_matchlist_by_name(self, player):
		player_info = self.get_player_info(player)
		return self.get_matchlist(str(player_info[player]['id']))

x = RiotAPI()
y = x.get_player_info('liquidpiglet')
# z = x.get_matchlist_name('everyonesma')
pprint.pprint(y)

z = x.get_player_info_r('chillbros')
pprint.pprint(z)
# pprint.pprint(z)

# class Scraper:
# 	def __init__(self, key):
# 		self.api_key = key
