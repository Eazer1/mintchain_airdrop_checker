import random
import requests
import json
import threading

from loguru import logger
from time import sleep
from threading import Thread
from eth_account.signers.local import LocalAccount
from eth_account import Account
from web3.auto import w3
from eth_account.messages import encode_defunct

from better_proxy import Proxy
proxy_list = Proxy.from_file('proxies.txt')
def get_random_proxy():
    
    proxy = (random.choice(proxy_list)).as_proxies_dict
    return proxy

def sign_message(prkey):
    main_acc: LocalAccount = Account.from_key(prkey)

    nonce = random.randint(1000000, 9999999)

    msg = f'''You are participating in the Mint Airdrop event: 
 {main_acc.address} 
 Nonce: {nonce}'''
    
    message = encode_defunct(text=msg)
    signed_message = w3.eth.account.sign_message(message, private_key=prkey)
    signed_message = signed_message.signature.hex()

    return signed_message, msg, nonce

def check_eligble(prkey, signed_message, msg, nonce):
    main_acc: LocalAccount = Account.from_key(prkey)
    
    url = f'https://airdropapi.mintchain.io/api/airdrop/verifyEligibility?address={main_acc.address}&signature={signed_message}&message=You+are+participating+in+the+Mint+Airdrop+event:+%0A+{main_acc.address}+%0A+Nonce:+{nonce}'

    headers = {
        'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'referer':'https://www.mintchain.io/',
        'origin':'https://www.mintchain.io',
    }

    while True:
        try:
            resp = requests.get(url, headers=headers, proxies=get_random_proxy())
            #print(resp.status_code)
            #print(resp.text)
            if resp.status_code == 200 or resp.status_code == 201:
                if resp.text == '': 
                    return None
                
                data = json.loads(resp.text)
                
                totalAirdrop = data['data']['totalAirdrop']
                return totalAirdrop
            
            sleep(5)
        except Exception as e:
            logger.error(f'[{main_acc.address}][check_eligble] Error: {e}')
            sleep(5)

def start(prkey):
    main_acc: LocalAccount = Account.from_key(prkey)

    signed_message, msg, nonce = sign_message(prkey)
    totalAirdrop = check_eligble(prkey, signed_message, msg, nonce)

    if float(totalAirdrop) == 0:
       logger.info(f'[{main_acc.address}] Not Eligible')

    else:
        logger.success(f'[{main_acc.address}] {float(totalAirdrop)}')
        with open(f'Eligible.txt', 'a', encoding='utf-8') as f:
            f.write(f'{prkey};{main_acc.address};{totalAirdrop}\n')

THREADS = int(input(f'Введите кол-во потоков: ')) + 1

file_name = 'wallets'
accs_list = open(file_name + '.txt', 'r').read().splitlines()

for el in accs_list:
    splited_data = el.split(';')
    prkey = splited_data[0]

    while threading.active_count() >= THREADS:
        sleep(1)

    Thread(target=start, args=(prkey, )).start()
    sleep(0.01)
