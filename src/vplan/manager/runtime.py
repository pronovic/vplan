# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
The manager service, that maintains state for the system
"""
import argparse
import os.path
import sys
import time

import requests_unixsocket

INTERRUPTED = False
POLL_INTERVAL_SEC = 5


def _parse_command_line() -> str:
    """Parse command line arguments, returning the API endpoint to use."""
    parser = argparse.ArgumentParser("Vacation plan manager")
    parser.add_argument("--local-port", dest="port", type=int, help="Connect to an API on http://localhost:<port>")
    parser.add_argument("--local-socket", dest="socket", type=str, help="Connect to an API on a local UNIX socket")
    args = parser.parse_args(args=sys.argv[1:])
    if args.port:
        endpoint = "http://localhost:%d" % args.port
    elif args.socket:
        if not os.path.exists(args.socket):
            raise ValueError("Socket does not exist: %s" % args.socket)
        requests_unixsocket.monkeypatch()
        endpoint = "http+unix://%s" % args.socket.replace("/", "%2F")
    else:
        raise ValueError("Invalid command line arguments")
    return endpoint


def manager() -> None:
    """Main entrypoint for the vacation plan manager process."""
    endpoint = _parse_command_line()
    print("Running against endpoint: %s" % endpoint)
    while not INTERRUPTED:
        time.sleep(POLL_INTERVAL_SEC)
