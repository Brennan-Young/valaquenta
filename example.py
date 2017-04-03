from api import *

def main():
	x = RiotAPI()
	y = x.get_player_info('liquidpiglet')
	pprint.pprint(y)

if __name__=='__main__':
	main()