import DemoParserCSGO.DemoParser as dp
import DemoParserCSGO.PrintStuff as hf
import timeit



def analyse_demo(path):
    file = open(path, "rb")
    parser = dp.DemoParser(file, ent="ALL")

    parser.subscribe_to_event("gevent_begin_new_match", begin_new_match)
    parser.subscribe_to_event("gevent_round_start", round_start)
    parser.subscribe_to_event("gevent_round_officially_ended", round_officially_ended)
    
    parser.subscribe_to_event("gevent_cs_win_panel_match", match_end)

    parser.parse()




def begin_new_match(data):
    print("MATCH STARTED")

def round_start(data):
    print("ROUND START")

def round_officially_ended(data):
    print("ROUND ENDED")

def match_end(data):
    print("MATCH ENDED")



if __name__ == "__main__":
    starttime = timeit.default_timer()
    analyse_demo('4675b31d-9b6c-4411-9997-156f72325684.dem')
    print("Time:", timeit.default_timer() - starttime)


# ----------- entity times ----------- #
# None: 10 secs
# P: 260 secs
# G: 260 secs
# T: 260 secs
# ALL: 290 secs