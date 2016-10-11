#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
keep_cred : receives user credentials during pam auth.
It keeps it until KEEP_CRED_TIMEOUT.
Other applications (extensions) can ask it to do operations that need credentials.

Extensions have to configure themselves with an /usr/local/lib/keep_cred/app.py
They have to implement :
+ FLAG_FILE : the file that flags it's epfl_roaming that sent USR1 signal to keep_cred
+ run(username, password) method that does the job
"""

import os
import sys
import time
import signal
import importlib

KEEP_CRED_TIMEOUT = 20  # sec
EXT_FOLDER = "/usr/local/lib/keep_cred"
EXT_FOLDER = os.path.normpath(os.path.join(__file__, "../../lib/keep_cred")) ## TODO DEBUG

VAR_RUN = "/var/run/keep_cred"


def fork_and_wait():
    def signal_USR1_handler(signum, frame):
        an_ext_was_run = False
        for ext in extensions:
            if os.path.exists(extensions[ext].FLAG_FILE):
                an_ext_was_run = True
                print "Running extension %s." % ext
                extensions[ext].run(USERNAME, PASSWORD)
                try:
                    os.unlink(extensions[ext].FLAG_FILE)
                except:
                    pass
                print "done."
        if not an_ext_was_run:
            print "got USR1 signal, but no extension were run."

    if os.fork() != 0:
        return

    extensions = {}

    # receive SIGUSR1 to trigger operations
    signal.signal(signal.SIGUSR1, signal_USR1_handler)

    sys.path.insert(0, EXT_FOLDER)
    for f in os.listdir(EXT_FOLDER):
        if f == "__init__.py" or not f.endswith(".py"):
            continue
        try:
            ext_name = f[:-3]
            mod = importlib.import_module(ext_name)
            if ("FLAG_FILE" in dir(mod) and "run" in dir(mod) and
                type(mod.FLAG_FILE) == str and callable(mod.run)):
                extensions[ext_name] = mod
            else:
                print "Error, %s doesn't implement required variables and functions; Skipping." % ext_name
        except Exception, e:
            print "Error, could not import %s; Skipping." % ext_name
            print e


    for i in range(KEEP_CRED_TIMEOUT):
        time.sleep(1)
    print "Finished to wait for %i seconds; exiting." % KEEP_CRED_TIMEOUT


if __name__ == "__main__":
    USERNAME = os.environ["PAM_USER"]
    SERVICE = os.environ["PAM_SERVICE"]
    TYPE = os.environ["PAM_TYPE"]

    print "USERNAME %s" % USERNAME
    print "SERVICE %s" % SERVICE
    print "TYPE %s" % TYPE

    if TYPE != "auth":
        sys.exit(0)

    PASSWORD = sys.stdin.readline().rstrip(chr(0))

    try:
        os.makedirs(VAR_RUN)
    except OSError:
        pass

    fork_and_wait()
    sys.exit(0)
