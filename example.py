from api import *

def main():
    x = RiotAPI()
    y = x.get_player_info(['liquidpiglet','doublelift','intamaterasu','everyonesma'])
    pprint.pprint(y)
    z = x.get_matchlist_by_name(['doublelift'])
    pprint.pprint(z)

if __name__=='__main__':
    main()