#!/usr/bin/env python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
import argparse


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if type(event) == FileModifiedEvent and not str(event.src_path).endswith('___jb_bak___'):
            print "Got it!"


def main():
    parse_args()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--follow", dest="use_descriptor", action='store_true')
    parser.add_argument("-n", "--lines", dest="lines", type=int)
    parser.add_argument('filename', type=str)
    return parser.parse_args()

if __name__ == "__main__":
    main()
    # event_handler = MyHandler()
    # observer = Observer()
    # observer.schedule(event_handler, path='.', recursive=False)
    # observer.start()
    #
    # try:
    #     while True:
    #         time.sleep(5)
    # except KeyboardInterrupt:
    #     observer.stop()
    # observer.join()