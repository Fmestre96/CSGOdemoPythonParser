import json

def print_header(header):
    print("DEMO HEADER:")
    print("    header= {}".format(header.header))
    print("    protocol= {}".format(header.demo_protocol))
    print("    net_proto= {}".format(header.network_protocol))
    print("    server_name= {}".format(header.server_name))
    print("    client_name= {}".format(header.client_name))
    print("    map_name= {}".format(header.map_name))
    print("    game_dir= {}".format(header.game_directory))
    print("    play_time= {}".format(header.playback_time))
    print("    ticks= {}".format(header.ticks))
    print("    frames= {}".format(header.frames))
    print("    signon= {}".format(header.signon_length))


def print_event_list(my_list):
    print("GAME EVENTS LIST:")
    for item in my_list.items():
        print("  > {}, {} <    ....".format(item[0], item[1].name))
        for item2 in item[1].keys:
            print(" {} /".format(item2.name))
    print("")


def print_counter(table):
    print("COMMANDS:")
    for item in sorted(table[0]):
        print("    cmd= {} / count= {}".format(item[0], item[1]))
    print("MESSAGES:")
    for item in sorted(table[1]):
        print("    msg= {} / count= {}".format(item[0], item[1]))
    print("EVENTS:")
    for item in sorted(table[2]):
        print("    ev= {} / count= {}".format(item[0], item[1]))


def print_userinfo(data):
    for x in data:
        if x.name == "userinfo":
            data = x.data
            break
    print("USERINFO FROM TABLE:")
    print("    version / xuid / name / uid / guid / fid / fname / fakepl / isHLTV / custom / files / eid / tbd")
    for item in data:
        x = item["user_data"]
        if x:
            print("{}:   {} / {} / {} / {} / ".format(item["entry"], x.version, x.xuid, x.name, x.user_id))
            print("{} / {} / {} / {} / ".format(x.guid, x.friends_id, x.friends_name, x.fake_player))
            print("{} / {} / {} / ".format(x.is_hltv, x.custom_files, x.files_downloaded))
            print("{} / {} ///".format(x.entity_id, x.tbd))


def print_players_userinfo(data):
    print("USERINFO:")
    print("    version / xuid / name / uid / guid / fid / fname / fakepl / isHLTV / custom / files / eid / tbd")
    for p in data.items():
        x = p[1]
        if x:
            print("{}:   {} / {} / {} / {} / ".format(p[0], x.version, x.xuid, x.name, x.user_id))
            print("{} / {} / {} / {} / ".format(x.guid, x.friends_id, x.friends_name, x.fake_player))
            print("{} / {} / {} / ".format(x.is_hltv, x.custom_files, x.files_downloaded))
            print("{} / {} ///".format(x.entity_id, x.tbd))


def print_match_stats(data):
    print("MATCH STATS:")
    for x in data.items():
        if x[0] == "otherdata":
            continue
        print("Round {}:".format(x[0]))
        print("team2= {} / team3= {}".format(x[1].score_team2, x[1].score_team3))
        print("        K / A / D")
        for i in range(len(x[1].pscore)):
            print("{} > {} / {} / {}, team= {} xuid= {}".format(x[1].pscore[i].player.name, x[1].pscore[i].k,
                                                                       x[1].pscore[i].a, x[1].pscore[i].d,
                                                                       x[1].pscore[i].player.start_team,
                                                                       x[1].pscore[i].player.userinfo.xuid))
        print("...............................................................")


def print_entities(data):
    print("ENTITIES:")
    for x in data.items():
        if x[1] is None or x[1].parse is False:
            continue
        print("ENTITY #{}: {} //".format(x[0], x[1].class_name))
        for x2 in x[1].props.items():
            print("....{} //........".format(x2[0]))
            for x3 in x2[1].items():
                print("{} = {} // ".format(x3[0], x3[1]))
    print("")


def print_one_entity(data):
    print("ENTITY #{}: {} //".format(data.entity_id, data.class_name))
    for x2 in data.props.items():
        print("....{} //........".format(x2[0]))
        for x3 in x2[1].items():
            print("{} = {} // ".format(x3[0], x3[1]))
    print("")


def print_one_prop(data):
    for item in data.items():
        print("{} = {} // ".format(item[0], item[1]))
    print("")


def tick_to_time(round_timer):
    return "{}:{}".format(int(round_timer / 60), str(int(round_timer % 60)).zfill(2))


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


def saveJson(dic):
    with open('data.json', 'w') as outfile:
        json.dump(dic, outfile)



def fix_len_string(text, le):
    text = str(text)
    if len(text) > le:
        return text[:le]
    else:
        while len(text) != le:
            text += " "
        return text
