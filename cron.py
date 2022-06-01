import time
import zlib
import io
from analyser import Demo
from faceit_api import *
faceit_v1_api = FaceitDatav1('f348de50-3c73-465a-aaf7-2f483c5c19af')
faceit_v2_api = FaceitDatav2('1c3a0790-4039-4f60-8fc3-9ca1dd15f5c9')
faceit_v4_api = FaceitDatav4('f348de50-3c73-465a-aaf7-2f483c5c19af')
faceit_v5_api = FaceitDatav5('c0df1e5c-570d-4069-9399-ec28b350c115')

#ECL_ID = 'edc12227-3b07-4c5e-9325-f223025628f3'
hubs_to_watch = [
    '6f63b115-f45e-42b7-88ef-2a96714cd5e1',
    '08c65b47-aabe-40c6-a78b-a326b92b4f82',
    'ada458d4-34c4-47ab-84a1-1ab87626c829',
    '6f2ea6be-65bc-4895-8ddd-4978e98e0eb2',
]
matches_in_queue = []
matches_analysed = []

def print_chat(match_id, all_chat):
    #create a file for the chat
    folder = "./data/"
    print("Exporting chat for match " + match_id)
    with open('{}{}.txt'.format(folder, match_id), 'w', encoding="utf-8") as f:
        for chat in all_chat:
            if chat['type_id'] == 5:
                f.write(chat['text'] + '\n')
            elif chat['type_id'] == 6:
                f.write('{}: {}'.format(chat['params'][0], chat['params'][1]) + '\n')

def get_active_matches():
    for hub in hubs_to_watch:
        matches = faceit_v4_api.hub_matches(hub)
        for match in matches['items']:
            if match['status'] == 'FINISHED' and match['match_id'] not in matches_in_queue and match['match_id'] not in matches_analysed:
                print("Adding match " + match['match_id'] + " to queue")
                matches_in_queue.append(match['match_id'])


def analyse_next_in_queue():
    match_id = matches_in_queue[0]
    details = analyse_match(match_id)
    if not details:
        print("Failed to analyse match " + match_id)
        matches_in_queue.append(matches_in_queue.pop(0))
        return
    print_chat(match_id, details['all_chat'])
    matches_analysed.append(matches_in_queue.pop(0))


def analyse_match(match_id):
    print("Analysing match " + match_id)
    demo_file = getDemo(match_id)
    if demo_file:
        demo = Demo(demo_file)
        demo.analyse()
        return demo.output


def getDemo(match_id):
    match_details = faceit_v4_api.match_details(match_id)

    if 'demo_url' not in match_details.keys():
        return
    demolink = match_details['demo_url'][0]

    res = requests.get(demolink)
    if res.status_code == 200:
        decompressed_data = zlib.decompress(res.content, 16+zlib.MAX_WBITS)
        return io.BytesIO(decompressed_data)
    else:
        print('demo download not OK | ' + demolink + ' | ' + str(res.status_code) + ' | ' + match_id)
        return


if __name__ == '__main__':
    sleeps_performed = 0
    while True:
        if sleeps_performed % 10 == 0:
            get_active_matches()

        if len(matches_in_queue) > 0:
            analyse_next_in_queue()

        print(matches_in_queue)
        time.sleep(15)
        sleeps_performed += 1