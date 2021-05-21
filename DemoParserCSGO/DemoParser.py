import math
import threading as t

from .proto import netmessages_pb2, cstrike15_usermessages_pb2

from . import PrintStuff as p
from . import consts as c
from .BitReader import Bitbuffer
from .ByteReader import Bytebuffer
from .structures import DemoHeader, CommandHeader, StringTable, UserInfo, ServerClass, Entity



class DemoParser:
    def __init__(self, demo_file, ent="ALL"):
        self._buf = Bytebuffer(demo_file.read())
        self._netmessages_pb2_dict = dict()
        for item in netmessages_pb2.NET_Messages.items():
            self._netmessages_pb2_dict.update({item[1]: item[0]})
        for item in netmessages_pb2.SVC_Messages.items():
            self._netmessages_pb2_dict.update({item[1]: item[0]})
        self._subscribers = dict()
        self._ut_set = set()
        self._ut_set.add("userinfo")
        self._ent = ent.upper()
        if self._ent != "NONE":
            self._ut_set.add("instancebaseline")
            self.subscribe_to_event("packet_svc_PacketEntities", self._mypkt_svc_PacketEntities)

            if self._ent != "ALL":
                settings = self._ent.split("+")
                self._ent_set = set()
                for s in settings:
                    if s == "P":
                        self._ent_set.add("CCSPlayer")
                        self._ent_set.add("CCSPlayerResource")
                        self._ent_set.add("CCSGameRulesProxy")
                    elif s == "T":
                        self._ent_set.add("CCSTeam")
                    elif s == "G":
                        self._ent_set.add("CBaseCSGrenadeProjectile")
                    elif s =="M":
                        self._ent_set.add("Cstrike_Chat_All")

        self.subscribe_to_event("packet_svc_CreateStringTable", self._mypkt_svc_CreateStringTable)
        self.subscribe_to_event("packet_svc_UpdateStringTable", self._mypkt_svc_UpdateStringTable)
        self.subscribe_to_event("packet_svc_GameEvent", self._mypkt_svc_GameEvent)
        self.subscribe_to_event("packet_svc_GameEventList", self._mypkt_svc_GameEventList)
        self.subscribe_to_event("packet_svc_UserMessage", self._mypkt_svc_EmitUserMessage)
    

        self.header = None
        self._game_events_dict = dict()
        self._serv_class_dict = dict()
        self._pending_baselines_dict = dict()
        self._baselines_dict = dict()
        self._data_tables_dict = dict()
        self._string_tables_list = list()
        self._class_bits = None
        self._entities = dict()
        self._players_by_uid = dict()
        self.progress = 0

    def subscribe_to_event(self, event: str, func: object):
        fncs = self._subscribers.get(event)
        if fncs:
            fncs.append(func)
        else:
            fncs = list()
            fncs.append(func)
        self._subscribers.update({event: fncs})

    def unsubscribe_from_event(self, event: str, func=None):
        if func:
            fncs = self._subscribers.get(event)
            if len(fncs) == 1:
                self._subscribers.pop(event)
                return
            for i2 in range(len(fncs)):
                if fncs[i2] == func:
                    fncs.pop(i2)
                    break
            self._subscribers.update({event: fncs})
        else:
            self._subscribers.pop(event)

    def _sub_event(self, event: str, data):
        ret = list()
        fncs = self._subscribers.get(event)
        if fncs:
            for func in fncs:
                rett = func(data)
                if rett:
                    ret.append(rett)
        return ret

    def parse(self):
        self.header = DemoHeader(self._buf.read(1072))
        assert self.header.header == "HL2DEMO"
        self._sub_event("parser_start", self.header)
        demo_finished = False
        old_tick = 0
        while not demo_finished:
            command_header = CommandHeader(self._buf.read(6))
            tick = command_header.tick
            if tick != old_tick:
                self._sub_event("parser_new_tick", tick)
                old_tick = tick
            # print(command_header.tick, command_header.command, command_header.player)
            self.progress = round(tick / self.header.ticks * 100, 2)
            cmd = command_header.command
            if cmd in (c.DEM_SIGNON, c.DEM_PACKET):  # 1 and 2
                self._handle_packet()
            elif cmd in (c.DEM_SYNCTICK, c.DEM_CUSTOMDATA):  # 3 and 8
                pass
            elif cmd == c.DEM_CONSOLECMD:  # 4
                self._handle_consolecmd()
                # pass
                # self.read_raw_data(None, 0)
            elif cmd == c.DEM_USERCMD:  # 5
                self._handle_usercmd()
                # pass
                # self.handle_usercmd(None, 0)
            elif cmd == c.DEM_DATATABLES:  # 6
                self._handle_datatables()
            elif cmd == c.DEM_STRINGTABLES:  # 9
                self._handle_stringtables()
            elif cmd == c.DEM_STOP:  # 7
                self._sub_event("cmd_dem_stop", None)
                #print(self.progress, "%  >DEMO ENDED<")
                #print("MATCH ENDED.....................................................................")
                demo_finished = True
            else:
                demo_finished = True
                raise Exception("Demo command not recognised: {}".format(cmd))
        return

    def _handle_packet(self):
        self._buf.read(152 + 4 + 4)
        length = self._buf.read_int()
        index = 0
        while index < length:
            msg = self._buf.read_varint()
            size = self._buf.read_varint()
            data = self._buf.read(size)
            index += self._buf.varint_size(msg) + self._buf.varint_size(size) + size
            self._sub_event("packet_" + self._netmessages_pb2_dict[msg], data)

    def _handle_datatables(self):
        length = self._buf.read_int()
        while True:
            v_type = self._buf.read_varint()
            size = self._buf.read_varint()
            data = self._buf.read(size)
            table = netmessages_pb2.CSVCMsg_SendTable()
            table.ParseFromString(data)
            if table.is_end:
                break
            self._data_tables_dict.update({table.net_table_name: table})
            # print(table.net_table_name)
        sv_classes = self._buf.read_short()
        self._class_bits = int(math.ceil(math.log2(sv_classes)))
        for i in range(sv_classes):
            my_id = self._buf.read_short()
            assert my_id == i
            name = self._buf.read_string()
            dt = self._buf.read_string()
            if self._ent != "NONE":
                sv_cls = ServerClass(my_id, name, dt)
                sv_cls.fprops = self._flatten_dt(self._data_tables_dict[dt])
                self._serv_class_dict.update({my_id: sv_cls})
                baseline = self._pending_baselines_dict.get(my_id)
                if baseline:
                    self._baselines_dict.update({my_id: self._get_baseline(baseline, my_id)})
                    self._pending_baselines_dict.pop(my_id)

    def _handle_stringtables(self):
        length = self._buf.read_int()
        data = self._buf.read(length)

    # PACKET MESSAGES >

    def _mypkt_svc_CreateStringTable(self, data):
        msg = netmessages_pb2.CSVCMsg_CreateStringTable()
        msg.ParseFromString(data)
        msg2 = StringTable(msg)
        uinfo = True if msg.name == "userinfo" else False
        self._update_string_table(msg.string_data, msg2, uinfo, msg.num_entries, msg.max_entries,
                                  msg.user_data_size_bits, msg.user_data_fixed_size)
        self._string_tables_list.append(msg2)

    def _update_string_table(self, data, res, uinfo, num_entries, max_entries, user_data_size, user_data_fixsize):
        _buf = Bitbuffer(data)
        history = []
        # ret = []
        entry = None
        entry_bits = int(math.log2(max_entries))
        assert not _buf.read_bit()
        index = 0
        last_index = -1
        for i in range(num_entries):
            index = last_index + 1
            if not _buf.read_bit():
                index = _buf.read_uint_bits(entry_bits)
            last_index = index
            assert 0 <= index <= max_entries
            if _buf.read_bit():
                if _buf.read_bit():
                    idx = _buf.read_uint_bits(5)
                    assert 0 <= idx <= 32
                    btc = _buf.read_uint_bits(c.SUBSTRING_BITS)
                    substring = history[idx][:btc]
                    suffix = _buf.read_string()
                    entry = substring + suffix
                else:
                    entry = _buf.read_string()
                res.data[index]["entry"] = entry
            user_data = None
            if _buf.read_bit():
                if user_data_fixsize:
                    user_data = _buf.readBits(user_data_size)
                else:
                    size = _buf.read_uint_bits(c.MAX_USERDATA_BITS)
                    user_data = _buf.readBits(size * 8)
                if uinfo:
                    user_data = UserInfo(user_data)
                    user_data.entity_id = int(res.data[index]["entry"]) + 1
                    self._sub_event("parser_update_pinfo", user_data)
                    # self._update_pinfo(user_data, res.data[index]["entry"])
                res.data[index]["user_data"] = user_data
            if len(history) == 32:
                history.pop(0)
            history.append(entry)
            if res.name == "instancebaseline" and user_data:
                cls_id = int(entry)
                if not self._serv_class_dict.get(cls_id):
                    self._pending_baselines_dict.update({cls_id: user_data})
                else:
                    self._baselines_dict.update({cls_id: self._get_baseline(user_data, cls_id)})
        # print("PB", sorted(self._pending_baselines_dict.keys()))

    def _mypkt_svc_UpdateStringTable(self, data):
        msg = netmessages_pb2.CSVCMsg_UpdateStringTable()
        msg.ParseFromString(data)
        obj = self._string_tables_list[msg.table_id]
        uinfo = True if obj.name == "userinfo" else False
        if obj.name in self._ut_set:
            self._update_string_table(msg.string_data, obj, uinfo, msg.num_changed_entries, obj.max_entries,
                                      obj.uds, obj.udfs)

    def _mypkt_svc_GameEvent(self, data):
        msg = netmessages_pb2.CSVCMsg_GameEvent()
        msg.ParseFromString(data)
        args = {}
        for i in range(len(msg.keys)):
            key_name = self._game_events_dict[msg.eventid].keys[i].name
            typed = msg.keys[i].type
            if typed == 1:
                key_val = msg.keys[i].val_string
            elif typed == 2:
                key_val = msg.keys[i].val_float
            elif typed == 3:
                key_val = msg.keys[i].val_long
            elif typed == 4:
                key_val = msg.keys[i].val_short
            elif typed == 5:
                key_val = msg.keys[i].val_byte
            elif typed == 6:
                key_val = msg.keys[i].val_bool
            elif typed == 7:
                key_val = msg.keys[i].val_uint64
            elif typed == 8:
                key_val = msg.keys[i].val_wstring
            else:
                raise Exception("UNKNOWN GameEvent Key Type: {}".format(msg.keys[i]))
            args.update({key_name: key_val})
        self._sub_event("gevent_" + self._game_events_dict[msg.eventid].name, args)

    def _mypkt_svc_PacketEntities(self, data):
        msg = netmessages_pb2.CSVCMsg_PacketEntities()
        msg.ParseFromString(data)
        buf = Bitbuffer(msg.entity_data)
        entity_id = -1
        for i2 in range(msg.updated_entries):
            entity_id += 1 + buf.readUBitVar()
            assert (0 <= entity_id <= (1 << c.MAX_EDICT_BITS)), "Entity id: {} < out of range".format(entity_id)
            if buf.read_bit():
                self._entities.update({entity_id: None})
                # if self._entities.get(entity_id):
                #     self._entities.pop(entity_id)
                buf.read_bit()
            elif buf.read_bit():
                cls_id = buf.read_uint_bits(self._class_bits)
                serial = buf.read_uint_bits(c.NUM_NETWORKED_EHANDLE_SERIAL_NUMBER_BITS)
                if self._ent != "ALL":
                    if self._serv_class_dict[cls_id].name in self._ent_set:
                        new_entity = Entity(self, entity_id, cls_id, serial)
                    else:
                        new_entity = Entity(self, entity_id, cls_id, serial, parse=False)
                else:
                    new_entity = Entity(self, entity_id, cls_id, serial)
                self._entities.update({entity_id: new_entity})
                self._read_new_entity(buf, new_entity)
            else:
                entity = self._entities[entity_id]
                self._read_new_entity(buf, entity)

    def _read_new_entity(self, buf, entity):
        sv_cls = self._serv_class_dict[entity.class_id]
        updates = self._handle_entity_update(buf, sv_cls, buffer=True)
        if entity.parse is False:
            return
        for update in updates:
            table_name = update["prop"]["table"].net_table_name
            var_name = update["prop"]["prop"].var_name
            entity.update(table_name, var_name, update["value"])

    def _mypkt_svc_GameEventList(self, data):
        msg = netmessages_pb2.CSVCMsg_GameEventList()
        msg.ParseFromString(data)
        for event in msg.descriptors:
            self._game_events_dict.update({event.eventid: event})


    def _mypkt_svc_EmitUserMessage(self, data):
        
        msg = netmessages_pb2.CSVCMsg_UserMessage()
        msg.ParseFromString(data)
        #5 = SayText
        #6 = SayText2
        if(msg.msg_type == 5):
            s = cstrike15_usermessages_pb2.CCSUsrMsg_SayText()
            s.ParseFromString(msg.msg_data)   
            s_dict = {
                'type_id': msg.msg_type,
                'type_name': 'SayText',
                'ent_idx': s.ent_idx,
                'text': s.text,
                'chat': s.chat,
            }
            self._sub_event("parser_server_chat", s_dict)
        elif(msg.msg_type == 6):
            s = cstrike15_usermessages_pb2.CCSUsrMsg_SayText2()
            s.ParseFromString(msg.msg_data)
            s_dict = {
                'type_id': msg.msg_type,
                'type_name': 'SayText2',
                'ent_idx': s.ent_idx,
                'chat': s.chat,
                'msg_name': s.msg_name,
                'params': [p for p in s.params],
                'textallchat': s.textallchat
            }
            self._sub_event("parser_player_chat", s_dict)
        #elif(msg.msg_type == 25):
        #    s = SpottedEntity(msg.msg_data)
        #    print(s.__dict__)
            
    # NO MORE PACKET MESSAGES <

    # NO MORE EVENTS HANDLERS <

    def _handle_entity_update(self, data, sv_cls, buffer=False):
        val = -1
        new_props = list()
        indices = list()
        buf = Bitbuffer(data) if not buffer else data
        new_way = buf.read_bit()
        while True:
            val = buf.read_index(val, new_way)
            if val == -1:
                break
            indices.append(val)
        for i2 in indices:
            prop = sv_cls.fprops[i2]
            val2 = buf.decode(prop)
            new_props.append({
                "prop": prop,
                "value": val2
            })
        return new_props

    def _get_baseline(self, data, id2):
        baseline = dict()
        sv_cls = self._serv_class_dict[id2]
        for item in self._handle_entity_update(data, sv_cls):
            table_name = item["prop"]["table"].net_table_name
            var_name = item["prop"]["prop"].var_name
            if not baseline.get(table_name):
                baseline.update({table_name: {}})
            baseline[table_name].update({var_name: item["value"]})
        return baseline

    def _flatten_dt(self, table):
        fprops = self._get_props(table, self._get_excl_props(table))
        prio = set(p2["prop"].priority for p2 in fprops)
        prio.add(64)
        prio = sorted(list(prio))
        start = 0
        for pr in prio:
            while True:
                cur_prop = start
                while cur_prop < len(fprops):
                    prop = fprops[cur_prop]["prop"]
                    if prop.priority == pr or (pr == 64 and (prop.flags & c.SPROP_CHANGES_OFTEN)):
                        if start != cur_prop:
                            temp = fprops[start]
                            fprops[start] = fprops[cur_prop]
                            fprops[cur_prop] = temp
                        start += 1
                        break
                    cur_prop += 1
                if cur_prop == len(fprops):
                    break
        return fprops

    def _get_props(self, table, excl):
        flat = list()
        for id2, prop in enumerate(table.props):
            if (prop.flags & c.SPROP_INSIDEARRAY or prop.flags & c.SPROP_EXCLUDE
                    or self._is_prop_excl(excl, table, prop)):
                continue
            if prop.type == c.PT_DataTable:
                sub_table = self._data_tables_dict[prop.dt_name]
                child_props = self._get_props(sub_table, excl)
                if (prop.flags & c.SPROP_COLLAPSIBLE) == 0:
                    for cp in child_props:
                        cp["col"] = False
                flat.extend(child_props)
            elif prop.type == c.PT_Array:
                flat.append({
                    "prop": prop,
                    "arr": table.props[id2 - 1],
                    "table": table
                })
            else:
                flat.append({
                    "prop": prop,
                    "table": table
                })
        return sorted(flat, key=self._key_sort)

    def _key_sort(self, item):
        if item.get("col", True) is False:
            return 0
        return 1

    def _is_prop_excl(self, excl, table, prop):
        for item in excl:
            if table.net_table_name == item.dt_name and prop.var_name == item.var_name:
                return True
        return False

    def _get_excl_props(self, table):
        excl = list()
        for id2, prop in enumerate(table.props):
            if prop.flags & c.SPROP_EXCLUDE:
                excl.append(prop)
            if prop.type == c.PT_DataTable:
                sub_table = self._data_tables_dict[prop.dt_name]
                excl.extend(self._get_excl_props(sub_table))
        return excl

    def _update_pinfo(self, data, entry):
        if data.guid != "BOT":
            self._players_by_uid.update({data.user_id: data})
            # exist = None
            # for x in self._players_userinfo.items():
            #     if data.xuid == x[1].xuid:
            #         exist = x[0]
            #         break
            # if exist:
            #     self._players_userinfo.update({exist: data})
            #     if exist != data.user_id:
            #         self._players_userinfo.update({data.user_id: self._players_userinfo[exist]})
            #         self._players_userinfo.pop(exist)
            # else:
            #     self._players_userinfo.update({data.user_id: data})
            # self._max_players = len(self._players_userinfo)

    def _update_cmd_counter(self, value, cmd=False, msg=False, ev=False):
        if cmd is True:
            for item in self._counter[0]:
                if item[0] == value:
                    item[1] += 1
                    return
            self._counter[0].append([value, 1])
            return
        elif msg is True:
            for item in self._counter[1]:
                if item[0] == value:
                    item[1] += 1
                    return
            self._counter[1].append([value, 1])
            return
        elif ev is True:
            for item in self._counter[2]:
                if item[0] == value:
                    item[1] += 1
                    return
            self._counter[2].append([value, 1])
            return

    #  OTHER FUNCTIONS >

    def get_player_entities(self, bots=False):
        ret = list()
        for x in self._string_tables_list:
            if x.name == "userinfo":
                for x2 in x.data:
                    ud = x2["user_data"]
                    entry = x2["entry"]
                    if not ud or not entry:
                        continue
                    if not bots and ud.guid == "BOT":
                        continue
                    y = self._entities.get(int(x2["entry"]) + 1)
                    if y:
                        ret.append(y)
        return ret

    def get_team_entities(self, all4=False):
        ret = list()
        all4 = 0 if all4 else 2
        for x in self._entities.values():
            if x and x.class_name == "CCSTeam":
                if x.get_prop("m_iTeamNum") >= all4:
                    ret.append(x)
        return ret

    def get_resource_table(self):
        for x in self._entities.values():
            if x and x.class_name == "CCSPlayerResource":
                return x

    def _handle_consolecmd(self):
        length = self._buf.read_int()
        data = self._buf.read(length)
        # print(data)

    def _handle_usercmd(self):
        length = self._buf.read_int()
        length = self._buf.read_int()
        data = self._buf.read(length)
        # print(data)
