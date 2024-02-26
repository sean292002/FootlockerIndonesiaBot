from cgitb import text
from os import get_inheritable
from pickle import NONE
import requests
import discord
from discord_webhook import DiscordWebhook, DiscordEmbed
from requests.models import Response
from requests.sessions import session
import csv
import time
from bs4 import BeautifulSoup
import random
import json
import colorama
from colorama import Fore
import logging
import threading
import time
import random
import string
from footlocker import Footlocker
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
colorama.init(autoreset=True)
from logger import *

def nonblank_lines(filename):
    with open(filename) as f:
        stripped_lines = [line.strip() for line in f]
        return [line for line in stripped_lines if line]

def load_proxies_from_file(filename, shuffle=True):
    proxies = nonblank_lines(filename)

    if len(proxies) >0 :
        proxy = random.choice(proxies)
        if proxy:
            (IPv4, Port, username, password) = proxy.split(':')
            ip = IPv4 + ':' + Port
            new_proxies = {
                "http": "http://" + username + ":" + password + "@" + ip,
                "https": "http://" + username + ":" + password + "@" + ip,
            }
        else:
            new_proxies = proxy
    else:
        proxy = "Local Host"
        new_proxies = None
    return new_proxies,proxy
    
def ftl_bot(ftl_instance):
    while True:
        proxy_file = 'proxies.txt'
        new_proxies,proxy = load_proxies_from_file(proxy_file, shuffle=True)
        try:
            ftl_instance.check_if_404(new_proxies) 
            if ftl_instance.product_status_404 == False:
                ftl_instance.get_footlocker_product_id(new_proxies)
                ftl_instance.pre_select_size()
                ftl_instance.login_formkey(new_proxies)
                if ftl_instance.loginformkey:
                    ftl_instance.login(new_proxies)
                    ftl_instance.get_address(new_proxies)
                    # ftl_instance.account.display()
                    ftl_instance.get_cart_id(new_proxies)
                    ftl_instance.atc_form_key(new_proxies)
                    ftl_instance.atc(new_proxies)
                    ftl_instance.cart_check()
                    ftl_instance.total(new_proxies)
                    ftl_instance.submit_shipping(new_proxies)
                    ftl_instance.total(new_proxies)
                    ftl_instance.total_pay(new_proxies)
                    try:
                        ftl_instance.checkout_virtual_account(new_proxies)
                    except requests.exceptions.ProxyError:
                        Logger.info("Submitted checkout - Proxy error for some reason")
                    finally:
                        try:
                            ftl_instance.get_va_code(new_proxies)
                        except Exception as e:
                            Logger.warning(f'{str(e)}')
                        finally:
                            ftl_instance.send_webhook()
                    break
        except Exception as e:
            Logger.warning(f'{str(e)}')
            time.sleep(1)
            continue

def main():
    threads = []
    with open('ftltasks.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        header = next(csv_reader)  # Skip the header
        for line in csv_reader:
            product_link, email, password, payment, cc_number, cc_month, cc_year, cc_cvv = line[:8]
            ftl_instance = Footlocker(product_link, email, password, payment, cc_number, cc_month, cc_year, cc_cvv)
            t = threading.Thread(target=ftl_bot, args=(ftl_instance,))
            threads.append(t)
            t.start()
    
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()