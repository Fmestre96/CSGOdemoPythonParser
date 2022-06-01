import DemoParserCSGO.DemoParser as dp
import tkinter as tk

match_started = False
round_current = 1
max_players = 10
PLAYERS_BY_UID = dict()
tickrate = 0
current_tick = 0
file = None
sec_threshold = 0
round_start_tick = 0
round_timer = 0
max_round_time = 115


def analyze_demo(path='demos/faceit.dem'):

    file = open(path, "rb")
    parser = dp.DemoParser(file, ent="NONE")

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
    
    #try:
    parser.parse()
    #except Exception:
    #    AlertWindow(app.window, "Error analyzing demo")

    app.status.text.set("done / waiting")
    app.status.frame.config(fg="#33ccff")
    file.close()




def player_blind(data):
    v = PLAYERS_BY_UID.get(data["userid"])
    a = PLAYERS_BY_UID.get(data["attacker"])
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
            if max_round_time == 40:
                print("BOMB ")
            print("{}:{} / ".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2)))
            print("Team Flash > {} flashed {} for {}s".format(a.name, v.name, time))
            a.teamflashes += 1
            a.teamflashesduration += time
        else:
            if max_round_time == 40:
                print("BOMB ")
            print("{}:{} / ".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2)))
            print("Enemy Flash > {} flashed {} for {}s".format(a.name, v.name, time))
            a.enemyflashes += 1
            a.enemyflashesduration += time


def player_death(data):
    if match_started:
        d = PLAYERS_BY_UID.get(data["userid"])
        if not d:
            return
        d.dead = True
        if not d.flashedby:
            return
        if d.start_team == d.flashedby.start_team:
            if max_round_time == 40:
                print("BOMB ")
            print("{}:{} / ".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2)))
            print("Team Death > {} died flashed by {}".format(d.name, d.flashedby.name))
            d.flashedby.ftotd.append(round_current)
        else:
            if max_round_time == 40:
                print("BOMB ")
            print("{}:{} / ".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2)))
            print("Enemy Death > {} died flashed by {}".format(d.name, d.flashedby.name))
            d.flashedby.ftoed.append(round_current)


def player_team(data):
    global PLAYERS_BY_UID, max_players, round_current
    # trying to find out player teams (and bots, mainly bots here) since i'm not parsing entities
    # if data["isbot"]:
    #     print("bot {} joined team {} / disc= {}".format(data["userid"], data["team"], data["disconnect"]))
    # else:
    #     print("player {} joined team {} / disc= {}".format(data["userid"], data["team"], data["disconnect"]))
    if data["team"] == 0 or data["isbot"]:
        return
    rp = PLAYERS_BY_UID.get(data["userid"])
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
    global PLAYERS_BY_UID, max_players, round_current
    # trying to find out player teams since i'm not parsing entities
    if data["teamnum"] == 0:
        return
    rp = PLAYERS_BY_UID.get(data["userid"])
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
    global match_started, file
    if match_started:
        _reset_pstats()
    match_started = True
    print("MATCH STARTED.....................................................................")


def round_officially_ended(data):
    global match_started, round_current, file, max_round_time
    if match_started:
        # STATS.update({round_current: MyRoundStats(team_score[2], team_score[3], PLAYERS)})
        round_current += 1
        max_round_time = 115
        for p in PLAYERS_BY_UID.values():
            if p:
                p.dead = False
    print("ROUND {}..........................................................".format(round_current))


def match_ended(data):
    global file
    print("MATCH ENDED.....................................................................")


def _reset_pstats():
    global PLAYERS_BY_UID
    for p2 in PLAYERS_BY_UID.values():
        p2.start_team = None


def update_pinfo(data):
    global PLAYERS_BY_UID, max_players
    if data.guid != "BOT":
        exist = None
        for x in PLAYERS_BY_UID.items():
            if data.xuid == x[1].userinfo.xuid:
                exist = x[0]
                break
        if exist:
            PLAYERS_BY_UID[exist].update(data, ui=True)
            if exist != data.user_id:
                PLAYERS_BY_UID.update({data.user_id: PLAYERS_BY_UID[exist]})
                PLAYERS_BY_UID.pop(exist)
        else:
            PLAYERS_BY_UID.update({data.user_id: MyPlayer(data, ui=True)})
        max_players = len(PLAYERS_BY_UID)


def new_demo(data):
    global match_started, round_current, PLAYERS_BY_UID, tickrate, current_tick
    current_tick = 0
    tickrate = int(data.ticks / data.playback_time)
    match_started = False
    round_current = 1
    PLAYERS_BY_UID = dict()


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
    global file
    data1 = sorted(PLAYERS_BY_UID.values(), key=lambda x: x.teamflashesduration, reverse=True)
    data2 = sorted(PLAYERS_BY_UID.values(), key=lambda x: x.enemyflashesduration, reverse=True)
    print("TEAM FLASH STATS:")
    for p in data1:
        print("{} blinded teammates {} ".format(fix_len_string(p.name, 20), fix_len_string(p.teamflashes, 2)))
        print("times for {}s ".format(fix_len_string(round(p.teamflashesduration, 2), 5)))
        print("resulting in {} team deaths".format(fix_len_string(len(p.ftotd), 2)))
        if len(p.ftotd):
            print(" in rounds: ")
            for r in p.ftotd:
                print("{}, ".format(r))
        print("")
    print("ENEMY FLASH STATS:")
    for p in data2:
        print("{} blinded enemies {} ".format(fix_len_string(p.name, 20), fix_len_string(p.enemyflashes, 2)))
        print("times for {}s ".format(fix_len_string(round(p.enemyflashesduration, 2), 5)))
        print("resulting in {} enemy deaths".format(fix_len_string(len(p.ftoed), 2)))
        if len(p.ftoed):
            print(" in rounds: ")
            for r in p.ftoed:
                print("{}, ".format(r))
        print("")


def get_entities(data):
    global current_tick, round_timer
    # PLAYER_ENTITIES.clear()
    current_tick = data
    round_timer = round(max_round_time - ((current_tick - round_start_tick) / tickrate), 2)
    for p in PLAYERS_BY_UID.values():
        # PLAYER_ENTITIES.update({p.userinfo.entity_id: data[0].get(p.userinfo.entity_id)})
        # if PLAYER_ENTITIES.get(p.userinfo.entity_id) and PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashMaxAlpha"):
        #     print("alpha", PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashMaxAlpha"))
        #     print(PLAYER_ENTITIES[p.userinfo.entity_id].get_prop("m_flFlashDuration"))
        if p.flashedby and not remaining_flash_time(p):
            # print("FLASH EXPIRED FOR {} AT {}".format(p.name, current_tick))
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


class MyButtonStyle:
    def __init__(self, root, label, cmd, name=None):
        self.text = tk.StringVar()
        self.text.set(label)
        self.btn = tk.Button(root, textvariable=self.text, command=cmd, name=name)
        self.btn.config(font=("arial", 10, ""), fg="white", bg="#101010", activebackground="#404040", bd=3)


class MyLabelStyle:
    def __init__(self, root, label):
        self.text = tk.StringVar()
        self.text.set(label)
        self.frame = tk.Label(root, textvariable=self.text)
        self.frame.config(font=("arial", 10, ""), fg="white", bg="#101010")


class MyEntryStyle:
    def __init__(self, root, label):
        self.text = tk.StringVar()
        self.text.set(label)
        self.frame = tk.Entry(root, textvariable=self.text)
        self.frame.config(justify=tk.CENTER, font=("arial", 10, ""), borderwidth=2, bg="#f0f0f0",
                          readonlybackground="#f0f0f0", width=5)


class AlertWindow:
    def __init__(self, root, message):
        self.window = tk.Toplevel(root)
        self.window.transient(root)
        self.window.title("error")
        self.window.minsize(100, 50)
        self.window.resizable(False, False)
        self.window.attributes("-topmost")
        self.window.config(bg="#101010")
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        x = MyLabelStyle(self.window, message)
        x.frame.pack()
        x = MyButtonStyle(self.window, "Close", self.window.destroy)
        x.btn.pack()
        self.window.update_idletasks()
        self.window.geometry("+%d+%d" % (calc_window_pos(root, self.window)))
        self.window.grab_set()
        self.window.focus_set()


class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Bang Bang Flashes")
        # self.window.minsize(sizex, sizey)
        # self.window.resizable(False, False)
        self.window.config(bg="#101010")
        frame = tk.Frame(self.window, bg="#101010")
        x = MyLabelStyle(frame, "Check flash over")
        x.frame.pack(side=tk.LEFT, padx=5, pady=2)
        self.entry = MyEntryStyle(frame, "0")
        self.entry.frame.pack(side=tk.LEFT, padx=5, pady=2)
        x = MyLabelStyle(frame, "seconds")
        x.frame.pack(side=tk.LEFT, padx=5, pady=2)
        frame.pack()
        self.status = MyLabelStyle(self.window, "waiting")
        self.status.frame.config(font=("arial", 12, ""), fg="#33ccff")
        self.status.frame.pack(padx=5, pady=5)
        frame = tk.Frame(self.window, bg="#101010")
        x = MyButtonStyle(frame, "Analyze", cmd=analyze_demo)
        x.btn.pack(side=tk.LEFT, padx=5, pady=2)
        frame.pack()



def calc_window_pos(x, y):
    if x.winfo_height() - y.winfo_height() < 0:
        return x.winfo_x() + (x.winfo_width() - y.winfo_width()) / 2, x.winfo_y()
    return x.winfo_x() + (x.winfo_width() - y.winfo_width()) / 2, x.winfo_y() + (
            x.winfo_height() - y.winfo_height()) / 2



def check_seconds(text):
    try:
        float(text)
        return True
    except ValueError:
        return False




if __name__ == "__main__":
    app = MainWindow()
    app.window.mainloop()
