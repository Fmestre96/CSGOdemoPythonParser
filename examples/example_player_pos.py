import DemoParserCSGO.DemoParser as dp

parser = None
# in_game_round_time = 0
PLAYERS = list()



def analyse_demo(path):
    global parser
    file = open(path, "rb")
    parser = dp.DemoParser(file, ent="P")

    parser.subscribe_to_event("parser_new_tick", print_player_positions)
    parser.subscribe_to_event("gevent_begin_new_match", begin_new_match)
    parser.subscribe_to_event("gevent_round_officially_ended", round_officially_ended)
    parser.subscribe_to_event("gevent_round_freeze_end", round_freeze_end)
    
    parser.parse()


class MyPlayer:
    def __init__(self, entity, userinfo):
        self.entity = entity
        self.userinfo = userinfo


def begin_new_match(data):
    # this event happens after warmup ends
    print("MATCH STARTED.....................................................................")


def round_officially_ended(data):
    # this event happens every time a round ends
    current_round = get_one_entity("CCSGameRulesProxy").get_prop("m_totalRoundsPlayed")
    #current_round = 1
    print("ROUND {} ..........................................................".format(current_round))


def round_freeze_end(data):
    # get player entities again since some may disconnect / reconnect in freeze time
    bind_player_entities()


def print_player_positions(data):
    global PLAYERS
    if not len(PLAYERS):
        return
    for player in PLAYERS:
        pos = player.entity.get_table("DT_CSLocalPlayerExclusive")
        posZ = player.entity.get_table("DT_LocalPlayerExclusive")["m_vecViewOffset[2]"]
        print("{} is at x: {} / y: {} / z: {} ".format(player.userinfo.name, pos["m_vecOrigin"]["x"], pos["m_vecOrigin"]["y"], pos["m_vecOrigin[2]"] + posZ))

def bind_player_entities():
    global PLAYERS, parser
    PLAYERS.clear()
    
    # looking for players through the "userinfo" table
    for table in parser._string_tables_list:
        if table.name == "userinfo":
            for player in table.data:
                # ud is a UserInfo instance from structures.py
                # entry is the entity id - 1
                ud = player["user_data"]
                entry = player["entry"]
                if not ud or not entry or ud.guid == "BOT":
                    continue
                player2 = parser._entities.get(int(player["entry"]) + 1)
                if player2:
                    PLAYERS.append(MyPlayer(player2, ud))
            break


def get_one_entity(text):
    global parser
    for ent in parser._entities.values():
        if ent and ent.class_name == text:
            return ent



if __name__ == "__main__":
    analyse_demo('demos/faceit.dem')