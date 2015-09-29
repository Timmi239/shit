#!/usr/bin/env python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import argparse
from collections import deque
import os


BYTE_OFFSET = 32


class MyHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.file = open(file_path, 'rb')
        self.file.seek(0, os.SEEK_END)
        super(MyHandler, self).__init__()

    def on_modified(self, event):
        if type(event) == FileModifiedEvent and not str(event.src_path).endswith('___jb_bak___'):
            print "".join(self.file.readlines())


def main():
    args = parse_args().__dict__
    if args['lines']:
        print get_last_strings_offset_file(args['lines'], args['filename'])
    if args['use_descriptor']:
        path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(path, args['filename'])
        event_handler = MyHandler(file_path)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(path), recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--follow", dest="use_descriptor", action='store_true')
    parser.add_argument("-n", "--lines", dest="lines", type=int)
    parser.add_argument('filename', type=str)
    return parser.parse_args()


def get_last_strings_deque(count, filename):
    with open(filename, 'rb') as f:
        last_strings = deque(f, count)
    return "".join(i for i in last_strings)


def get_last_strings_offset_file(count, filename):
    f = open(filename, 'rb')
    current_offset = BYTE_OFFSET
    f.seek(-current_offset, os.SEEK_END)
    while True:
        read_lines = f.readlines()
        if len(read_lines) < count + 1:
            current_offset += BYTE_OFFSET
        else:
            f.close()
            return "".join(read_lines[-count:])
        f.seek(-current_offset, os.SEEK_END)


if __name__ == "__main__":
    main()
