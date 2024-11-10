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
    process_inner_proxy = []
    for proxy in list(set(proxy_list)):
        proxy_parts = proxy.split(':')
        proxy_without_country = proxy_parts[0] + ':' + proxy_parts[1]

        if proxy.startswith('https://raw.github'):
            raw_proxy_list = requests.get(proxy).text.splitlines()
            count = 0
            for item in raw_proxy_list:
                if item.startswith('socks5://'):
                    item = item[9:]
                if item.startswith('http://'):
                    item = item[7:]
                process_inner_proxy.append(item)
                count += 1
            logging.info('number of proxies loaded from url: '+ str( count))

    # Remove any possible duplicates
    unique_proxy_list = list(set(process_inner_proxy))
    for item in unique_proxy_list:
        processed_proxies.append({'https': f'{proxy_type}://{item}'})

    # Deduplication of proxy servers
    return processed_proxies


def get_all_proxies():
    all_proxies = []

    socks5_proxy_list = get_proxies_from_api(SOCKS5_PROXY_TXT_API)  # fetch list from web, comment this one for only local
    # socks5_proxy_list = []                                        # uncomment this one for only local
    f = open( 'socks5_proxy_list.txt', 'r')                         # use local file
    for line in f:
        socks5_proxy_list.append(line.rstrip('\r\n'))
    f.close()
    logging.info('socks5_proxy_list: '+ str(len( socks5_proxy_list)))
    all_proxies.extend(process_proxy_list(socks5_proxy_list, 'socks5'))
    logging.info('number of all_proxies available: '+ str( len( all_proxies)))
    
    https_proxy_list = get_proxies_from_api(HTTPS_PROXY_TXT_API)    # fetch list from web, comment this one for only local
    # https_proxy_list = []                                         # uncomment this one for only local
    f = open( 'https_proxy_list.txt', 'r')                          # use local file
    for line in f:
        https_proxy_list.append(line.rstrip('\r\n'))
    f.close()
    logging.info('https_proxy_list: '+ str(len(https_proxy_list)))
    all_proxies.extend(process_proxy_list(https_proxy_list, 'http'))
    logging.info('number of all_proxies available: '+ str(len(all_proxies)))

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


def get_link_info(url: str) -> list:
    '''
    Get file name and size. 
    '''
    try:
        r = requests.get(url)
        html = lxml.html.fromstring(r.content)
        if html.xpath('//*[@id="pass"]'):
            return ['Private File', '- MB']
        name = html.xpath('//td[@class=\'normal\']')[0].text
        size = html.xpath('//td[@class=\'normal\']')[2].text
        r.close()
        return [name, size]
    except:
        logging.debug(__name__+' Exception')
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
