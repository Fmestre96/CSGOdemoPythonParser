import json
import urllib.parse
import requests
import logging

logger = logging.getLogger(__name__)

ALLOW_ERROR_URLS = [
    'faceit.com/data/v4/tournaments',
    'https://api.faceit.com/match/v2/match/'
]
RETRIES = 3

def urlAllowsErrors(url):
    for exc_url in ALLOW_ERROR_URLS:
        if exc_url in url:
            return True
    return False


        
def performRequestRequests(url, headers=None):
    i=0
    while(i<RETRIES):
        data = requests.get(url, headers=headers)
        res = data.content
        res_decoded = res.decode("utf-8","replace")
        status_code = str(data.status_code)
        #print("requesting " + url + " | status: " + str(data.status_code))
        if urlAllowsErrors(url) or (not str(status_code).startswith("5")):
            return json.loads(res_decoded)
        else:
            logger.warning("Invalid Response from faceit | " + url + " | " +  status_code)
            logger.warning(res_decoded)
        i+=1
    logger.error('Invalid response after retries')


class FaceitDatav1: 
    """The Data API for Faceit"""
    
    def __init__(self, api_token):

        self.api_token = api_token
        self.headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_token)
        }
        self.list_headers = ['accept: application/json', 'Authorization: Bearer {}'.format(self.api_token)]
        
    def performRequest(self, url):
        return performRequestRequests(url)

    def user_info(self):
        api_url = "https://api.faceit.com/auth/v1/resources/userinfo"
        res = self.performRequest(api_url)
        return res

    def user_details(self, playername):
        api_url = "https://api.faceit.com/users/v1/nicknames/{}".format(playername)
        res = self.performRequest(api_url)
        return res  

    def user_stats(self,playerid,size=20,page=0):
        api_url = "https://api.faceit.com/stats/api/v1/stats/time/users/{}/games/csgo?size={}&page={}".format(playerid,size,page)
        #res = json.loads(requests.get(api_url).content.decode('utf-8'))
        res = self.performRequest(api_url)
        return res
    
    def user_ranking(self, region, playerid):
        api_url = "https://api.faceit.com/ranking/v1/globalranking/csgo/{}/{}".format(region, playerid)
        #res = json.loads(requests.get(api_url).content.decode('utf-8'))
        res = self.performRequest(api_url)
        return res
    

    def match_details(self,matchid):
        api_url = "https://api.faceit.com/stats/v1/matches/{}".format(matchid)
        res = self.performRequest(api_url)
        return res           

    def hub_search(self,size=20,offset=0):
        api_url = "https://api.faceit.com/search/v1/hubs?game=csgo&joinableOnly=false&limit={}&offset={}&queue.open=true&sort=-activity".format(size,offset)
        res = self.performRequest(api_url)
        return res

    def player_hubs(self,playerid,size):
        api_url = "https://api.faceit.com/hubs/v1/user/{}/membership?limit={}&".format(playerid,size)
        res = self.performRequest(api_url)
        return res

    def player_tournaments(self,playerid,size):
        api_url = "https://api.faceit.com/core/v1/users/{}/tournaments/past?limit={}".format(playerid,size)
        res = self.performRequest(api_url)
        return res

    def player_championships(self,playerid,size):
        api_url = "https://api.faceit.com/championships/v1/membership/user/{}?limit={}".format(playerid,size)
        res = self.performRequest(api_url)
        return res

    def hub_info(self,hubid):
        api_url = "https://api.faceit.com/hubs/v1/hub/{}".format(hubid)
        res = self.performRequest(api_url)
        return res

    def tournament_info(self,tourneyid):
        api_url = "https://api.faceit.com/core/v1/tournaments/{}".format(tourneyid)
        res = self.performRequest(api_url)
        return res

    def championships_info(self,tourneyid):
        api_url = "https://api.faceit.com/championships/v1/championship/{}".format(tourneyid)
        res = self.performRequest(api_url)
        return res

    def matchmaking_info(self,tourneyid):
        api_url = "https://api.faceit.com/queue/v1/queue/matchmaking/{}".format(tourneyid)
        res = self.performRequest(api_url)
        return res

    def search(self,query):
        api_url = "https://api.faceit.com/search/v1?query={}".format(query) 
        res = self.performRequest(api_url)
        return res


class FaceitDatav2:
    """The Data API for Faceit"""
    
    def __init__(self, api_token):

        self.api_token = api_token
        self.headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_token)
        }
        self.list_headers = ['accept: application/json', 'Authorization: Bearer {}'.format(self.api_token)]

    def performRequest(self, url):
        return performRequestRequests(url)

    def match_details(self,matchid):
        api_url = "https://api.faceit.com/match/v2/match/{}".format(matchid)
        res = self.performRequest(api_url)
        return res         


class FaceitDatav4:
    """The Data API for Faceit"""
    
    def __init__(self, api_token):
        """Contructor

        Keyword arguments:
        api_token -- The api token used for the Faceit API (either client or server API types)
        """

        self.api_token = api_token
        self.base_url = "https://open.faceit.com/data/v4"

        self.headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_token)
        }
        self.list_headers = ['accept: application/json', 'Authorization: Bearer {}'.format(self.api_token)]


    def performRequest(self, url):
        return performRequestRequests(url, self.headers)

    # Championships

    def championship_details(self, championship_id=None, expanded=None):
        """Retrieve championship details

        championship_id -- The ID of the championship
        expanded -- List of entity names to expand in request, either "organizer" or "game"
        """

        if championship_id is None:
            print("The championship_id of championship_details() cannot be nothing!")
        else :
            api_url = "{}/championships/{}".format(self.base_url, championship_id)

            if expanded is not None:
                if expanded.lower() == "game":
                    api_url += "?expanded=game"
                elif expanded.lower() == "organizer":
                    api_url += "?expanded=organizer"

            res = self.performRequest(api_url)
            return res

    def championship_matches(self, championship_id=None, type_of_match="all", starting_item_position=0, return_items=20):
        """Championship match details

        Keyword arguments:
        championship_id -- The championship ID
        type_of_match -- Kind of matches to return. Can be all(default), upcoming, ongoing or past
        starting_item_position -- The starting item position (default 0)
        return_items -- The number of items to return (default 20)
        """

        if championship_id is None:
            print("The championship_id of championship_matches() cannot be nothing!")
        else:
            api_url = "{}/championships/{}/matches?type={}&offset={}&limit={}".format(
                self.base_url, championship_id, type_of_match, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def championship_subscriptions(self, championship_id=None, starting_item_position=0, return_items=10):
        """Retrieve all subscriptions of a championship

        Keyword arguments:
        championship_id -- The championship ID
        starting_item_position -- The starting item position (default 0)
        return_items -- The number of items to return (default 10)
        """

        if championship_id is None:
            print("The championship_id of championship_subscriptions() cannot be nothing!")
        else:
            api_url = "{}/championships/{}/subscriptions?offset={}&limit={}".format(
                self.base_url, championship_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Games

    def all_faceit_games(self, starting_item_position=0, return_items=20):
        """Retrieve details of all games on FACEIT

        Keyword arguments:
        starting_item_position -- The starting item position (default 0)
        return_items -- The number of items to return (default 20)
        """

        api_url = "{}/games?offset={}&limit={}".format(
            self.base_url, starting_item_position, return_items)

        res = self.performRequest(api_url)
        return res

    def game_details(self, game_id=None):
        """Retrieve game details

        Keyword arguments:
        game_id -- The id of the game
        """

        if game_id is None:
            print("You need to specify a game_id in game_details()!")
        else:
            api_url = "{}/games/{}".format(self.base_url, game_id)

            res = self.performRequest(api_url)
            return res

    def game_details_parent(self, game_id=None):
        """Retrieve the details of the parent game, if the game is region-specific.

        Keyword arguments:
        game_id -- The id of the game
        """

        if game_id is None:
            print("You need to specify a game_id in game_details_parent!")
        else:
            api_url = "{}/games/{}/parent".format(self.base_url, game_id)

            res = self.performRequest(api_url)
            return res

    # Hubs

    def hub_details(self, hub_id=None, game=None, organizer=None):
        #print("Hub, getting details: " + hub_id)
        """Retrieve hub details

        Keyword arguments:
        hub_id -- The id of the hub
        game -- An entity to expand in request (default is None, but can be True)
        organizer -- An entity to expand in request (default is None, but can be True)
        """

        if hub_id is None:
            print("You need to specify a hub ID in hub_details()!")
        else:
            api_url = "{}/hubs/{}".format(self.base_url, hub_id)
            if game is not None:
                if game is True:
                    api_url += "?expanded=game"
            if organizer is not None:
                if game is None:
                    if organizer is True:
                        api_url += "?expanded=organizer"
            
            #print(api_url)
            res = self.performRequest(api_url)

            return res


    def hub_matches(self, hub_id=None, type_of_match="all", starting_item_position=0, return_items=5):
        """Retrieve all matches of a hub

        Keyword arguments:
        hub_id -- The ID of the hub (required)
        type_of_match -- Kind of matches to return. Default is all, can be upcoming, ongoing, or past
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            hub_id = "74caad23-077b-4ef3-8b1d-c6a2254dfa75" # Default hub = FPL
            
        api_url = "{}/hubs/{}/matches?type={}&offset={}&limit={}".format(
            self.base_url, hub_id, type_of_match, starting_item_position, return_items)

        res = self.performRequest(api_url)
        return res

    def hub_members(self, hub_id=None, starting_item_position=0, return_items=20):
        """Retrieve all members of a hub

        Keyword arguments:
        hub_id -- The ID of the hub (required)
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id of hub_members() cannot be nothing!")
        else:
            api_url = "{}/hubs/{}/members?offset={}&limit={}".format(
                self.base_url, hub_id, starting_item_position, return_items)
            
            res = self.performRequest(api_url)
            return res

    def hub_roles(self, hub_id=None, starting_item_position=0, return_items=20):
        """Retrieve all roles members can have in a hub

        Keyword arguments:
        hub_id -- The ID of the hub
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id of hub_roles() cannot be nothing!")
        else:
            api_url = "{}/hubs/{}/roles?offset={}&limit={}".format(
                self.base_url, hub_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def hub_statistics(self, hub_id=None, starting_item_position=0, return_items=20):
        """Retrieves statistics of a hub

        Keyword arguments:
        hub_id -- The ID of the hub
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id of hub_statistics() cannot be nothing!")
        else:
            api_url = "{}/hubs/{}/stats?offset={}&limit={}".format(
                self.base_url, hub_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Leaderboards

    def championship_leaderboards(self, championship_id=None, starting_item_position=0, return_items=20):
        """Retrieves all leaderboards of a championship

        Keyword arguments:
        championship_id -- The ID of a championship
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if championship_id is None:
            print("The championship ID cannot be nothing!")
        else:
            api_url = "{}/leaderboards/championships/{}?offset={}&limit={}".format(
                self.base_url, championship_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def championship_group_ranking(self, championship_id=None, group=None, starting_item_position=0, return_items=20):
        """Retrieve group ranking of a championship

        Keyword arguments:
        championship_id -- The ID of a championship
        group -- A group of the championship
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if championship_id is None:
            print("The championship ID cannot be nothing!")
        else:
            if group is None:
                print("The group cannot be nothing!")
            else:
                api_url = "{}/leaderboards/championships/{}/groups/{}?offset={}&limit={}".format(
                    self.base_url, championship_id, group, starting_item_position, return_items)

                res = self.performRequest(api_url)
                return res

    def hub_leaderboards(self, hub_id=None, starting_item_position=0, return_items=20):
        """Retrieve all leaderboards of a hub

        Keyword arguments:
        hub_id -- The ID of the hub
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id cannot be nothing!")
        else:
            api_url = "{}/leaderboards/hubs/{}?offset={}&limit={}".format(
                self.base_url, hub_id, starting_item_position, return_items)
            res = self.performRequest(api_url)
            return res

    def hub_ranking(self, hub_id=None, starting_item_position=0, return_items=20):
        """Retrieve all time ranking of a hub

        Keyword arguments:
        hub_id -- The ID of the hub
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id cannot be nothing!")
        else:
            api_url = "{}/leaderboards/hubs/{}/general?offset={}&limit={}".format(
                self.base_url, hub_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def hub_season_ranking(self, hub_id=None, season=None, starting_item_position=0, return_items=20):
        """Retrieve seasonal ranking of a hub

        Keyword arguments:
        hub_id -- The ID of the hub
        season -- A season of the hub
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if hub_id is None:
            print("The hub_id cannot be nothing!")
        else:
            if season is None:
                print("The season cannot be nothing!")
            else:
                api_url = "{}/leaderboards/hubs/{}/seasons/{}?offset={}&limit={}".format(
                    self.base_url, hub_id, season, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def leaderboard_ranking(self, leaderboard_id=None, starting_item_position=0, return_items=20):
        """Retrieve ranking from a leaderboard id

        Keyword arguments:
        leaderboard_id -- The ID of the leaderboard
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if leaderboard_id is None:
            print("The leaderboard_id cannot be nothing!")
        else:
            api_url = "{}/leaderboards/{}?offset={}&limit={}".format(
                self.base_url, leaderboard_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Matches

    def match_details(self, match_id=None):
        """Retrieve match details

        Keyword arguments:
        match_id -- The ID of the match
        """

        if match_id is None:
            print("match_id cannot be nothing")
        else:
            api_url = "{}/matches/{}".format(self.base_url, match_id)

            res = self.performRequest(api_url)
            return res

    def match_stats(self, match_id=None):
        """Retrieve match details

        Keyword arguments:
        match_id -- The ID of the match
        """

        if match_id is None:
            print("match_id cannot be nothing")
        else:
            api_url = "{}/matches/{}/stats".format(self.base_url, match_id)
            res = self.performRequest(api_url)
            return res

    # Organizers

    def organizer_details(self, name_of_organizer=None, organizer_id=None):
        """Retrieve organizer details

        Keyword arguments:
        name_of_organizer -- The name of organizer (use either this or the the organizer_id)
        organizer_id -- The ID of the organizer (use either this or the name_of_organizer)
        """

        if name_of_organizer is None:
            if organizer_id is None:
                print(
                    "You cannot have the name_of_organizer or the organizer_id set to None! Please choose one!")
            else:
                api_url = "{}/organizers/{}".format(self.base_url,organizer_id)
                #res = requests.get(api_url, headers=self.headers)
                res = self.performRequest(api_url)
                return res

    def organizer_championships(self, organizer_id=None, starting_item_position=0, return_items=20):
        """Retrieve all championships of an organizer

        Keyword arguments:
        organizer_id -- The ID of the organizer
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if organizer_id is None:
            print("You cannot have organizer_id set to nothing!")
        else:
            api_url = "{}/organizers/{}/championships?offset={}&limit={}".format(
                self.base_url, organizer_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def organizer_games(self, organizer_id=None):
        """Retrieve all games an organizer is involved with.

        Keyword arguments:
        organizer_id -- The ID of the organizer
        """

        if organizer_id is None:
            print("You cannot have organizer_id set to nothing!")
        else:
            api_url = "{}/organizers/{}/games".format(
                self.base_url, organizer_id)

            res = self.performRequest(api_url)
            return res

    def organizer_hubs(self, organizer_id=None, starting_item_position=0, return_items=20):
        """Retrieve all hubs of an organizer

        Keyword arguments:
        organizer_id -- The ID of the organizer
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if organizer_id is None:
            print("You cannot have the organizer_id set to nothing!")
        else:
            api_url = "{}/organizers/{}/hubs?offset={}&limit={}".format(
                self.base_url, organizer_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def organizer_tournaments(self, organizer_id=None, type_of_tournament="upcoming", starting_item_position=0, return_items=20):
        """Retrieve all tournaments of an organizer

        Keyword arguments:
        organizer_id -- The ID of the organizer
        type_of_tournament -- Kind of tournament. Can be upcoming(default) or past
        starting_item_position -- The starting item position. Default is 0
        return_items -- The number of items to return. Default is 20
        """

        if organizer_id is None:
            print("You cannot have the organizer_id set to nothing!")
        else:
            api_url = "{}/organizers/{}/tournaments?type={}&offset={}&limit={}".format(
                self.base_url, organizer_id, type_of_tournament, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Players

    def player_details(self, nickname=None, game=None, game_player_id=None):
        """Retrieve player details

        Keyword arguments:
        nickname -- The nickname of the player of Faceit
        game -- A game on Faceit
        game_player_id -- The ID of a player on a game's platform
        """

        api_url = "{}/players".format(self.base_url)
        if nickname is not None:
            api_url += "?nickname={}".format(nickname)
        if game_player_id is not None:
            if nickname is not None:
                api_url += "&game_player_id={}".format(game_player_id)
            else:
                api_url += "?game_player_id={}".format(game_player_id)
        if game is not None:
            api_url += "&game={}".format(game)

       # print(api_url)
        res = self.performRequest(api_url)
        return res

    def player_id_details(self, player_id=None):
        """Retrieve player details

        Keyword arguments:
        player_id -- The ID of the player
        """

        if player_id is None:
            print("The player_id cannot be nothing!")
        else:
            api_url = "{}/players/{}".format(self.base_url, player_id)

            res = self.performRequest(api_url)
            return res

    def player_matches(self, player_id=None, game=None, from_timestamp=1325376000, to_timestamp=None, starting_item_position=0, return_items=20):
        """Retrieve all matches of a player

        Keyword arguments:
        player_id -- The ID of a player
        game -- A game on Faceit
        from_timestamp -- The timestamp (UNIX time) as a lower bound of the query. 1 month ago if not specified
        to_timestamp -- The timestamp (UNIX time) as a higher bound of the query. Current timestamp if not specified
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if player_id is None:
            print("The player_id cannot be nothing!")
        else:
            if game is None:
                print("The game cannot be nothing!")
            else:
                api_url = "{}/players/{}/history".format(self.base_url,player_id)
                api_url += "?game={}&offset={}&limit={}".format(
                        game, starting_item_position, return_items) 
                        
                if from_timestamp is not None:
                    api_url += "&from={}".format(from_timestamp)
                
                if to_timestamp is not None:
                    api_url += "&to={}".format(to_timestamp)
                    
                
                res = self.performRequest(api_url)
                return res

    def player_hubs(self, player_id=None, starting_item_position=0, return_items=20):
        """Retrieve all hubs of a player

        Keyword arguments:
        player_id -- The ID of a player
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if player_id is None:
            print("The player_id cannot be nothing!")
        else:
            api_url = "{}/players/{}/hubs?offset={}&limit={}".format(
                self.base_url, player_id, starting_item_position, return_items)
            
            #res = requests.get(api_url, headers=self.headers)
            res = self.performRequest(api_url)
            return res

    def player_stats(self, player_id=None, game_id='csgo'):
        """Retrieve the statistics of a player

        Keyword arguments:
        player_id -- The ID of a player
        game_id -- A game on Faceit
        """

        if player_id is None:
            print("The player_id cannot be nothing!")
        else:
            if game_id is None:
                print("The game_id cannot be nothing!")
            else:
                api_url = "{}/players/{}/stats/{}".format(
                    self.base_url, player_id, game_id)

                res = self.performRequest(api_url)
                return res

    def player_tournaments(self, player_id=None, starting_item_position=0, return_items=20):
        """Retrieve all hubs of a player

        Keyword arguments:
        player_id -- The ID of a player
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if player_id is None:
            print("The player_id cannot be nothing!")
        else:
            api_url = "{}/players/{}/tournaments?offset={}&limit={}".format(
                self.base_url, player_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Rankings

    def game_global_ranking(self, game_id=None, region=None, country=None, starting_item_position=0, return_items=20):
        """Retrieve global ranking of a game

        Keyword arguments:
        game_id -- The ID of a game (Required)
        region -- A region of a game (Required)
        country -- A country code (ISO 3166-1)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if game_id is None:
            print("The game_id cannot be nothing!")
        else:
            if region is None:
                print("The region cannot be nothing!")
            else:
                api_url = "{}/rankings/games/{}/regions/{}".format(
                    self.base_url, game_id, region)
                if country is not None:
                    api_url += "?country={}&offset={}&limit={}".format(
                        country, starting_item_position, return_items)
                else:
                    api_url += "?offset={}&limit={}".format(
                        starting_item_position, return_items)

                res = self.performRequest(api_url)
                return res

    def player_ranking_of_game(self, game_id=None, region=None, player_id=None, country=None, return_items=20):
        """Retrieve user position in the global ranking of a game

        Keyword arguments:
        game_id -- The ID of a game (required)
        region -- A region of a game (required)
        player_id -- The ID of a player (required)
        country -- A country code (ISO 3166-1)
        return_items -- The number of items to return (default is 20)
        """

        if game_id is None:
            print("The game_id cannot be nothing!")
        else:
            if region is None:
                print("The region cannot be nothing!")
            else:
                if player_id is None:
                    print("The player_id cannot be nothing!")
                else:
                    api_url = "{}/rankings/games/{}/regions/{}/players/{}".format(
                        self.base_url, game_id, region, player_id)

                    if country is not None:
                        api_url += "?country={}&limit={}".format(
                            country, return_items)
                    else:
                        api_url += "?limit={}".format(return_items)

                    res = self.performRequest(api_url)
                    if "errors" not in res.keys():
                        return res
                    else:
                        return None

    # Search

    def search_championships(self, name_of_championship=None, game=None, region=None, type_of_competition="all", starting_item_position=0, return_items=20):
        """Search for championships

        Keyword arguments:
        name_of_championship -- The name of a championship on Faceit (required)
        game -- A game on Faceit
        region -- A region of the game
        type_of_competition -- Kind of competitions to return (default is all, can be upcoming, ongoing, or past)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """
        if name_of_championship is None:
            print("The name of the championship cannot be nothing!")
        else:
            api_url = "{}/search/championships?name={}&type={}&offset={}&limit={}".format(self.base_url, urllib.parse.quote_plus(
                name_of_championship), type_of_competition, starting_item_position, return_items)

            if game is not None:
                api_url += "&game={}".format(game)
            elif region is not None:
                api_url += "&region={}".format(region)

            res = self.performRequest(api_url)
            return res

    def search_hubs(self, name_of_hub=None, game=None, region=None, starting_item_position=0, return_items=20):
        """Search for hubs

        Keyword arguments:
        name_of_hub -- The name of a hub on Faceit (required)
        game -- A game on Faceit
        region -- A region of the game
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if name_of_hub is None:
            print("The name_of_hub cannot be nothing!")
        else:
            api_url = "{}/search/hubs?name={}&offset={}&limit={}".format(
                self.base_url, urllib.parse.quote_plus(name_of_hub), starting_item_position, return_items)

            if game is not None:
                api_url += "&game={}".format(game)
            elif region is not None:
                api_url += "&region={}".format(region)

            res = self.performRequest(api_url)
            return res

    def search_organizers(self, name_of_organizer=None, starting_item_position=0, return_items=20):
        """Search for organizers

        Keyword arguments: 
        name_of_organizer -- The name of an organizer on Faceit
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if name_of_organizer is None:
            print("The name of the organizer cannot be nothing!")
        else:
            api_url = "{}/search/organizers?name={}&offset={}&limit={}".format(
                self.base_url, urllib.parse.quote_plus(name_of_organizer), starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    def search_players(self, nickname=None, game=None, country_code=None, starting_item_position=0, return_items=20):
        """Search for players

        Keyword arguments:
        nickname -- The nickname of a player on Faceit (required)
        game -- A game on Faceit
        country_code -- A country code (ISO 3166-1)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if nickname is None:
            print("The nickname cannot be nothing!")
        else:
            api_url = "{}/search/players?nickname={}&offset={}&limit={}".format(
                self.base_url, nickname, starting_item_position, return_items)

            if game is not None:
                api_url += "&game={}".format(urllib.parse.quote_plus(game))
            elif country_code is not None:
                api_url += "&country={}".format(country_code)

            res = self.performRequest(api_url)
            return res

    def search_teams(self, nickname=None, game=None, starting_item_position=0, return_items=20):
        """Search for teams

        Keyword arguments:
        nickname -- The nickname of a team on Faceit (required)
        game -- A game on Faceit
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if nickname is None:
            print("The nickname for search_teams() cannot be nothing!")
        else:
            api_url = "{}/search/teams?nickname={}&offset={}&limit={}".format(
                self.base_url, urllib.parse.quote_plus(nickname), starting_item_position, return_items)

            if game is not None:
                api_url += "&game={}".format(urllib.parse.quote_plus(game))

            res = self.performRequest(api_url)
            return res

    def search_tournaments(self, name_of_tournament=None, game=None, region=None, type_of_competition="all", starting_item_position=0, return_items=20):
        """Search for tournaments

        Keyword arguments:
        name_of_tournament -- The name of a tournament on Faceit (required)
        game -- A game on Faceit
        region -- A region of the game
        type_of_competition -- Kind of competitions to return (default is all, can be upcoming, ongoing, or past)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if name_of_tournament is None:
            print("The name_of_tournament for search_tournaments() cannot be nothing!")
        else:
            api_url = "{}/search/tournaments?name={}&type={}&offset={}&limit={}".format(self.base_url, urllib.parse.quote_plus(
                name_of_tournament), type_of_competition, starting_item_position, return_items)

            if game is not None:
                api_url += "&game={}".format(urllib.parse.quote_plus(game))
            elif region is not None:
                api_url += "&region={}".format(region)

            res = self.performRequest(api_url)
            return res

    # Teams

    def team_details(self, team_id=None):
        """Retrieve team details

        Keyword arguments:
        team_id -- The ID of the team (required)
        """

        if team_id is None:
            print("The team_id of team_details() cannot be None!")
        else:
            api_url = "{}/teams/{}".format(self.base_url, team_id)

            res = self.performRequest(api_url)
            return res

    def team_stats(self, team_id=None, game_id=None):
        """Retrieve statistics of a team

        Keyword arguments:
        team_id -- The ID of a team (required)
        game_id -- A game on Faceit (required)
        """

        if team_id is None:
            print("The team_id of team_stats() cannot be nothing!")
        elif game_id is None:
            print("The game_id of team_stats() cannot be nothing")
        else:
            api_url = "{}/teams/{}/stats/{}".format(
                self.base_url, team_id, urllib.parse.quote_plus(game_id))

            res = self.performRequest(api_url)
            return res

    def team_tournaments(self, team_id=None, starting_item_position=0, return_items=20):
        """Retrieve tournaments of a team

        Keyword arguments:
        team_id -- The ID of a team (required)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if team_id is None:
            print("The team_id of team_tournaments() cannot be nothing!")
        else:
            api_url = "{}/teams/{}/tournaments?offset={}&limit={}".format(
                self.base_url, team_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res

    # Tournaments

    def all_tournaments(self, game=None, region=None, type_of_tournament="upcoming", starting_item_position=0, return_items=20):
        """Retrieve all tournaments

        Keyword arguments:
        game -- A game on Faceit
        region -- A region of the game
        type_of_tournament -- Kind of tournament. Can be upcoming(default) or past
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        api_url = "{}/tournaments?type={}".format(
            self.base_url, type_of_tournament)

        if game is not None:
            api_url += "&game={}".format(urllib.parse.quote_plus(game))
        elif region is not None:
            api_url += "&region={}".format(region)

        res = self.performRequest(api_url)
        return res
    
    def tournament_details(self, tournament_id=None, expanded=None):
        """Retrieve tournament details

        Keyword arguments:
        tournament_id -- The ID of the tournament (required)
        expanded -- List of entity names to expand in request, either "organizer" or "game"
        """

        if tournament_id == None:
            print("The tournament_id of tournament_details() cannot be nothing!")
        else:
            api_url = "{}/tournaments/{}".format(self.base_url, tournament_id)
            if expanded != None:
                if expanded.lower() == "organizer":
                    api_url += "?expanded=organizer"
                elif expanded.lower() == "game":
                    api_url += "?expanded=game"
            
            res = self.performRequest(api_url)
            return res
    
    def tournament_brackets(self, tournament_id=None):
        """Retrieve brackets of a tournament
        
        Keyword arguments:
        tournament_id -- The ID of the tournament (required)
        """

        if tournament_id is None:
            print("The tournament_id of tournament_brackets() cannot be nothing!")
        else:
            api_url = "{}/tournaments/{}/brackets".format(self.base_url, tournament_id)

            res = self.performRequest(api_url)
            return res
    
    def tournament_matches(self, tournament_id=None, starting_item_position=0, return_items=20):
        """Retrieve all matches of a tournament

        Keyword arguments:
        tournament_id -- The ID of a tournament (required)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if tournament_id is None:
            print("The tournament_id of tournament_matches() cannot be nothing!")
        else:
            api_url = "{}/tournaments/{}/matches?offset={}&limit={}".format(self.base_url, tournament_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res
    
    def tournament_teams(self, tournament_id=None, starting_item_position=0, return_items=20):
        """Retrieve all teams of a tournament

        Keyword arguments:
        tournament_id -- The ID of a tournament (required)
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if tournament_id is None:
            print("The tournament_id of tournament_teams() cannot be nothing!")
        else:
            api_url = "{}/tournaments/{}/teams?offset={}&limit={}".format(self.base_url, tournament_id, starting_item_position, return_items)

            res = self.performRequest(api_url)
            return res


class FaceitDatav5:

    def __init__(self, api_token):
        """Contructor

        Keyword arguments:
        api_token -- The api token used for the Faceit API (either client or server API types)
        """

        self.api_token = api_token
        self.base_url = "https://open.faceit.com/data/v5"

        self.headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_token)
        }
        self.list_headers = ['accept: application/json', 'Authorization: Bearer {}'.format(self.api_token)]

    def performRequest(self, url):
        return performRequestRequests(url, self.headers)

    def player_matches(self, player_id=None, from_timestamp=None, to_timestamp=None, page=0, return_items=20):
        """Retrieve all matches of a player

        Keyword arguments:
        player_id -- The ID of a player
        game -- A game on Faceit
        from_timestamp -- The timestamp (UNIX time) as a lower bound of the query. 1 month ago if not specified
        to_timestamp -- The timestamp (UNIX time) as a higher bound of the query. Current timestamp if not specified
        starting_item_position -- The starting item position (Default is 0)
        return_items -- The number of items to return (Default is 20)
        """

        if player_id == None:
            print("The player_id cannot be nothing!")
        else:
            api_url = "https://api.faceit.com/match-history/v5/players/{}/history/".format(player_id)
            api_url += "?page={}&size={}".format(page,return_items) 
                    
            if from_timestamp is not None:
                api_url += "&from={}".format(from_timestamp)
            
            if to_timestamp is not None:
                api_url += "&to={}".format(to_timestamp)
                
            #res = requests.get(api_url, headers=self.headers)
            res = self.performRequest(api_url)
            return res



#https://api.faceit.com/stats/v1/stats/configuration/csgo

#i0:  region
#i1:  map
#i2:  some id 
#i3:  FIRST HALF SCORE
#i4:  SECOND HALF SCORE
#i5:  team name
#i6:  kills
#i7:  assists
#i8:  deaths
#i9:  mvps 
#i10: win
#i11: XXXXXXXXXXXXX - DNE
#i12: number of rounds
#i13: headshots
#i14: triple kills 
#i15: quadra kills 
#i16: aces
#i17: XXXXXXXXXXXXX - DNE  (teamWin)
#i18: final score
#i19: if overtime, how many round wins above 15

#c1 = status ? 
#c2 = kdr
#c3 = kpr
#c4 = hs%
#c5 = round wins