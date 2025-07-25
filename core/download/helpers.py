import logging
import random
import requests
import math
import os
import time
import lxml.html
import urllib3
# SSL Ignore warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FIRST_RUN = True
SOCKS5_PROXY_TXT_API = 'https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/socks5_proxy_list.txt'
HTTPS_PROXY_TXT_API = 'https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/https_proxy_list.txt'
PLATFORM = os.name


def get_proxies(settings):
    '''
    If there are saved proxy settings, apply them override the default proxy settings.
    '''

    if settings:
        r_proxies = requests.get(settings).text.splitlines()
    else:
        '''
        Socks5, https proxy server list in array form
        '''
        r_proxies = get_all_proxies()

    return r_proxies


def get_proxies_from_api(api_url):
    proxy_list = []
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            proxy_list = response.text.splitlines()
    except requests.RequestException as e:
        logging.debug(f"Failed to get proxy list from {api_url}: {e}")
    return proxy_list


def process_proxy_list(proxy_list, proxy_type):
    processed_proxies = []
    for proxy in list(set(proxy_list)):
        proxy_parts = proxy.split(':')
        proxy_without_country = proxy_parts[0] + ':' + proxy_parts[1]

        if proxy.startswith('https://raw.github'):
            raw_proxy_list = requests.get(proxy).text.splitlines()
            unique_proxy_list = list(set(raw_proxy_list))
            for item in unique_proxy_list:
                # Only prepend protocol if not already present
                if not item.startswith('http://') and not item.startswith('https://'):
                    item = f'{proxy_type}://{item}'
                processed_proxies.append({'https': item})
        elif proxy_without_country.startswith(proxy_type):
            processed_proxies.append({'https': proxy_without_country})
        else:
            if not proxy_without_country.startswith('http://') and not proxy_without_country.startswith('https://'):
                proxy_without_country = f'{proxy_type}://{proxy_without_country}'
            processed_proxies.append({'https': proxy_without_country})

    return processed_proxies

def get_all_proxies():
    all_proxies = []

    socks5_proxy_list = get_proxies_from_api(SOCKS5_PROXY_TXT_API) or []
    try:
        with open('socks5_proxy_list.txt', 'r') as f:               # use local file if it exists
            for line in f:
                socks5_proxy_list.append(line.strip())
    except FileNotFoundError:
        logging.warning('socks5_proxy_list.txt not found. Skipping local socks5 proxies.')

    logging.info('socks5_proxy_list: '+ str(len( socks5_proxy_list)))
    all_proxies.extend(process_proxy_list(socks5_proxy_list, 'socks5'))
    logging.info('number of all_proxies available: ' + str(len(all_proxies)))

    https_proxy_list = get_proxies_from_api(HTTPS_PROXY_TXT_API) or []
    try:
        with open('https_proxy_list.txt', 'r') as f:
            for line in f:
                https_proxy_list.append(line.strip())
    except FileNotFoundError:
        logging.warning('https_proxy_list.txt not found. Skipping local https proxies.')

    logging.info('https_proxy_list: '+ str(len(https_proxy_list)))
    all_proxies.extend(process_proxy_list(https_proxy_list, 'http'))
    logging.info('number of all_proxies available: ' + str(len(all_proxies)))

    # Shuffle
    random.shuffle(all_proxies)
    return all_proxies


def convert_size(size_bytes: int) -> str:
    '''
    Convert from bytes to human readable sizes (str).
    '''
    # https://stackoverflow.com/a/14822210
    if size_bytes == 0:
        return '0 B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '%s %s' % (s, size_name[i])


def download_speed(bytes_read: int, start_time: float) -> str:
    '''
    Convert speed to human readable speed (str).
    '''
    if bytes_read == 0:
        return '0 B/s'
    elif time.time()-start_time == 0:
        return '- B/s'
    size_name = ('B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s')
    bps = bytes_read/(time.time()-start_time)
    i = int(math.floor(math.log(bps, 1024)))
    p = math.pow(1024, i)
    s = round(bps / p, 2)
    return '%s %s' % (s, size_name[i])


def get_link_info(url: str, retries: int = 3, delay: int = 1) -> list:
    '''
    Get file name and size with basic retry logic on failure.
    '''
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=10)
            html = lxml.html.fromstring(r.content)

            # If it's a private file (with a password field)
            if html.xpath('//*[@id="pass"]'):
                return ['Private File', '- MB']

            # Fetch the <td> inside the table with class "premium"
            td = html.xpath('//table[@class="premium"]//td[@class="normal"]')[0]
            spans = td.xpath('.//span')
            nome = spans[0].text_content().strip()
            tamanho = spans[1].text_content().strip()
            return [nome, tamanho]

        except requests.exceptions.Timeout:
            logging.warning(f"Timeout on attempt {attempt+1} for {url}")
            time.sleep(delay)
        except Exception as e:
            logging.debug(f"{__name__} Exception: {e}")
            break

    return ['Error', '- MB']



def is_valid_link(url: str) -> bool:
    '''
    Returns True if `url` is a valid 1fichier domain, else it returns False
    '''
    domains = [
        '1fichier.com/',
        'afterupload.com/',
        'cjoint.net/',
        'desfichiers.com/',
        'megadl.fr/',
        'mesfichiers.org/',
        'piecejointe.net/',
        'pjointe.com/',
        'tenvoi.com/',
        'dl4free.com/',
        'ouo.io/',
        'ouo.press/'
    ]

    return any([x in url.lower() for x in domains])
