import DemoParserCSGO.DemoParser as dp

match_started = False
round_current = 1
max_players = 10
PLAYERS = dict()
tickrate = 0
current_tick = 0
sec_threshold = 0
round_start_tick = 0
round_timer = 0
max_round_time = 115

def printDic(dic,ident=0):
    sBuffer = ''
    if isinstance(dic,dict):
        for key, value in dic.items():
            if not (isinstance(value,list) or isinstance(value,dict)):
                sBuffer += ' '*ident + str(key) + ': '+ str(value) + '\n'
            else:
                sBuffer += ' '*ident + str(key) + ': '  + '\n'
                sBuffer += printDic(value,ident+5)
        
    elif isinstance(dic,list):
        for i in dic:
            sBuffer += printDic(i,ident)
            if len(dic)== 0 or (isinstance(i,list) or isinstance(i,dict)) :
                sBuffer += ' '* ident + '---------------------'  + '\n'
    elif isinstance(dic,str):
        sBuffer += ' ' * ident + dic  + '\n'
    elif isinstance(dic,int) or isinstance(dic,float) or isinstance(dic,complex):
        sBuffer += ' ' * ident + str(dic)  + '\n'
    else:
        sBuffer += printDic(dic.__dict__,ident)
    
    return sBuffer


def analyze_demo(path):
    file = open(path, "rb")
    parser = dp.DemoParser(file, ent="NONE")
    print('subscribing to death')
    parser.subscribe_to_event("gevent_player_death", player_death)
    parser.subscribe_to_event("parser_start", new_demo)
    parser.subscribe_to_event("gevent_player_blind", player_blind)
    parser.subscribe_to_event("parser_new_tick", get_entities)
    parser.subscribe_to_event("gevent_player_death", player_death)
    parser.subscribe_to_event("gevent_player_team", player_team)
    parser.subscribe_to_event("gevent_player_spawn", player_spawn)
    parser.subscribe_to_event("gevent_begin_new_match", begin_new_match)
    parser.subscribe_to_event("gevent_round_officially_ended", round_officially_ended)
    parser.subscribe_to_event("gevent_round_freeze_end", round_fr_end)
    parser.subscribe_to_event("gevent_bomb_planted", bomb_planted)
    parser.subscribe_to_event("gevent_hostage_follows", hostage_follows)
    parser.subscribe_to_event("parser_update_pinfo", update_pinfo)
    parser.subscribe_to_event("cmd_dem_stop", match_ended)
    parser.subscribe_to_event("cmd_dem_stop", print_end_stats)

    parser.parse()


def getTime(round_timer):
    return "{}:{}".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2))

def player_blind(data):
    v = PLAYERS.get(data["userid"])
    a = PLAYERS.get(data["attacker"])
    time = round(data["blind_duration"], 2)
    if not v or not a:
        return
    # print(ve.get_prop("m_flFlashMaxAlpha"))
    # print(ve.get_prop("m_flFlashDuration"))
    if time > sec_threshold and not v.dead and time > remaining_flash_time(v):
        v.flashedby = a
        v.lastflashdur = time
        v.lastflashtick = current_tick
        if v.start_team == a.start_team:
            a.teamflashes += 1
            a.teamflashesduration += time
        else:
            a.enemyflashes += 1
            a.enemyflashesduration += time


def player_death(data):
    if match_started:
        d = PLAYERS.get(data["userid"])
        if not d:
            return
        d.dead = True
        if not d.flashedby:
            return
        if d.start_team == d.flashedby.start_team:
            d.flashedby.ftotd.append(round_current)
        else:
            d.flashedby.ftoed.append(round_current)


def player_team(data):
    global PLAYERS, max_players, round_current
    #trying to find out player teams (and bots, mainly bots here) since i'm not parsing entities
    if data["isbot"]:
        print("bot {} joined team {} / disc= {}".format(data["userid"], data["team"], data["disconnect"]))
    else:
        print("player {} joined team {} / disc= {}".format(data["userid"], data["team"], data["disconnect"]))
    if data["team"] == 0 or data["isbot"]:
        return
    rp = PLAYERS.get(data["userid"])
    if rp and rp.start_team is None:
        if max_players == 10:
            if round_current <= 15:
                if data["team"] in (2, 3):
                    rp.start_team = data["team"]
            else:
                if data["team"] == 2:
                    rp.start_team = 3
                elif data["team"] == 3:
                    rp.start_team = 2
        elif max_players == 4:
            if round_current <= 8:
                if data["team"] in (2, 3):
                    rp.start_team = data["team"]
            else:
                if data["team"] == 2:
                    rp.start_team = 3
                elif data["team"] == 3:
                    rp.start_team = 2


def player_spawn(data):
    global PLAYERS, max_players, round_current
    # trying to find out player teams since i'm not parsing entities
    if data["teamnum"] == 0:
        return
    rp = PLAYERS.get(data["userid"])
    if rp and rp.start_team is None:
        if max_players == 10:
            if round_current <= 15:
                if data["teamnum"] in (2, 3):
                    rp.start_team = data["teamnum"]
            else:
                if data["teamnum"] == 2:
                    rp.start_team = 3
                elif data["teamnum"] == 3:
                    rp.start_team = 2
        elif max_players == 4:
            if round_current <= 8:
                if data["teamnum"] in (2, 3):
                    rp.start_team = data["teamnum"]
            else:
                if data["teamnum"] == 2:
                    rp.start_team = 3
                elif data["teamnum"] == 3:
                    rp.start_team = 2


def begin_new_match(data):
    global match_started
    if match_started:
        _reset_pstats()
    match_started = True
    print("\nMATCH STARTED.....................................................................\n")

def round_officially_ended(data):
    global match_started, round_current, max_round_time
    if match_started:
        # STATS.update({round_current: MyRoundStats(team_score[2], team_score[3], PLAYERS)})
        round_current += 1
        max_round_time = 115
        for p in PLAYERS.values():
            if p:
                p.dead = False
    print("\nROUND {}..........................................................\n".format(round_current))


def match_ended(data):
    print("\nMATCH ENDED.....................................................................\n")


def _reset_pstats():
    global PLAYERS
    for p2 in PLAYERS.values():
        p2.start_team = None


def update_pinfo(data):
    global PLAYERS, max_players
    if data.guid != "BOT":
        exist = None
        for x in PLAYERS.items():
            if data.xuid == x[1].userinfo.xuid:
                exist = x[0]
                break
        if exist:
            PLAYERS[exist].update(data, ui=True)
            if exist != data.user_id:
                PLAYERS.update({data.user_id: PLAYERS[exist]})
                PLAYERS.pop(exist)
        else:
            PLAYERS.update({data.user_id: MyPlayer(data, ui=True)})
        max_players = len(PLAYERS)


def new_demo(data):
    global match_started, round_current, PLAYERS, tickrate, current_tick
    current_tick = 0
    tickrate = int(data.ticks / data.playback_time)
    match_started = False
    round_current = 1
    PLAYERS = dict()


def round_fr_end(data):
    global round_start_tick
    round_start_tick = current_tick


def bomb_planted(data):
    global round_start_tick, max_round_time
    max_round_time = 40
    round_start_tick = current_tick


def hostage_follows(data):
    global max_round_time
    max_round_time += 60


def print_end_stats(data):
    for p in PLAYERS.values():
        print(p)
    print("End Stats would go here")


def get_entities(data):
    #print(data)
    global current_tick, round_timer
    # PLAYER_ENTITIES.clear()
    current_tick = data
    round_timer = round(max_round_time - ((current_tick - round_start_tick) / tickrate), 2)
    for p in PLAYERS.values():
        # PLAYER_ENTITIES.update({p.userinfo.entity_id: data[0].get(p.userinfo.entity_id)})
        # if PLAYER_ENTITIES.get(p.userinfo.entity_id) and PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashMaxAlpha"):
        #     print("alpha", PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashMaxAlpha"))
        #     print(PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashDuration"))
        if p.flashedby and not remaining_flash_time(p):
            # print("FLASH EXPIRED FOR {} AT {}\n".format(p.name, current_tick))
            p.flashedby = None


def remaining_flash_time(player):
    timesinceflash = (current_tick - player.lastflashtick) / tickrate
    # print(player.name, timesinceflash, player.lastflashdur)
    if timesinceflash >= player.lastflashdur:
        # print(player.name, timesinceflash, player.lastflashdur)
        return 0
    return timesinceflash


def fix_len_string(text, le):
    text = str(text)
    if len(text) > le:
        return text[:le]
    else:
        while len(text) != le:
            text += " "
        return text


class MyPlayer:
    def __init__(self, data=None, ui=False):
        self.k = 0
        self.d = 0
        self.a = 0
        self.teamflashes = 0
        self.enemyflashes = 0
        self.teamflashesduration = 0
        self.enemyflashesduration = 0
        self.ftotd = list()
        self.ftoed = list()
        self.flashedby = None
        self.lastflashdur = 0
        self.lastflashtick = 0
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
        printDic(self)

    def __str__(self) :
        return printDic(self)

if __name__ == "__main__":
    analyze_demo('4675b31d-9b6c-4411-9997-156f72325684.dem')