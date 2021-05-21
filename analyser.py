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

    def save_to_file(self, data):
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
        hf.saveJson(stats)


    def analyze(self):
        file = open(self.path, "rb")
        self.parser = dp.DemoParser(file, ent="NONE")

        #Demo Start, Finnish
        self.parser.subscribe_to_event("parser_start", self.demo_started)
        self.parser.subscribe_to_event("cmd_dem_stop", self.demo_ended)
        self.parser.subscribe_to_event("cmd_dem_stop", self.save_to_file)

        #Connects
        self.parser.subscribe_to_event("gevent_player_team", self.player_team)
        self.parser.subscribe_to_event("parser_update_pinfo", self.update_pinfo)
    
        #Chat
        self.parser.subscribe_to_event("parser_server_chat", self.server_chat)
        self.parser.subscribe_to_event("parser_player_chat", self.player_chat)

        #Timing based Stats - Round starts, freezetime and End 
        self.parser.subscribe_to_event("gevent_begin_new_match", self.begin_new_match)
        self.parser.subscribe_to_event("gevent_round_start", self.round_start)
        self.parser.subscribe_to_event("gevent_round_freeze_end", self.round_fr_end)
        self.parser.subscribe_to_event("gevent_round_officially_ended", self.round_officially_ended)
        self.parser.subscribe_to_event("gevent_cs_win_panel_match", self.match_end)
        
        #Player based Stats - kills, assists, deaths, etc 
        self.parser.subscribe_to_event("gevent_player_spawn", self.player_spawn)
        self.parser.subscribe_to_event("gevent_player_death", self.player_death)
        self.parser.subscribe_to_event("gevent_bomb_planted", self.bomb_planted)
        
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
        rp = self.player_stats.get(data["userid"])
        if rp and rp.start_team is None:
            if self.max_players == 10:
                if self.round_current <= 15:
                    if data["team"] in (2, 3):
                        rp.start_team = data["team"]
                else:
                    if data["team"] == 2:
                        rp.start_team = 3
                    elif data["team"] == 3:
                        rp.start_team = 2
            elif self.max_players == 4:
                if self.round_current <= 8:
                    if data["team"] in (2, 3):
                        rp.start_team = data["team"]
                else:
                    if data["team"] == 2:
                        rp.start_team = 3
                    elif data["team"] == 3:
                        rp.start_team = 2


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
        if self.match_started:
            self._reset_pstats()
        self.match_started = True
        printVerbose("Match started")

    def round_start(self, data):
        if(self.round_current==2):
            #print(self.parser._game_events_dict)
            hf.saveTxt(self.parser._game_events_dict)
        printVerbose("----------\nRound {} started".format(self.round_current))

    def round_fr_end(self, data):
        self.round_start_tick = self.current_tick
        printVerbose("Round {} freezetime ended".format(self.round_current))

    def round_officially_ended (self, data):
        printVerbose("Round {} ended".format(self.round_current))
        if self.match_started:
            self.round_current += 1
            self.max_round_time = 115
            for p in self.player_stats.values():
                if p:
                    p.dead = False
        


    def match_end(self, data):
        printVerbose("Match ended")

    #-----------------------------------Demo Start, Finnish-----------------------------------

    def player_death(self,data):
        if self.match_started:
            k = self.player_stats.get(data["attacker"])
            a = self.player_stats.get(data["assister"])
            d = self.player_stats.get(data["userid"])

            if data["assister"] and not data["assistedflash"]:
                if a:  # asd
                    self.player_stats[data["assister"]].a += 1
                    # print("ass", d.userinfo.xuid, d.start_team, a.start_team, df, af)
                    if d and a.start_team and d.start_team and a.start_team == d.start_team:
                        self.player_stats[data["assister"]].a -= 1
            if k:
                self.player_stats[data["attacker"]].k += 1
            if d:
                self.player_stats[data["userid"]].d += 1
            if d and data["userid"] == data["attacker"]:
                self.player_stats[data["userid"]].k -= 2
            else:
                if k and d and k.start_team and d.start_team and k.start_team == d.start_team:
                    self.player_stats[data["attacker"]].k -= 2




    def player_spawn(self, data):
        # trying to find out player teams since i'm not parsing entities
        if data["teamnum"] == 0:
            return
        rp = self.player_stats.get(data["userid"])
        # print(data["userid"], bp, rp)
        # print("inside")
        # print(round_current, ">", bp, rp.start_team if rp else None)
        if rp and rp.start_team is None:
            if self.max_players == 10:
                if self.round_current <= 15:
                    if data["teamnum"] in (2, 3):
                        rp.start_team = data["teamnum"]
                else:
                    if data["teamnum"] == 2:
                        rp.start_team = 3
                    elif data["teamnum"] == 3:
                        rp.start_team = 2
            elif self.max_players == 4:
                if self.round_current <= 8:
                    if data["teamnum"] in (2, 3):
                        rp.start_team = data["teamnum"]
                else:
                    if data["teamnum"] == 2:
                        rp.start_team = 3
                    elif data["teamnum"] == 3:
                        rp.start_team = 2
        # print(">>", _BOTS.get(data["userid"]), rp.start_team if rp else None)
        # print(".................................................")




    def _reset_pstats(self):
        for p2 in self.player_stats.values():
            p2.start_team = None








    def bomb_planted(self, data):
        self.max_round_time = 40
        self.round_start_tick = self.current_tick


class MyPlayer:
    def __init__(self, data=None, ui=False):
        self.k = 0
        self.d = 0
        self.a = 0
        self.dead = True
        self.id = None
        self.name = None
        self.profile = None
        self.bot = False
        # 2 = "T" // 3 = "CT"
        self.start_team = None
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





if __name__ == "__main__":
    demoInstance = Demo('4675b31d-9b6c-4411-9997-156f72325684.dem')
    demoInstance.analyze()