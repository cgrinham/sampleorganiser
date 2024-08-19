#!/usr/bin/env python3

"""Play a sound file.

This only reads a certain number of blocks at a time into memory,
therefore it can handle very long files and also files with many
channels.

NumPy and the soundfile module (http://PySoundFile.rtfd.io/) must be
installed for this to work.

"""
import logging
try:
    import queue  # Python 3.x
except ImportError:
    import Queue as queue  # Python 2.x
import sys
import threading
import jack
import soundfile as sf

AUDIO_LOGGER = logging.getLogger('sample_organiser/audio')

BUFFER_SIZE: int = 20
CLIENT_NAME: str = 'sample_organiser'
MANUAL: bool = True  # do not manually connect output ports


CLIENT = jack.Client(CLIENT_NAME)
BLOCKSIZE = CLIENT.blocksize
SAMPLERATE = CLIENT.samplerate

q = queue.Queue(maxsize=BUFFER_SIZE)
event = threading.Event()


def print_error(*args):
    print(*args, file=sys.stderr)


def xrun(delay):
    print_error("An xrun occured, increase JACK's period size?")


def shutdown(status, reason):
    print_error('JACK shutdown!')
    print_error('status:', status)
    print_error('reason:', reason)
    event.set()


def stop_callback(msg=''):
    if msg:
        print_error(msg)
    for port in CLIENT.outports:
        port.get_array().fill(0)
    event.set()
    raise jack.CallbackExit


def process(frames):
    if frames != BLOCKSIZE:
        stop_callback('blocksize must not be changed, I quit!')
    try:
        data = q.get_nowait()
    except queue.Empty:
        stop_callback('Buffer is empty: increase buffersize?')
    if data is None:
        stop_callback()  # Playback is finished
    for channel, port in zip(data.T, CLIENT.outports):
        port.get_array()[:] = channel


def set_up_client():
    CLIENT.set_xrun_callback(xrun)
    CLIENT.set_shutdown_callback(shutdown)
    CLIENT.set_process_callback(process)
    for ch in range(1, 3):
        CLIENT.outports.register(f'out_{ch}')


def connect_ports():
    AUDIO_LOGGER.info("Connect ports")
    target_ports = CLIENT.get_ports(
        is_physical=True, is_input=True, is_audio=True)
    if len(CLIENT.outports) == 1 and len(target_ports) > 1:
        # Connect mono file to stereo output
        CLIENT.outports[0].connect(target_ports[0])
        CLIENT.outports[0].connect(target_ports[1])
    else:
        for source, target in zip(CLIENT.outports, target_ports):
            source.connect(target)


def play_sample(sample):
    AUDIO_LOGGER.info("Play audio with jack")
    try:
        with sf.SoundFile(sample.path) as f:
            block_generator = f.blocks(blocksize=BLOCKSIZE, dtype='float32',
                                       always_2d=True, fill_value=0)
            for _, data in zip(range(BUFFER_SIZE), block_generator):
                q.put_nowait(data)  # Pre-fill queue
            AUDIO_LOGGER.info("Queue filled")
            with CLIENT:
                if not MANUAL:
                    connect_ports()
                timeout = BLOCKSIZE * BUFFER_SIZE / SAMPLERATE
                for data in block_generator:
                    q.put(data, timeout=timeout)
                AUDIO_LOGGER.info("Putting data")
                q.put(None, timeout=timeout)  # Signal end of file
                event.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        AUDIO_LOGGER.warning('Interrupted by user')
    except (queue.Full):
        # A timeout occured, i.e. there was an error in the callback
        AUDIO_LOGGER.warning('A timeout occurred, i.e. there was an error in the callbac')
    except Exception as e:
        AUDIO_LOGGER.warning(type(e).__name__ + ': ' + str(e))
