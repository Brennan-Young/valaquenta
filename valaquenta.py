import os
import requests
from pymongo import MongoClient
import pprint
import json


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

	def base_query(self, db_path, api_path, item):
		data = db_path.find_one( { item : {'$exists' : True } } )
		if data:
			return data
		else:
			r = requests.get(api_path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			db_path.insert_one(data)
			return data

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
		if data: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/' + player
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
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
		if data: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-account/' + playerid
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			self.playersCollection.insert_one(data)
			return data

	# def get_match(self, matchid):
	# 	data = self.

	def get_matchlist(self, playerid):
		data = self.playersMatches.find_one( { playerid : {'$exists' : True} } )
		if data: # if player is in DB
			return data
		else:
			path = 'https://na.api.pvp.net/api/lol/na/v2.2/matchlist/by-summoner/' + playerid
			r = requests.get(path, params = {'api_key':self.api_key})
			data = json.loads(r.content)
			# self.playersMatches.insert_one(data)
			return data

	def get_matchlist_by_name(self, player):
		player_info = self.get_player_info(player)
		return self.get_matchlist(str(player_info[player]['id']))

x = RiotAPI()
# y = x.get_player_info('liquidpiglet')
z = x.get_matchlist_name('everyonesma')
# pprint.pprint(y)
pprint.pprint(z)

# class Scraper:
# 	def __init__(self, key):
# 		self.api_key = key
