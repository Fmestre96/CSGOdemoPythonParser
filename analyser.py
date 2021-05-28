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
        self.tickrate = 0
        self.player_stats = dict()
        self.round_stats = dict()
        self.last_spawns = dict()
        self.team_sides = self.empty_team_sides()
        self.all_chat = []


    def save_to_file(self):
        hf.saveJson(self.get_stats())

    def get_stats(self):
        #Convert SegmentStats into dics so I can __dict__ later
        for p, ps in self.player_stats.items():

            player_global_stats = SegmentStats()
            for r, rs in ps.round_stats.items():
                player_global_stats += rs

            self.player_stats[p].round_stats = {r: rs.__dict__ for r, rs in ps.round_stats.items()}
            self.player_stats[p].match_stats = player_global_stats.__dict__
    
        stats = {
            'file_info': {
                'path': self.path,
            },
            'demo_info': {
                'service': self.service,
                'map': self.map,
                'tickrate': self.tickrate,
            },
            'round_stats':{
                r: rs.toDict() for r, rs in self.round_stats.items()
            },
            'team_sides': self.team_sides,
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

        #Player Connects and Updates
        self.parser.subscribe_to_event("gevent_player_team", self.player_team)
        self.parser.subscribe_to_event("parser_update_pinfo", self.update_pinfo)
    
        #Chat
        self.parser.subscribe_to_event("parser_server_chat", self.server_chat)
        self.parser.subscribe_to_event("parser_player_chat", self.player_chat)

        #Timing based Stats - Round starts, freezetime and End 
        self.parser.subscribe_to_event("gevent_begin_new_match", self.begin_new_match)
        self.parser.subscribe_to_event("gevent_round_prestart", self.round_start)
        self.parser.subscribe_to_event("gevent_round_freeze_end", self.round_freezetime_end)
        self.parser.subscribe_to_event("gevent_round_end", self.round_end)
        self.parser.subscribe_to_event("gevent_round_officially_ended", self.round_officially_ended)
        self.parser.subscribe_to_event("gevent_cs_win_panel_match", self.match_end)
        
        #Player based Stats - kills, assists, deaths, etc 
        self.parser.subscribe_to_event("gevent_player_spawn", self.player_spawn)
        self.parser.subscribe_to_event("gevent_player_hurt", self.player_hurt)
        self.parser.subscribe_to_event("gevent_player_death", self.player_death)
        self.parser.subscribe_to_event("gevent_bomb_planted", self.bomb_planted)
        self.parser.subscribe_to_event("gevent_bomb_defused", self.bomb_defused)
        
        self.parser.parse()


    #-----------------------------------Demo Start, Finnish-----------------------------------
    
    def demo_started(self,data):
        self.map = data.map_name
        self.match_started = False
        self.round_current = 1
        self.player_stats = dict()
        self.tickrate = int(data.ticks / data.playback_time)
        if 'FACEIT' in data.server_name:
            self.service = 'FACEIT'
        elif 'ESL' in data.server_name:
            self.service = 'ESL'
        elif self.tickrate == 128:
            self.service = 'ESEA'


    def demo_ended(self, data):
        printVerbose("Demofile ended")
        #for p in self.team_sides["3"]["players"]:
        #    print("Player {} ({})".format(p, self.player_stats[p].name))
        self.save_to_file()



    #-----------------------------------Connects-----------------------------------

    def player_team(self,data):
        if data["team"] == 0 or data["isbot"]:
            return
        player_id = data["userid"]
        player_xuid = self.player_stats[player_id].userinfo.xuid
        old_team = data["oldteam"]
        new_team = data["team"]
        self.last_spawns[player_id] = new_team

        if player_id in self.team_sides[old_team]["players"]:
            self.team_sides[old_team]["players"].remove(player_id)

        if player_id not in self.team_sides[new_team]["players"]:
            self.team_sides[new_team]["players"].append(player_id)


    def update_pinfo(self, data):
        if data.guid != "BOT":
            exist = None
            for player_id, player_stats in self.player_stats.items():
                if data.xuid == player_stats.userinfo.xuid:
                    exist = player_id
                    break
            if exist:
                self.player_stats[exist].update(data, ui=True)
                if exist != data.user_id:
                    self.player_stats.update({data.user_id: self.player_stats[exist]})
                    self.player_stats.pop(exist)
            else:
                self.player_stats.update({data.user_id: MyPlayer(data, ui=True)})



    #--------------------------- Chat  ---------------------------
    def player_chat(self, data):
        self.all_chat.append(data)
    
    def server_chat(self, data):
        self.all_chat.append(data)

    #------------------------Timing based Stats - Round starts, freezetime and End ------------------------

    def begin_new_match(self, data):
        printVerbose("Match started")
        self.reset_player_stats_all()
        self.match_started = True
        self.round_current = 1
        self.team_sides = self.empty_team_sides()
        self.round_stats = dict()
        self.round_start()
        
        

    def round_start(self, data=None):
        if not self.match_started:
            return
        self.update_round()
        printVerbose("----------\nRound {} started".format(self.round_current))
        self.round_stats[self.round_current] = MyRound()
        for p, s in self.player_stats.items():
            s.round_stats[self.round_current] = SegmentStats()
        if self.is_swap_round():
            self.swap_team_sides()


    def round_freezetime_end(self, data):
        if not self.match_started:
            return
            
        printVerbose("Round {} freezetime ended".format(self.round_current))
        self.assign_team_sides()
        

    def round_end (self, data):
        if not self.match_started:
            return
        printVerbose("Round {} ended".format(self.round_current))
        if not data or not data.get("winner"):
            return
        for ps in self.player_stats.values():
            if ps.round_stats[self.round_current].team == data["winner"]:
                ps.round_stats[self.round_current].round_wins += 1
        self.team_sides[data["winner"]]["round_wins"] += 1
        
        
    def round_officially_ended (self, data):
        if not self.match_started:
            return
        printVerbose("Round {} officially ended".format(self.round_current))


    def match_end(self, data):
        printVerbose("Match ended")

    #-----------------------------------Demo Start, Finnish-----------------------------------

    def player_hurt(self, data):
        if not self.match_started:
            return

        #Get general info
        round = self.round_current
        r_stats = self.round_stats[round]
        k_id = data["attacker"]
        k = self.player_stats.get(k_id)
        d_id = data["userid"]
        d = self.player_stats.get(d_id)

        if not k or not d:
            return

        #First Time damage from attacker to victim
        if not k.round_stats[round].damage_report.get(d.name):
            k.round_stats[round].damage_report[d.name] = {"damage_given":{},"damage_taken":{},"teamdamage":False,"kill":False}

        if not d.round_stats[round].damage_report.get(k.name):
            d.round_stats[round].damage_report[k.name] = {"damage_given":{},"damage_taken":{},"teamdamage":False,"kill":False}
        
        #Frist time damage from attacker to victim in a specific hitgroup
        if not k.round_stats[round].damage_report[d.name]["damage_given"].get(data["hitgroup"]):
            k.round_stats[round].damage_report[d.name]["damage_given"][data["hitgroup"]] = {"hits":0, "dmg":0} 
            d.round_stats[round].damage_report[k.name]["damage_taken"][data["hitgroup"]] = {"hits":0, "dmg":0} 
        
        damage = d.round_stats[round].health if data["dmg_health"] > d.round_stats[round].health else data["dmg_health"]
        d.round_stats[round].health -= damage

        #If it's a kill
        if d.round_stats[round].health == 0:
            k.round_stats[round].damage_report[d.name]["damage_given"]["kill"] = True
            d.round_stats[round].damage_report[k.name]["damage_taken"]["kill"] = True

        #Add stats to damage_given to attacker || damage_taken to victim
        k.round_stats[round].damage_report[d.name]["damage_given"][data["hitgroup"]]["hits"] += 1
        k.round_stats[round].damage_report[d.name]["damage_given"][data["hitgroup"]]["dmg"] += damage
        d.round_stats[round].damage_report[k.name]["damage_taken"][data["hitgroup"]]["hits"] += 1
        d.round_stats[round].damage_report[k.name]["damage_taken"][data["hitgroup"]]["dmg"] += damage

        if k.round_stats[round].team != d.round_stats[round].team:
            k.round_stats[round].damage_given += damage
        else:
            k.round_stats[round].damage_report[d.name]["damage_given"]["teamdamage"] = True
            d.round_stats[round].damage_report[k.name]["damage_taken"]["teamdamage"] = True

    def player_death(self,data):
        if not self.match_started:
            return

        #Get general info
        round = self.round_current
        r_stats = self.round_stats[round]
        k_id = data["attacker"]
        k = self.player_stats.get(k_id)
        a_id = data["assister"]
        a = self.player_stats.get(a_id)
        d_id = data["userid"]
        d = self.player_stats.get(d_id)

        if not k or not d:
            return 

        k.round_stats[round].k += 1
        d.round_stats[round].d += 1

        
        # Increment Assist (if not flash)
        if a and not data["assistedflash"]:
            a.round_stats[round].a += 1

        # Increment Headshots
        if data["headshot"]:
            k.round_stats[round].headshots += 1

        #Increment Entry kills
        if not r_stats.first_kill_by_t and not r_stats.first_kill_by_ct:
            if k.round_stats[round].team==2:
                k.round_stats[round].entries_t += 1
                r_stats.first_kill_by_t = True
            elif k.round_stats[round].team==3:
                k.round_stats[round].entries_ct += 1
                r_stats.first_kill_by_ct = True


    def increment_kill(self, player):
        if not player:
            return
        self.player_stats[player].round_stats[self.round_current].k += 1

    def player_spawn(self, data):
        if not data or not self.match_started or data["teamnum"] == 0:
            #print("scenario 1")
            return




    def bomb_planted(self, data):
            if not self.match_started:
                return
            player = self.player_stats.get(data["userid"])
            round = self.round_current
            r_stats = self.round_stats[round]

            if not player:
                return
            player.round_stats[round].bomb_plants = 1
            r_stats.bomb_planted = True
            
    def bomb_defused(self, data):
        if not self.match_started:
            return
        player = self.player_stats.get(data["userid"])
        round = self.round_current
        r_stats = self.round_stats[round]
        if not player:
            return
        player.round_stats[round].bomb_defuses = 1
        r_stats.bomb_defused = True
            








    def empty_team_sides(self):
        team_sides =  {
            0:{
                "side":"U",
                "round_wins":0,
                "players":[]
            },
            1:{
                "side":"S",
                "round_wins":0,
                "players":[]
            },
            2: {
                "side":"T",
                "round_wins":0,
                "players":[]
            },
            3:{
                "side":"CT",
                "round_wins":0,
                "players":[]
            }
        }
        return team_sides

    def assign_team_sides(self):
        for player, side in self.last_spawns.items():
            if self.player_stats.get(player):
                self.player_stats[player].round_stats[self.round_current].team = side

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

    def get_player_by_xuid(self, xuid):
        for p_id, player_details in self.player_stats.items():
            if player_details.userinfo.xuid == xuid:
                return p_id
        return None

    def is_initial_side(self):
        swap=False
        round = self.round_current
        if round < 30:
            if round > 15:
                swap = not swap
        else:
            swap = not swap
            round -= 30
            while round > 6:
                round-=6
                swap = not swap
            if round > 2:
                swap= not swap



    def is_swap_round(self):
        round = self.round_current - 1
        if 0 < round < 30:
            return round % 15 == 0
        else:
            round -= 30
            return round % 3 == 0 and round % 6 != 0

    def swap_team_sides(self):
        self.team_sides[2]["round_wins"], self.team_sides[3]["round_wins"] = self.team_sides[3]["round_wins"], self.team_sides[2]["round_wins"]


    def update_round(self):
        try:
            self.round_current = self.team_sides[2]["round_wins"] + self.team_sides[3]["round_wins"] + 1
        except:
            self.round_current = 1

class MyRound:
    def __init__(self):
        self.first_kill_by_t = False
        self.first_kill_by_ct = False
        self.bomb_planted = False
        self.bomb_defused = False

    def toDict(self):
        return self.__dict__

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
        self.a = 0
        self.d = 0
        self.bomb_defuses = 0
        self.bomb_plants = 0
        self.damage_given = 0
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
        self.round_wins = 0
        self.multikills = {
            "0k":0,
            "1k":0,
            "2k":0,
            "3k":0,
            "4k":0,
            "5k":0,
        }
        self.damage_report = dict()

    def __add__(self, b):
        if isinstance(b, SegmentStats):
            c = SegmentStats()
            c.team = b.team
            c.k = self.k + b.k
            c.a = self.a + b.a
            c.d = self.d + b.d
            c.bomb_defuses = self.bomb_defuses + b.bomb_defuses
            c.bomb_plants = self.bomb_plants + b.bomb_plants
            c.damage_given = self.damage_given + b.damage_given
            c.entries_t = self.entries_t + b.entries_t
            c.entries_ct = self.entries_ct + b.entries_ct
            c.shots = self.shots + b.shots
            c.hits = self.hits + b.hits
            c.headshots = self.headshots + b.headshots
            c.money_spent = self.money_spent + b.money_spent
            c.mvps = self.mvps + b.mvps
            c.score = self.score + b.score
            c.teamkills = self.teamkills + b.teamkills
            c.rws = self.rws + b.rws
            c.health = self.health + b.health
            c.round_wins = self.round_wins + b.round_wins
            c.multikills = {
                "0k": self.multikills["0k"]+c.multikills["0k"],
                "1k": self.multikills["1k"]+c.multikills["1k"],
                "2k": self.multikills["2k"]+c.multikills["2k"],
                "3k": self.multikills["3k"]+c.multikills["3k"],
                "4k": self.multikills["4k"]+c.multikills["4k"],
                "5k": self.multikills["5k"]+c.multikills["5k"],
            }
            return c
        else:
            return self



if __name__ == "__main__":
    demoInstance = Demo('demos/faceit.dem')
    demoInstance.analyze()