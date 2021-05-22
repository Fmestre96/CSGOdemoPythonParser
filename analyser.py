import DemoParserCSGO.DemoParser as dp
import DemoParserCSGO.PrintStuff as hf

verbose = True
def printVerbose(s):
    if verbose:
        print(s)

class Demo:
    def __init__(self,path):
        self.parser = None
        self.path = path
        self.map = ""
        self.service = "MM"
        self.match_started = False
        self.match_paused = False
        self.match_ended = False
        self.round_current = 1
        self.max_players = 10
        self.tickrate = 0
        self.current_tick = 0
        self.round_start_tick = 0
        self.round_timer = 0
        self.max_round_time = 115
        self.player_stats = dict()
        self.round_stats = dict()
        self.all_chat = []


    def save_to_file(self, ignoreData=None):
        hf.saveJson(self.get_stats())

    def get_stats(self):
        #Convert SegmentStats into dics so I can __dict__ later
        for p, ps in self.player_stats.items():
            self.player_stats[p].round_stats = {r: rs.__dict__ for r, rs in ps.round_stats.items()}

        stats = {
            'file_info': {
                'path': self.path,
            },
            'demo_info': {
                'service': self.service,
                'map': self.map,
                'tickrate': self.tickrate,
            },
            'match_stats': {
                'rounds': self.round_current,
            },
            'round_stats':{

            },
            'player_stats': {
                v.name: v.toDict() for v in self.player_stats.values()
            },
            'all_chat': self.all_chat,
        }
        return stats


    def analyze(self):
        file = open(self.path, "rb")
        self.parser = dp.DemoParser(file, ent="NONE")

        #Demo Start, Finnish
        self.parser.subscribe_to_event("parser_start", self.demo_started)
        self.parser.subscribe_to_event("cmd_dem_stop", self.demo_ended)
        self.parser.subscribe_to_event("cmd_dem_stop", self.save_to_file)

        #Player Connects and Updates
        #self.parser.subscribe_to_event("gevent_player_team", self.player_team)
        self.parser.subscribe_to_event("parser_update_pinfo", self.update_pinfo)
    
        #Chat
        self.parser.subscribe_to_event("parser_server_chat", self.server_chat)
        self.parser.subscribe_to_event("parser_player_chat", self.player_chat)

        #Timing based Stats - Round starts, freezetime and End 
        self.parser.subscribe_to_event("gevent_begin_new_match", self.begin_new_match)
        self.parser.subscribe_to_event("gevent_round_prestart", self.round_start)
        self.parser.subscribe_to_event("gevent_round_freeze_end", self.round_freezetime_end)
        self.parser.subscribe_to_event("gevent_round_end", self.round_end)
        self.parser.subscribe_to_event("gevent_cs_win_panel_match", self.match_end)
        
        #Player based Stats - kills, assists, deaths, etc 
        self.parser.subscribe_to_event("gevent_player_spawn", self.player_spawn)
        #self.parser.subscribe_to_event("gevent_player_death", self.player_death)
        #self.parser.subscribe_to_event("gevent_bomb_planted", self.bomb_planted)
        
        self.parser.parse()


    #-----------------------------------Demo Start, Finnish-----------------------------------
    
    def demo_started(self,data):
        self.map = data.map_name
        self.match_started = False
        self.round_current = 1
        self.team_score = {2: 0, 3: 0}
        self.max_players = 0
        self.player_stats = dict()
        self.tickrate = int(data.ticks / data.playback_time)
        if 'FACEIT' in data.server_name:
            self.service = 'FACEIT'
        elif 'ESL' in data.server_name:
            self.service = 'ESL'
        elif self.tickrate == 128:
            self.service = 'ESEA'


    def demo_ended (self, data):
        printVerbose("Demofile ended")



    #-----------------------------------Connects-----------------------------------

    def player_team(self,data):
        if data["team"] == 0:
            return
        self.player_stats.get(data["userid"]).team = data["team"]



    def update_pinfo(self, data):
        if data.guid != "BOT":
            exist = None
            for x in self.player_stats.items():
                if data.xuid == x[1].userinfo.xuid:
                    exist = x[0]
                    break
            if exist:
                self.player_stats[exist].update(data, ui=True)
                if exist != data.user_id:
                    self.player_stats.update({data.user_id: self.player_stats[exist]})
                    self.player_stats.pop(exist)
            else:
                self.player_stats.update({data.user_id: MyPlayer(data, ui=True)})
            self.max_players = len(self.player_stats)



    #--------------------------- Connects  ---------------------------
    def player_chat(self, data):
        self.all_chat.append(data)
    
    def server_chat(self, data):
        self.all_chat.append(data)
    #------------------------Timing based Stats - Round starts, freezetime and End ------------------------

    def begin_new_match(self, data):
        printVerbose("Match started")
        if self.match_started:
            self.reset_player_stats_all()
        self.match_started = True
        self.round_start()
        

    def round_start(self, data=None):
        for p, s in self.player_stats.items():
            s.round_stats[self.round_current] = SegmentStats()
        printVerbose("----------\nRound {} started".format(self.round_current))

    def round_freezetime_end(self, data):
        self.round_start_tick = self.current_tick
        printVerbose("Round {} freezetime ended".format(self.round_current))

    def round_end (self, data):
        print(data)
        printVerbose("Round {} ended".format(self.round_current))
        if self.match_started:
            self.round_current += 1
            self.max_round_time = 115
        


    def match_end(self, data):
        printVerbose("Match ended")

    #-----------------------------------Demo Start, Finnish-----------------------------------

    def player_death(self,data):
        if self.match_started:
            round = self.round_current
            k = self.player_stats.get(data["attacker"])
            a = self.player_stats.get(data["assister"])
            d = self.player_stats.get(data["userid"])

            if k:
                self.player_stats[data["attacker"]].k += 1
            if d:
                self.player_stats[data["userid"]].d += 1
            if a and data["assister"] and not data["assistedflash"]:
                self.player_stats[data["assister"]].a += 1




    def increment_field(self, player):
        if not player:
            return
        self.player_stats[player].round_stats[self.round_current].k += 1

    def player_spawn(self, data):
        if not data or not self.match_started or data["teamnum"] == 0:
            return
        player = self.player_stats.get(data["userid"])
        if not player or not player.round_stats.get(self.round_current):
            return
        print("assigning team")
        player.round_stats[self.round_current].team = data["teamnum"]





    def reset_player_stats_all(self):
        for p in self.player_stats.keys():
            self.reset_player_stats_one(p)

    def reset_player_stats_one(self, player):
        if not player:
            return
        self.player_stats[player].round_stats = dict()

    def init_player_round_all(self):
        for p in self.player_stats.keys():
            self.init_player_round_one(p)

    def reset_player_round_one(self, player):
        if not player or not self.player_stats.get(player) or not self.player_stats.get(player).round_stats.get(self.round_current):
            return
        self.player_stats[player].round_stats[self.round_current] = SegmentStats()

    def bomb_planted(self, data):
        self.max_round_time = 40
        self.round_start_tick = self.current_tick


# 2 = "T" // 3 = "CT"
class MyPlayer:
    def __init__(self, data=None, ui=False):
        self.round_stats = dict()
        self.name = None
        self.id = None
        self.profile = None
        self.bot = False
        self.userinfo = None
        if data:
            self.update(data, ui)

    def update(self, data, ui=False):
        if ui:
            self.userinfo = data
            self.id = data.user_id
            self.name = data.name
            self.profile = "https://steamcommunity.com/profiles/" + str(data.xuid)

    def print(self):
        hf.printDic(self)

    def __str__(self):
        return hf.printDic(self)

    def toDict(self):
        player_dict = self.__dict__
        player_dict['userinfo'] = self.userinfo.__dict__
        return player_dict


class SegmentStats:
    def __init__(self):
        self.team = 0
        self.k = 0
        self.d = 0
        self.a = 0
        self.k0 = 0
        self.k1 = 0
        self.k2 = 0
        self.k3 = 0
        self.k4 = 0
        self.k5 = 0
        self.bomb_defuses = 0
        self.bomb_plants = 0
        self.damage_dealt = 0
        self.entries_t = 0
        self.entries_ct = 0
        self.shots = 0
        self.hits = 0
        self.headshots = 0
        self.money_spent = 0
        self.mvps = 0
        self.score = 0
        self.teamkills = 0
        self.rws = 0
        self.health = 100
        self.round_win = 0
        self.damage_report = dict()




if __name__ == "__main__":
    demoInstance = Demo('4675b31d-9b6c-4411-9997-156f72325684.dem')
    demoInstance.analyze()