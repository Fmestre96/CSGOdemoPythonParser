import DemoParserCSGO.DemoParser as dp
import DemoParserCSGO.PrintStuff as hf


class Demo:
    def __init__(self,path):
        self.path = path
        self.match_started = False
        self.round_current = 1
        self.max_players = 10
        self.tickrate = 0
        self.current_tick = 0
        self.sec_threshold = 0
        self.round_start_tick = 0
        self.round_timer = 0
        self.max_round_time = 115
        self.PLAYERS = dict()
        self.BOTS = dict()
        self.takeovers = dict()
        self.STATS = {"otherdata": {},'rounds':{}}

    def save_to_file(self, data):
        stats = {
            'players': {k: v.toDict() for k,v in self.PLAYERS.items()},
            'stats':{},
            'takeovers':self.takeovers
        }
        hf.saveJson(stats)


    def analyze(self):
        file = open(self.path, "rb")
        parser = dp.DemoParser(file, ent="NONE")

        #Demo Start, Finnish
        parser.subscribe_to_event("parser_start", self.demo_started)
        parser.subscribe_to_event("cmd_dem_stop", self.demo_ended)
        parser.subscribe_to_event("cmd_dem_stop", self.save_to_file)

        #Connects
        parser.subscribe_to_event("gevent_player_team", self.player_team)
    
        #Chat


        #Timing based Stats - Round starts, freezetime and End 
        parser.subscribe_to_event("gevent_begin_new_match", self.begin_new_match)
        parser.subscribe_to_event("gevent_round_freeze_end", self.round_fr_end)
        parser.subscribe_to_event("gevent_round_officially_ended", self.round_officially_ended)
        
        #Player based Stats - kills, assists, deaths, etc 
        parser.subscribe_to_event("gevent_player_death", self.player_death)
        parser.subscribe_to_event("gevent_player_spawn", self.player_spawn)
        parser.subscribe_to_event("gevent_bomb_planted", self.bomb_planted)
        

        parser.parse()


    #-----------------------------------Demo Start, Finnish-----------------------------------
    
    def demo_started(self,data):
        self.match_started = False
        self.round_current = 1
        self.team_score = {2: 0, 3: 0}
        self.max_players = 0
        self.PLAYERS = dict()
        self.BOTS = dict()
        self.takeovers = dict()
        self.STATS = {"otherdata": {"map": data.map_name}, 'rounds':{}}


    def demo_ended (self, data):
        print("MATCH ENDED.....................................................................")



    #-----------------------------------Connects-----------------------------------

    def player_team(self,data):
        if data["team"] == 0:
            if data["isbot"] and self.BOTS.get(data["userid"]):
                self.BOTS.pop(data["userid"])
            return
        if data["isbot"] and not self.BOTS.get(data["userid"]):
            self.BOTS.update({data["userid"]: data["team"]})
            return
        rp = self.PLAYERS.get(data["userid"])
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


    #------------------------Timing based Stats - Round starts, freezetime and End ------------------------

    def round_fr_end (self, data):
        self.round_start_tick = self.current_tick


    def round_officially_ended (self, data):
        if self.match_started:
            self.STATS['rounds'].update({})
            self.round_current += 1
            self.max_round_time = 115
            for p in self.PLAYERS.values():
                if p:
                    p.dead = False
        print("ROUND {}..........................................................".format(self.round_current))



    #-----------------------------------Demo Start, Finnish-----------------------------------

    def player_death(self,data):
        if self.match_started:
            k = self.PLAYERS.get(data["attacker"])
            a = self.PLAYERS.get(data["assister"])
            d = self.PLAYERS.get(data["userid"])
            kf = self.BOTS.get(data["attacker"])
            af = self.BOTS.get(data["assister"])
            df = self.BOTS.get(data["userid"])
            kto = self.takeovers.get(data["attacker"])
            ato = self.takeovers.get(data["assister"])
            dto = self.takeovers.get(data["userid"])
            # if self.round_current == 7:
            #     print (self, data)
            if data["assister"] and not data["assistedflash"]:
                if a and not ato:  # asd
                    self.PLAYERS[data["assister"]].a += 1
                    # print("ass", d.userinfo.xuid, d.start_team, a.start_team, df, af)
                    if d and a.start_team and d.start_team and a.start_team == d.start_team:
                        self.PLAYERS[data["assister"]].a -= 1
                    elif not df and a.start_team and a.start_team == df:
                        self.PLAYERS[data["assister"]].a -= 1
            if k and not kto:
                self.PLAYERS[data["attacker"]].k += 1
            if d and not dto:
                self.PLAYERS[data["userid"]].d += 1
            if d and not dto and data["userid"] == data["attacker"]:
                self.PLAYERS[data["userid"]].k -= 2
            else:
                if k and not kto and d and k.start_team and d.start_team and k.start_team == d.start_team:
                    self.PLAYERS[data["attacker"]].k -= 2
                elif k and not kto and not df and k.start_team and k.start_team == df:
                    self.PLAYERS[data["attacker"]].k -= 2




    def player_spawn(self, data):
        # trying to find out player teams since i'm not parsing entities
        if data["teamnum"] == 0:
            return
        rp = self.PLAYERS.get(data["userid"])
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


    def begin_new_match(self, data):
        if self.match_started:
            self._reset_pstats()
        self.match_started = True
        print("MATCH STARTED.....................................................................")





    def _reset_pstats(self):
        for p2 in self.PLAYERS.values():
            p2.start_team = None


    def update_pinfo (self, data):
        if data.guid != "BOT":
            exist = None
            for x in self.PLAYERS.items():
                if data.xuid == x[1].userinfo.xuid:
                    exist = x[0]
                    break
            if exist:
                self.PLAYERS[exist].update(data, ui=True)
                if exist != data.user_id:
                    self.PLAYERS.update({data.user_id: self.PLAYERS[exist]})
                    self.PLAYERS.pop(exist)
            else:
                self.PLAYERS.update({data.user_id: MyPlayer(data, ui=True)})
            self.max_players = len(self.PLAYERS)







    def bomb_planted (self, data):
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