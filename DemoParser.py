import math

import NETMSG_pb2 as pbuf
import PrintStuff as p
import consts as c
from BitReader import Bitbuffer
from ByteReader import Bytebuffer
from structures import DemoHeader, CommandHeader, StringTable, UserInfo, ServerClass, Entity


class DemoParser:
    def __init__(self, demo_path, dump=None, ent="ALL"):
        self._buf = Bytebuffer(open(demo_path, "rb").read())
        self._pbuf_dict = dict()
        for item in pbuf.NET_Messages.items():
            self._pbuf_dict.update({item[1]: item[0]})
        for item in pbuf.SVC_Messages.items():
            self._pbuf_dict.update({item[1]: item[0]})
        self._subscribers = dict()
        self.dump = None
        self._ut_set = set()
        self._ut_set.add("userinfo")
        self._ent = ent.upper()
        if self._ent != "NONE":
            self._ut_set.add("instancebaseline")
            self.subscribe_to_event("packet_svc_PacketEntities", self._mypkt_svc_PacketEntities)
            if self._ent != "ALL":
                self._ent_set = set()
                self._ent_set.add("CCSPlayer")
                self._ent_set.add("CCSTeam")
                self._ent_set.add("CCSPlayerResource")
                if self._ent_set == "P+G":
                    self._ent_set.add("CBaseCSGrenadeProjectile")
        if dump:
            self.dump = open(dump, "w", encoding="utf-8")
            self._counter = [[], [], []]

        self.subscribe_to_event("gevent_begin_new_match", self._my_begin_new_match)
        self.subscribe_to_event("gevent_round_end", self._my_round_end)
        self.subscribe_to_event("gevent_round_officially_ended", self._my_round_officially_ended)
        self.subscribe_to_event("packet_svc_CreateStringTable", self._mypkt_svc_CreateStringTable)
        self.subscribe_to_event("packet_svc_UpdateStringTable", self._mypkt_svc_UpdateStringTable)
        self.subscribe_to_event("packet_svc_GameEvent", self._mypkt_svc_GameEvent)
        self.subscribe_to_event("packet_svc_GameEventList", self._mypkt_svc_GameEventList)

        self.header = None
        self._game_events_dict = dict()
        self._serv_class_dict = dict()
        self._pending_baselines_dict = dict()
        self._baselines_dict = dict()
        self._data_tables_dict = dict()
        self._string_tables_list = list()
        self._class_bits = None
        self._entities = dict()
        self._players_userinfo = dict()
        self.progress = 0
        self._match_started = False
        self._round_current = 1

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
        while not demo_finished:
            command_header = CommandHeader(self._buf.read(6))
            tick = command_header.tick
            self.progress = round(tick / self.header.ticks * 100, 2)
            cmd = command_header.command
            # self.dump.write("cmd= {}\n".format(cmd))
            if self.dump:
                self._update_cmd_counter(cmd, cmd=True)
            if cmd in (c.DEM_SIGNON, c.DEM_PACKET):  # 1 and 2
                self._handle_packet()
            elif cmd in (c.DEM_SYNCTICK, c.DEM_CUSTOMDATA):  # 3 and 8
                pass
            elif cmd == c.DEM_CONSOLECMD:  # 4
                pass
                # self.read_raw_data(None, 0)
            elif cmd == c.DEM_USERCMD:  # 5
                pass
                # self.handle_usercmd(None, 0)
            elif cmd == c.DEM_DATATABLES:  # 6
                self._handle_datatables()
            elif cmd == c.DEM_STRINGTABLES:  # 9
                self._handle_stringtables()
            elif cmd == c.DEM_STOP:  # 7
                self._sub_event("cmd_dem_stop", None)
                # print(self.progress, "%  >DEMO ENDED<")
                demo_finished = True
            else:
                demo_finished = True
                print("Demo command not recognised: ", cmd)
        self._demo_ended_stuff()
        extra_data = dict()
        extra_data.update({"file": self.dump})
        self._sub_event("parser_demo_finished_print", self.dump)
        self._sub_event("parser_demo_finished", None)
        if self.dump:
            self.dump.close()
        return

    def _handle_packet(self):
        self._buf.read(152 + 4 + 4)
        length = self._buf.read_int()
        index = 0
        while index < length:
            msg = self._buf.read_varint()
            size = self._buf.read_varint()
            data = self._buf.read(size)
            # self.dump.write("...msg= {} / size= {}\n".format(msg, size))
            index += self._buf.varint_size(msg) + self._buf.varint_size(size) + size
            if self.dump:
                self._update_cmd_counter(msg, msg=True)
            self._sub_event("packet_" + self._pbuf_dict[msg], data)

    def _handle_datatables(self):
        length = self._buf.read_int()
        while True:
            v_type = self._buf.read_varint()
            size = self._buf.read_varint()
            data = self._buf.read(size)
            table = pbuf.CSVCMsg_SendTable()
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
        msg = pbuf.CSVCMsg_CreateStringTable()
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
                    self._update_pinfo(user_data)
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

    def _mypkt_svc_UpdateStringTable(self, data):
        msg = pbuf.CSVCMsg_UpdateStringTable()
        msg.ParseFromString(data)
        obj = self._string_tables_list[msg.table_id]
        uinfo = True if obj.name == "userinfo" else False
        if obj.name in self._ut_set:
            self._update_string_table(msg.string_data, obj, uinfo, msg.num_changed_entries, obj.max_entries,
                                      obj.uds, obj.udfs)

    def _mypkt_svc_GameEvent(self, data):
        msg = pbuf.CSVCMsg_GameEvent()
        msg.ParseFromString(data)
        if self.dump:
            self._update_cmd_counter(msg.eventid, ev=True)
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
                key_val = None
                print("UNKNOWN >", msg.keys[i])
                assert key_val is not None
            args.update({key_name: key_val})
        self._sub_event("gevent_" + self._game_events_dict[msg.eventid].name, args)

    def _mypkt_svc_PacketEntities(self, data):
        msg = pbuf.CSVCMsg_PacketEntities()
        msg.ParseFromString(data)
        buf = Bitbuffer(msg.entity_data)
        entity_id = -1
        for i2 in range(msg.updated_entries):
            entity_id += 1 + buf.readUBitVar()
            assert (0 <= entity_id <= (1 << c.MAX_EDICT_BITS)), "Entity id: {} < out of range".format(entity_id)
            if buf.read_bit():
                self._entities.update({entity_id: None})
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
        msg = pbuf.CSVCMsg_GameEventList()
        msg.ParseFromString(data)
        for event in msg.descriptors:
            self._game_events_dict.update({event.eventid: event})

    # NO MORE PACKET MESSAGES <

    # EVENTS HANDLERS >

    def _my_begin_new_match(self, data):
        # pass
        self._match_started = True
        # print("MATCH STARTED.....................................................................")

    def _my_round_end(self, data):
        pass
        # if self._match_started:
        #     print("    {} / {}".format(data["reason"], data["message"]))

    def _my_round_officially_ended(self, data):
        # pass
        if self._match_started:
            self._round_current += 1
        # print("ROUND {}..........................................................".format(self._round_current))
        # if self._round_current == 7:
        #     p.print_entities(self.dump, self._entities)

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

    def _update_pinfo(self, data):
        self._sub_event("parser_update_pinfo", data)
        if data.guid != "BOT":
            exist = None
            for x in self._players_userinfo.items():
                if data.xuid == x[1].xuid:
                    exist = x[0]
                    break
            if exist:
                self._players_userinfo.update({exist: data})
                if exist != data.user_id:
                    self._players_userinfo.update({data.user_id: self._players_userinfo[exist]})
                    self._players_userinfo.pop(exist)
                self._sub_event("parser_old_player_connected", data)
            else:
                self._sub_event("parser_new_player_connected", data)
                self._players_userinfo.update({data.user_id: data})
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

    def _demo_ended_stuff(self):
        if self.dump:
            p.print_header(self.dump, self.header)
            p.print_event_list(self.dump, self._game_events_dict)
            p.print_counter(self.dump, self._counter)
            # p.print_userinfo(self.dump, self._string_tables_list)
            p.print_players_userinfo(self.dump, self._players_userinfo)
            # p.print_entities(self.dump, self._entities)
