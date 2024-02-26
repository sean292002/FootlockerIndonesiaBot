from datetime import datetime
import threading
from threading import *

screen_lock = Semaphore(value=1) 



RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
GREEN = "\033[92m"
ORANGE = '\033[33m'
PURPLE = '\033[35m'


class Logger:
    def getTime():
        return datetime.now().strftime("%H:%M:%S")

    def threadname():
        return str(threading.current_thread().getName())

    def info(reason):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {BLUE}{reason}{RESET}")
        screen_lock.release()
        pass

    def warning(reason):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {ORANGE}{reason}{RESET}")
        screen_lock.release()
        pass

    def error(reason):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {RED}{reason}{RESET}")
        screen_lock.release()
        pass

    def success(message):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {GREEN}{message}{RESET}")
        screen_lock.release()
        pass

    def debug(message):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {ORANGE}{message}{RESET}")
        screen_lock.release()
        pass

    def cloudflare(message):
        screen_lock.acquire()
        print(f"[{Logger.getTime()}] [{Logger.threadname()}] {PURPLE}{message}{RESET}")
        screen_lock.release()
        pass