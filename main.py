import json
import platform
import plistlib
import re
import subprocess
import time

import requests


def rev_geocoder(lat, lon):
    rev_geocoder_url = 'https://revgeocode.search.hereapi.com/v1/revgeocode?at={},{}&limit=10&lang=zh-TW&apikey={}'.format(
        lat, lon, api_key)
    r = requests.get(rev_geocoder_url)
    rev_geocoder_result_items = json.loads(r.text).get('items')
    for rev_geocoder_result_item in rev_geocoder_result_items:
        result_type = rev_geocoder_result_item['resultType']
        if result_type == 'houseNumber' or result_type == 'street' or result_type == 'intersection':
            result_position = rev_geocoder_result_item['position']
            result_lat = result_position['lat']
            result_lon = result_position['lng']
            result_title = rev_geocoder_result_item['title']
            return (result_lat, result_lon, result_title)
        else:
            continue


# def rev_geocoder(lat, lon):
#     hls_rev_geocoder_url = 'https://reverse.geocoder.ls.hereapi.com/6.2/reversegeocode.json?prox={},{}&mode=retrieveAddress&maxresults=1&gen=9&apiKey={}'.format(lat, lon, api_key)
#     hls_rev_geocode_r = requests.get(hls_rev_geocoder_url)
#     address = json.loads(hls_rev_geocode_r.text)['Response']['View'][0]['Result'][0]['Location']['Address']['Label']
#     print('Address: {}'.format(address))
#     return address

def mia_cicular_picture(lon, lat, radius, label):
    mia_url = 'https://image.maps.ls.hereapi.com/mia/1.6/mapview?c={},{}&u={}&w=1440&h=900&ml=cht' \
              '&ppi=250&apiKey={}&t=3&tx={},{};{}&txs=30'.format(lat, lon, radius, api_key, lat - 0.00005, lon, label)
    image_data = requests.get(mia_url).content
    timestamp = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
    image_file_name = 'here_network_positioning_result_{}.jpg'.format(timestamp)
    positioning_log.write('{}\t{}\t{}\t{}\n'.format(timestamp, wifi_scan_result, network_positioning_r.text, label))
    with open(image_file_name, 'wb') as handler:
        handler.write(image_data)


api_key = 'kVpNlN_Zq68gCvCKaZGJA8No9l-9nQfWKls02XySZus'  # YOUR HERE API KEY
positioning_headers = {'Content-Type': 'application/json'}
positioning_url = 'https://positioning.hereapi.com/v2/locate?apiKey={}'.format(api_key)
if platform.system() == 'Windows':
    results = subprocess.check_output(["netsh", "wlan", "show", "network", "bssid"])
    results = results.decode("ascii", errors='ignore')  # needed in python 3
    results_list = results.replace('\r', '').replace('    ', '').split('\n\n')
    i = 0
    parsed_result_list = []
    for results in results_list:
        results = results.split('\n')
        for result in results:
            if result.startswith('BSSID') or result.startswith(' Signal'):
                parsed_result_list.append(result.split(' : ')[1].strip())
            else:
                continue
    mac_list = set()
    while i < len(parsed_result_list):
        if i % 2 == 1:
            signal_percentage = int(parsed_result_list[i].replace('%', ''))
            mac_list.add(
                '{"mac": "' + parsed_result_list[i - 1] + '", "rss": ' + str(int((signal_percentage / 2) - 100)) + '}')
        i += 1
elif platform.system() == 'Darwin':
    command = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s -x'  # the shell command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None, shell=True)
    output = process.communicate()
    hotspots_plist = plistlib.loads(str.encode(output[0].decode('utf-8', errors='ignore')), fmt=plistlib.FMT_XML)
    mac_list = set()
    for hotspot in hotspots_plist:
        ssid_str = hotspot['SSID_STR']
        bssid = hotspot['BSSID']
        rssi = hotspot['RSSI']
        if not re.findall('\w\w:\w\w:\w\w:\w\w:\w\w:\w\w', hotspot['BSSID']):
            bssid_arr = bssid.split(':')
            bssid_modified_arr = []
            for bssid_elem in bssid_arr:
                if len(bssid_elem) == 1:
                    bssid_elem = '0{}'.format(bssid_elem)
                bssid_modified_arr.append(bssid_elem)
            bssid = ':'.join(bssid_modified_arr)
        mac_list.add('{\"mac\":\"' + bssid + '\",\"powrx\":' + str(rssi) + '}')  # BSSID + Powrx
wifi_scan_result = '{"wlan":[' + ','.join(i for i in mac_list) + ']}'
print('Wifi hotspots:\n' + wifi_scan_result)
network_positioning_r = requests.post(url=positioning_url, data=wifi_scan_result, headers=positioning_headers)
if network_positioning_r.status_code == 200:
    json_result = json.loads(network_positioning_r.text)
    print('result:\n' + str(json_result))
    lat = json_result['location']['lat']
    lon = json_result['location']['lng']
    positioning_log = open('positioning_result_log.txt', mode='a', encoding='utf-8')
    radius = json_result['location']['accuracy']
    address_lat, address_lon, address_label = rev_geocoder(lat, lon)
    mia_cicular_picture(lon, lat, radius, address_label)
else:
    print(network_positioning_r.text)
