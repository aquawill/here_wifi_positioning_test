import json
import os
import platform
import plistlib
import re
import subprocess
import requests
import time


def rev_geocoder(lat, lon):
    rev_geocoder_url = 'https://revgeocode.search.hereapi.com/v1/revgeocode?at={},{}&limit=1&lang=zh-TW&apikey={}'.format(
        lat,
        lon, api_key)
    r = requests.get(rev_geocoder_url)
    result_title = json.loads(r.text).get('items')[0].get('title')
    print('Address: {}'.format(result_title))
    return result_title


def mia_cicular_picture(lon, lat, radius, label):
    mia_url = 'https://image.maps.ls.hereapi.com/mia/1.6/mapview?c={},{}&u={}&w=1440&h=900&ml=cht' \
              '&ppi=250&apiKey={}&t=3&tx={},{};{}&txs=30'.format(lat, lon, radius, api_key, lat - 0.00005, lon, label)
    image_data = requests.get(mia_url).content
    image_file_name = 'here_network_positioning_result_{}.jpg'.format(
        time.strftime('%d_%b_%Y_%H:%M:%S', time.localtime(time.time())))
    with open(image_file_name, 'wb') as handler:
        handler.write(image_data)


api_key = ''  # YOUR HERE API KEY
positioning_headers = {'Content-Type': 'application/json'}
positioning_url = 'https://pos.ls.hereapi.com/positioning/v1/locate?apiKey={}'.format(api_key)
rev_geocoder_url = 'https://reverse.geocoder.ls.hereapi.com/6.2/reversegeocode.json?prox='
if platform.system() == 'Windows':
    results = subprocess.check_output(["netsh", "wlan", "show", "network", "bssid"])
    results = results.decode("ascii")  # needed in python 3
    result_list = results.replace('\r', '').split('\n')
    mac_list = set()
    for element in result_list:
        if re.match('.*BSSID.*', element):
            mac_list.add('{"mac": "' + (element.split(' : ')[1]) + '"}')
elif platform.system() == 'Darwin':
    wifi_list = os.popen(
        '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s -x').read()
    open('wifi_plist.txt', mode='w').write(wifi_list)
    hotspots_plist = plistlib.loads(str.encode(wifi_list), fmt=plistlib.FMT_XML)
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
data = '{"wlan":[' + ','.join(i for i in mac_list) + ']}'
print('Wifi hotspots:\n' + data)
req = requests.post(url=positioning_url, data=data, headers=positioning_headers)
json_result = json.loads(req.text)
print('result:\n' + str(json_result))
lat = json_result['location']['lat']
lon = json_result['location']['lng']
radius = json_result['location']['accuracy']
address_label = rev_geocoder(lat, lon)
mia_cicular_picture(lon, lat, radius, address_label)
