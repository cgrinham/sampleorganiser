import playsound
import threading
import time


DIR = '/home/christie/Sync/Programming/Projects/sampleorganiser/samples'

KICK = f'{DIR}/musicradar-drum-samples/Assorted Hits/Kicks/Acoustic/CYCdh_AcouKick-01.wav'
HH = f'{DIR}/musicradar-drum-samples/Assorted Hits/Hi Hats/Acoustic/Acoustic Hat-01.wav'
SNARE = f'{DIR}/musicradar-drum-samples/Assorted Hits/Snares/Acoustic/Acoustic Snare-01.wav'


SEQ = [
    [KICK,  None,   None,   None],
    [None,  None,   SNARE,  None],
    [HH,    HH,     HH,     HH],
]


def play_sample_handler(sample):
    playsound.playsound(sample)


def play_sample(sample, wait=False):
    if wait:
        play_sample_handler(sample)
    else:
        threading.Thread(target=play_sample_handler, args=(sample,)).start()


def transform_sequence():
    beats = []
    for row in SEQ:
        for beat, sample in enumerate(row):
            try:
                beats[0].append(sample)
            except IndexError:
                beats.append([sample])
    return beats


def play_sequence():
    seq = transform_sequence()
    for beat in seq:
        for sample in beat:
            play_sample(beat)
        time.sleep(0.5)
