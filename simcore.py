from __future__ import division
from collections import namedtuple
from pprint import pprint, pformat
from collections import Iterable
from itertools import izip
import datetime
import inspect
import json
import multiprocessing
import os
import Queue
import time
import types
import uuid

import humanize

import channel
import helpers


SampleResult = namedtuple('SampleResult', ['ebn0s', 'bers', 'description', 'frame_length', 'repeat_count'])
SpecimenStatus = namedtuple('SpecimenStatus', ['id', 'status', 'progress', 'current_estimate', 'bers'])


_discrete_time = lambda: int(time.time() * 5)
_minutes_time = lambda: int(time.time()) // 60
_spinner = lambda: "-\|/"[_discrete_time() % 4]


class Specimen(object):
    def samplen(self):
        for ebn0, repeat in izip(self.ebn0s, self.repeat_count):
            self.curr_ebn0 = ebn0

            error_count = 0
            for i in xrange(repeat):
                self.current_frame = i + 1

                error_count += self.sample(ebn0)

                self.current_estimate = error_count / (self.current_frame * self.frame_length)

            p = error_count / (repeat * self.frame_length)
            self.bers.append(p)

            if not p:
                while len(self.bers) < len(self.ebn0s):
                    self.bers.append(0)
                break

        self.set_status("F")

        return SampleResult(
            self.ebn0s,
            self.bers,
            self.description,
            self.frame_length,
            self.repeat_count)

    def sample(self, ebn0):
        data = list(helpers.generate_random(self.frame_length))
        decoded_data = self.transmit(data, ebn0)

        return helpers.hamming_distance(data, decoded_data)

    def transmit(self, data, ebn0):
        self.set_status("N")

        if isinstance(data, types.GeneratorType):
            data = list(data)

        encoded_data = list(self.encoder.encoden(data))
        encoded_data = helpers.modulaten(encoded_data)

        noisy_data = channel.transmit_awgn(encoded_data, ebn0)
        noisy_data = list(noisy_data)

        self.set_status("D")
        decoded_data = self.decode(noisy_data, ebn0)

        return decoded_data

    def set_status(self, state):
        if self.queue:
            self.queue.put(SpecimenStatus(
                self.id,
                state,
                self.get_progress(),
                self.current_estimate,
                self.bers))

    def get_progress(self):
        if self.curr_ebn0 in self.ebn0s:
            i = self.ebn0s.index(self.curr_ebn0)
            total_frames_sent = sum(self.repeat_count[:i]) + self.current_frame
            progress = total_frames_sent / sum(self.repeat_count)
            return int(progress * 100)

        return 0

    def __init__(self, spec_id, frame_length, encoder, decoder_func, ebn0s, repeat_count=1, description="", queue=None):
        self.id = spec_id
        self.description = description

        self.frame_length = frame_length
        self.encoder = encoder
        self.decode = decoder_func

        self.ebn0s = ebn0s
        self.bers = []

        if not isinstance(repeat_count, Iterable):
            self.repeat_count = [repeat_count] * len(ebn0s)
        elif len(repeat_count) == len(ebn0s):
            self.repeat_count = repeat_count
        else:
            raise ValueError(
                "Mismatched lengths of ebn0s ({}) and repeat_count ({})."
                .format(len(ebn0s), len(repeat_count)))

        self.queue = queue
        self.curr_ebn0 = None
        self.current_estimate = 0.0
        self.current_frame = 0
        self.set_status("N")


def create_specimens(configurations, queue=None):
    specimens = []
    for i, config in enumerate(configurations):
        specimens.append(Specimen(i, queue=queue, **config))

    return specimens


def pool_exec(configurations, process_count=6):
    specimens = create_specimens(configurations)

    pool = multiprocessing.Pool(process_count)
    result = pool.map(lambda spec: spec.samplen(), specimens)

    return result


def verbose_exec(configurations, process_count=6):
    print "TURBO SIMCORE"
    print "Running {} specimens:".format(len(configurations))
    for config in configurations:
        print "  - " + config['description']
    print "Number of processes: {}".format(process_count)

    manager = multiprocessing.Manager()
    queue = manager.Queue()

    specimens = create_specimens(configurations, queue)

    pool = multiprocessing.Pool(process_count)

    async_result = pool.map_async(lambda spec: spec.samplen(), specimens)

    log = create_log()
    log.write(pformat(configurations) + "\n" * 2)

    print time.strftime("Started %H:%M:%S\n")
    start_time = time.time()

    display_stats(log, queue, async_result, start_time)

    time_elapsed = time.time() - start_time
    print time.strftime("\nFinished %H:%M:%S")
    print "Time elapsed: {}\n".format(humanize.time.naturaldelta(time_elapsed))

    results = async_result.get()

    [pprint(dict(item._asdict())) for item in results]

    info = {
        "date": datetime.datetime.isoformat(datetime.datetime.now()),
        "time_elapsed": time_elapsed,
        "specimens": len(specimens),
        "processes": process_count,
        "log_file": log.name,
    }
    out_file = save_results(info, results)
    print "\nFile saved:", out_file

    close_log(log, results)

    return results


def display_stats(log, queue, async_result, start_time):
    stats = {}
    timer = _discrete_time()
    timer_mins = _minutes_time()
    time_elapsed = lambda: time.time() - start_time

    while not async_result.ready():
        try:
            status = queue.get_nowait()
            stats[status.id] = status

        except Queue.Empty:
            pass

        if timer != _discrete_time():
            print_stats(stats, time_elapsed())
        timer = _discrete_time()

        if timer_mins != _minutes_time():
            log_stats(log, stats)
        timer_mins = _minutes_time()

    print_stats(stats, time_elapsed())
    print


def print_stats(stats, time_elapsed):
    print '\r[{}] {:<10}'.format(_spinner(), humanize.time.naturaldelta(time_elapsed)),
    for spec_id, status in stats.items():
        print "[{:<2}{}{:>4}% {:<.6f}]".format(
            spec_id,
            status.status,
            status.progress,
            status.current_estimate),


def save_results(info, results):
    data = dict(info)
    data["results"] = [item._asdict() for item in results]
    data = json.dumps(data)

    out_folder = os.path.abspath("out")
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    out_file = os.path.basename(inspect.stack()[2][1])[:-3]
    out_file = "{}_{}.json".format(
        hex(len(os.listdir(out_folder)))[2:],
        out_file)
    out_file = os.path.join(out_folder, out_file)

    with open(out_file, 'w') as f:
        f.write(data)

    return out_file


def create_log():
    logs_folder = os.path.abspath("logs")
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)

    log_uuid = str(uuid.uuid4())
    log_file = os.path.join(logs_folder, "{}.log".format(log_uuid))

    log_file = open(log_file, "a")
    log_file.write("{}\n".format(_iso_time()))

    print "Log created:", log_file.name

    return log_file


def close_log(log, results):
    log.write("\n\n{}\n".format(_iso_time()))
    log.write(pformat(results))

    log.close()


def log_stats(log, stats):
    log.write("[{}] {}\n".format(_iso_time(), stats))


def _iso_time():
    return datetime.datetime.isoformat(datetime.datetime.now())
