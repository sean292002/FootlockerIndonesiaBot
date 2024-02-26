from cgitb import text
from distutils.command import check
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

class Footlocker:
    class Account:
        def __init__(self, firstname, lastname, address, city, region, postcode, phone, address_id):
            self.firstname = firstname
            self.lastname = lastname
            self.address = address
            self.city = city
            self.region = region
            self.postcode = postcode
            self.phone = phone
            self.address_id = address_id
            self.regionID = '755'
            self.regionCode = 'ID-JK'
            self.customer_id = None
        
        def display(self):
            print(f"Name: {self.firstname} {self.lastname}")
            print(f"Address: {self.address}")
            print(f"City: {self.city}, {self.region} {self.postcode}")
            print(f"Phone: {self.phone}")
            print(f"Address ID: {self.address_id}")
            print(f"Customer ID: {self.customer_id}")
    
    class Webhook:
        def __init__(self):
            self.product = 'Place Holder'
            self.sku = 'Place Holder'
            self.price = 'Place Holder'
            self.order_number = 'Place Holder'
            self.email = 'Place Holder'
            self.va_code = 'Place Holder'
            self.payment = 'Virtual Account'
            self.version = '0.0.1'
            self.mode = 'Footlocker Indonesia ACO'
            self.productimageurl = None
        
        

    software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value] 

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)

    def __init__(self, product_link, email, password, payment, cc_number, cc_month, cc_year, cc_cvv):
        self.product_link = product_link
        self.email = email
        self.password = password
        self.payment = payment
        self.cc_number = cc_number
        self.cc_month = cc_month
        self.cc_year = cc_year
        self.cc_cvv = cc_cvv
        self.session = requests.session()
        self.user_agent = Footlocker.user_agent_rotator.get_random_user_agent()
        self.product_status_404 = None
        self.footlocker_product_id = None
        self.size_footlocker = None
        self.us_size_final = None
        self.loginformkey = None
        self.atc_formkey = None
        self.cart_response = None
        self.cart_id = None
        self.va_code = None


    def check_if_404(self,new_proxies):
        headers = {
            'User-Agent': self.user_agent
        }
        html_content = self.session.get(self.product_link,headers=headers,proxies=new_proxies)
        #print(html_content)
        soup_product_size = BeautifulSoup(html_content.text, 'html.parser')
        product_details = soup_product_size.find_all('title')[0].text.strip() #Get Product Image and Name 
        if '404' not in product_details: #Not 404
            self.product_status_404 = False #Able to see product
        else:
            self.product_status_404 = True
        return

    def get_footlocker_product_id(self,new_proxies):
        headers = {
            'User-Agent': self.user_agent
        }
        html_content = self.session.get(self.product_link,headers=headers,proxies=new_proxies)
        banner_content_html = BeautifulSoup(html_content.text, 'html.parser')
        banner_items = banner_content_html.find('div', {"class": "product-add-form"})
        formkey_hidden = banner_items.find_all('input', {'type':'hidden'})[0]
        footlocker_product_id = formkey_hidden['value']
        self.footlocker_product_id = footlocker_product_id
        return

    def pre_select_size(self):
        size_dict_all = {
                'US 3.5Y': '368', 'US 4Y': '352', 'US 4.5Y': '364', 'US 5Y': '363', 'US 5.5Y': '365',
                'US 6Y': '354', 'US 6.5Y': '355', 'US 7Y': '367', 'US 6': '65', 'US 6.5': '141',
                'US 7': '112', 'US 7.5': '180', 'US 8': '66', 'US 8.5': '181', 'US 9': '67',
                'US 9.5': '177', 'US 10': '68', 'US 10.5': '76', 'US 11': '69', 'US 12': '74'
            }
            
        # Reverse the dictionary to map IDs back to US sizes
        size_dict_reversed = {value: key for key, value in size_dict_all.items()}
        # Choose a size based on the product URL
        if 'men' or 'unisex' in self.product_link:
            applicable_sizes = {k: v for k, v in size_dict_all.items() if not 'Y' in k}
        elif 'grade' in self.product_link:
            applicable_sizes = {k: v for k, v in size_dict_all.items() if 'Y' in k}
        else:
            applicable_sizes = size_dict_all

        size_id_final = random.choice(list(applicable_sizes.values()))
        us_size_final = size_dict_reversed[size_id_final]
        logging.info(f"Got Size = {us_size_final}")
        self.size_footlocker = size_id_final
        self.us_size_final = us_size_final
        return 
    
    def login_formkey(self,new_proxies):
        cart_homepage_url = 'https://www.footlocker.id/checkout/cart/'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        #Get Form Key
        cart_html_content = self.session.get(cart_homepage_url,headers=headers,proxies=new_proxies)
        soup = BeautifulSoup(cart_html_content.text, 'html.parser')
        formkey_hidden = soup.find_all('input', {'type':'hidden'})[0]
        loginformkey = formkey_hidden['value']
        Logger.success(f"Successfully got login auth key")
        self.loginformkey = loginformkey
        return  

    def login(self,new_proxies):
        url = 'https://www.footlocker.id/customer/account/loginPost/referer/aHR0cHM6Ly93d3cuZm9vdGxvY2tlci5pZC8%2C/'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        }
        query = {
            "form_key": self.loginformkey,
            "login[username]": self.email,
            "login[password]": self.password,
            "send": ""
        }
        response = self.session.post(url,data=query,headers=headers,proxies=new_proxies)
        if response.status_code == 200:
            Logger.info(f"Successfully Logged In")
        else:
            Logger.error(f"Error Logging In")
        return 

    def get_address(self,new_proxies):
        cart_homepage_url = 'https://www.footlocker.id/customer/account/'
        headers = {
            'User-Agent': self.user_agent
        }
        #Get Form Key
        cart_html_content = self.session.get(cart_homepage_url,headers=headers,proxies=new_proxies)
        soup = BeautifulSoup(cart_html_content.text, 'html.parser')
        shipping_address_box = soup.find('div', class_='box-shipping-address')
        shipping_address = shipping_address_box.find('address').get_text(separator="\n").strip()
        lines = shipping_address.split('\n')
        edit_link = shipping_address_box.find('div', class_='box-actions').find('a', class_='action edit')['href']
        address_id = edit_link.split('/id/')[1].split('/')[0]
        filtered_lines = [line for line in lines if line.strip() and line not in ['\r', 'Indonesia', 'T:  62 ']]
        names = filtered_lines[0].split()
        firstname = names[0]
        lastname = ' '.join(names[1:])
        address = filtered_lines[2].strip()
        city,region,postcode = [x.strip() for x in filtered_lines[2].split(',')]
        phone = filtered_lines[-1]
        self.account = Footlocker.Account(firstname, lastname, address, city, region, postcode, phone,address_id)
        return 
    
    def atc_form_key(self,new_proxies):
        cart_homepage_url = self.product_link
        headers = {
            'User-Agent': self.user_agent
        }
        #Get Form Key
        cart_html_content = self.session.get(cart_homepage_url,headers=headers,proxies=new_proxies)
        soup = BeautifulSoup(cart_html_content.text, 'html.parser')
        formkey_hidden = soup.find_all('input', {'type':'hidden'})[0]
        #print(formkey_hidden)
        atc_formkey = formkey_hidden['value']
        Logger.success(f"Successfully got auth key - {atc_formkey}")
        self.atc_formkey = atc_formkey
        return 
    
    def atc(self,new_proxies):
        #Add Product to Cart
        headers = {
            'User-Agent': self.user_agent,
            # 'Accept':'application/json, text/javascript, */*; q=0.01',
            # 'Accept-Encoding':'gzip, deflate, br',
            # 'Accept-Language':'en-US,en;q=0.5',
            'Content-Type':'multipart/form-data',
            'X-Requested-With':'XMLHttpRequest',
            'Origin':'https://www.footlocker.id',
            'Referer': self.product_link,
            # 'Cookie' : f'form_key:{self.atc_formkey}'
            
        }
        # print(self.footlocker_product_id)
        add_to_cart_url = f'https://www.footlocker.id/checkout/cart/add/uenc/aHR0cHM6Ly93d3cuZm9vdGxvY2tlci5pZC9hc2ljcy1qYXBhbi1zLXN0LXN0YW5kYXJkLXVuaXNleC1zLXNuZWFrZXJzLXNob2VzLWJsYWNrLTE2Lmh0bWw%2C/product/{self.footlocker_product_id}/'
        # print(add_to_cart_url)
        query = {
            'product': int(self.footlocker_product_id),
            'selected_configurable_option': '',
            'related_product':'',
            'item': int(self.footlocker_product_id),
            'form_key': self.atc_formkey,
            'super_attribute[182]':int(self.size_footlocker),
            'qty': 1
        }
        # print(self.atc_formkey)
        # print(self.us_size_final)
        # print(self.size_footlocker)
        # print(self.session.cookies)
        atc = self.session.post(add_to_cart_url,data=query,headers=headers,proxies=new_proxies)
        # print(atc)
        headers2 = {
            'User-Agent': self.user_agent,
            'X-Requested-With':'XMLHttpRequest'
        }
        cart_check_url= f'https://www.footlocker.id/customer/section/load/?sections=cart&force_new_section_timestamp=True&_={int(time.time())}'
        cart_response = self.session.get(cart_check_url,headers=headers2,proxies=new_proxies).json()
        # print(cart_response)
        self.cart_response = cart_response
        cart_total = cart_response['cart']['summary_count']
        return atc,cart_response,cart_total

    def cart_check(self):
        self.webhook = Footlocker.Webhook()
        Logger.success(f"Successfully Added To Cart")
        self.size = self.cart_response['cart']['items'][0]['options'][0]['value']
        # product_url = self.cart_response['cart']['items'][0]['product_url']
        self.webhook.price = str(self.cart_response['cart']['items'][0]['product_price_value']) + ' IDR'
        self.webhook.sku = self.cart_response['cart']['items'][0]['product_sku']
        self.webhook.productimageurl = self.cart_response['cart']['items'][0]['product_image']['src']
        self.webhook.product = self.cart_response['cart']['items'][0]['product_image']['alt'].upper()
        
    
    def cart_check_total(self,new_proxies):
        #Step 1 of checkout
        headers = {
            'User-Agent': self.user_agent,
            'X-Requested-With':'XMLHttpRequest'
        }
        cart_check_url = 'https://www.footlocker.id/rest/idn/V1/carts/mine/totals'
        cart_response = self.session.get(cart_check_url,headers=headers,proxies=new_proxies).json()
        # print(cart_response)
        Logger.success(f"Successfully check cart total")
        return 

    def get_cart_id(self,new_proxies):
        #Get CART ID, to post to ensure success
        headers = {
            'User-Agent': self.user_agent,
            'X-Requested-With': 'XMLHttpRequest'
        }   
        cart_id_url = 'https://www.footlocker.id/reclaim/checkout/email'
        query = {
            "email": self.email
        }
        cart_id_content = self.session.post(cart_id_url,headers=headers,data=query,proxies=new_proxies)
        cart_id_content_json = cart_id_content.json()
        cart_id = cart_id_content_json["success"]['entity_id']
        customer_id = cart_id_content_json["success"]['customer_id']
        Logger.success(f"Successfully Got Cart ID - {cart_id}")
        self.cart_id = cart_id
        self.account.customer_id = customer_id
        return 
    
    def total(self,new_proxies):
        #submit total after clicking checkount and setting shipping
        Submit_shipping_link = 'https://www.footlocker.id/rest/idn/V1/carts/mine/totals-information'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        Submit_shipping_query = {
            "addressInformation": {
                "address": {
                    "city": self.account.city,
                    "countryId": "ID",
                    "extension_attributes": {
                        "advanced_conditions": {
                            "billing_address_country": None,
                            "city": self.account.city,
                            "currency": "IDR",
                            "payment_method": None,
                            "shipping_address_line": [
                                self.account.address
                            ]
                        }
                    },
                    "postcode": self.account.postcode,
                    "region": self.account.region,
                    "regionId": self.account.regionID
                },
                "shipping_carrier_code": "advancerate",
                "shipping_method_code": "advancedmatrix0"
            }
        }
        submit_shipping = self.session.post(Submit_shipping_link,headers=headers,json=Submit_shipping_query,proxies=new_proxies)
        # print(submit_shipping)
        # print(submit_shipping.text)
        #print(submit_shipping.json())
        Logger.success(f"Successfully Submitted Totals Info")

    def submit_shipping(self,new_proxies):
        #submit Shipping
        Submit_shipping_link = 'https://www.footlocker.id/rest/idn/V1/carts/mine/shipping-information'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        Submit_shipping_query = {
            "addressInformation": {
                "billing_address": {
                    "city": self.account.city,
                    "countryId": "ID",
                    "extension_attributes": {},
                    "firstname": self.account.firstname,
                    "lastname": self.account.lastname,
                    "postcode": self.account.postcode,
                    "region": self.account.region,
                    "regionCode": self.account.regionCode,
                    "regionId": self.account.regionID,
                    "saveInAddressBook": None,
                    "street": [
                        self.account.address
                    ],
                    "telephone": self.account.phone
                },
                "extension_attributes": {
                    "is_pickup": False,
                    "pickup_customer_firstname": "",
                    "pickup_customer_lastname": "",
                    "pickup_customer_phone": "",
                    "pickup_store": ""
                },
                "shipping_address": {
                    "city":self.account.city,
                    "countryId": "ID",
                    "extension_attributes": {},
                    "firstname": self.account.firstname,
                    "lastname": self.account.lastname,
                    "postcode": self.account.postcode,
                    "region": self.account.region,
                    "regionCode": self.account.regionCode,
                    "regionId": self.account.regionID,
                    "street": [
                        self.account.address
                    ],
                    "telephone": self.account.phone
                },
                "shipping_carrier_code": "advancerate",
                "shipping_method_code": "advancedmatrix0"
            }
        }
        submit_shipping = self.session.post(Submit_shipping_link,headers=headers,json=Submit_shipping_query,proxies=new_proxies)
        # print(submit_shipping)
        # print(submit_shipping.text)
        Logger.success(f"Successfully Submitted Shipping Info")
        return
    
    def total_pay(self,new_proxies):
        #submit total
        Submit_shipping_link = 'https://www.footlocker.id/rest/idn/V1/carts/mine/totals-information'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        Submit_shipping_query = {
            "addressInformation": {
                "address": {
                    "city": self.account.city,
                    "countryId": "ID",
                    "extension_attributes": {
                        "advanced_conditions": {
                            "billing_address_country": None,
                            "city": self.account.city,
                            "currency": "IDR",
                            "payment_method": "midtransbca",
                            "shipping_address_line": [
                                self.account.address
                            ]
                        }
                    },
                    "postcode": self.account.postcode,
                    "region": self.account.region,
                    "regionId": self.account.regionID
                },
                "shipping_carrier_code": "advancerate",
                "shipping_method_code": "advancedmatrix0"
            }
        }
        submit_shipping = self.session.post(Submit_shipping_link,headers=headers,json=Submit_shipping_query,proxies=new_proxies)
        # print(submit_shipping)
        Logger.success(f"Successfully Submitted Totals Pay Info")
    
    def checkout_virtual_account(self,new_proxies):
        #Checkout
        submit_checkout_url = 'https://www.footlocker.id/rest/idn/V1/carts/mine/payment-information'
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            # 'Alt-Used':'www.footlocker.id',
            # 'Accept':'*/*',
            # 'Accept-Encoding':'gzip,deflate,br',
            # 'Accept-Language':'en-US,en;q=0.5',
            # 'Origin':'https://www.footlocker.id',
            # 'Referer':'https://www.footlocker.id/checkout/'
        }
        submit_checkout_query = {
                "cartId": self.cart_id,
                "billingAddress": {
                    "customerAddressId": self.account.address_id,
                    "countryId": "ID",
                    "regionId": self.account.regionID,
                    "regionCode": self.account.regionCode,
                    "region": self.account.region,
                    "customerId": self.account.customer_id,
                    "street": [
                        self.account.address
                    ],
                    "company": None,
                    "telephone": self.account.phone,
                    "fax": None,
                    "postcode": self.account.postcode,
                    "city": self.account.city,
                    "firstname": self.account.firstname,
                    "lastname": self.account.lastname,
                    "middlename": None,
                    "prefix": None,
                    "suffix": None,
                    "vatId": None,
                    "customAttributes": []
                },
                "paymentMethod": {
                    "method": "midtransbca",
                    "po_number": None,
                    "additional_data": {
                        "amgdpr_agreement": "{}"
                    },
                    "extension_attributes": {
                        "comment": ""
                    }
                }
            }
        Logger.info(f'Submitting Checkout')
        checkout = self.session.post(submit_checkout_url,headers=headers,json=submit_checkout_query,proxies=new_proxies)
        # print(checkout)
        # print(checkout.text)
        data_checkout = checkout.json()
        #print(data_checkout)
        return data_checkout

    def get_va_code(self,new_proxies):
        headers = {
            'User-Agent': self.user_agent
        }
        #Checkout
        Logger.info(f'Getting Va Code')
        va_url = 'https://www.footlocker.id/checkout/onepage/success/'
        va_data = self.session.get(va_url,headers=headers,proxies=new_proxies)
        soup = BeautifulSoup(va_data.text, 'html.parser')
        bca_va_code = soup.find('span', {'class':'success-payment-code'})
        va_code_payment = bca_va_code.text.strip()
        # print(va_code_payments)
        self.va_code = va_code_payment
        return
    
    def send_webhook(self):
        # print(self.product_link,self.webhook.product,self.webhook.sku,self.webhook.size,self.webhook.price,self.email,self.va_code,self.webhook.payment,self.webhook.version,self.webhook.mode,self.webhook.productimageurl)
        webhook = DiscordWebhook(url='')
        embed = DiscordEmbed(title='Footlocker ID', description='Successfully Checked Out', color='2ECC71',url= self.product_link)
        embed.set_timestamp()
        embed.add_embed_field(name='Product', value=self.webhook.product)
        embed.add_embed_field(name='SKU', value=self.webhook.sku)
        embed.add_embed_field(name='Size', value=self.us_size_final)
        embed.add_embed_field(name='Price', value=self.webhook.price)
        embed.add_embed_field(name='Email', value=self.email)
        embed.add_embed_field(name='VA Code', value=self.va_code)
        embed.add_embed_field(name='Payment Method', value=self.webhook.payment)
        embed.add_embed_field(name='Version', value=self.webhook.version)
        embed.add_embed_field(name='Mode', value=self.webhook.mode)
        embed.set_thumbnail(url=self.webhook.productimageurl)
        embed.set_footer(text='@Powered by Sean292002',icon_url='')
        webhook.add_embed(embed)
        response = webhook.execute()
        Logger.success(f"Checkout Webhook Successfully Sent")