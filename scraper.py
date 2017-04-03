class Scraper():
	def __init__(self):
		self.api_key = os.environ.get('RIOT_API_KEY')
		self.client = MongoClient()
		self.db = self.client.ireliaDB
		self.playersCollection = self.db.playersCollection
		self.playersMatches = self.db.playersMatches
		self.matches = self.db.matches
		self.limits = [RateLimiter(5,5), RateLimiter(250, 600)]

		logging.basicConfig(filename = 'RiotScraper.log', level = logging.DEBUG)

	def _base_query(self, db_collection, url, item):
		data = db_collection.find_one( { item : {'$exists' : True } } )
		if not data:
			# r = requests.get('https://na.api.pvp.net/api/lol/na' + url, params = {'api_key':self.api_key})
			r = self._call_API(self, 'https://na.api.pvp.net/api/lol/na' + url)
			data = json.loads(r.content)
			data['lastUpdate'] = time()
			db_collection.insert_one(data)
		return data


	def _call_API(self, url):
		if all([limit.is_available for limit in self.limits]):
			r = requests.get(url, params = {'api_key' : self.api_key})
			for limit in self.limits:
				limit.request()
		else:
			logging.warning('Rate limit exceeded for Scraper class.  Last call: ' + url)
		return

	def scrape(self):