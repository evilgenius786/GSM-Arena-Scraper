import csv
import json
import os
import threading
import time
import traceback

import requests

from bs4 import BeautifulSoup

gsm = "https://www.gsmarena.com/"
semaphore = threading.Semaphore(1)
thread = threading.Semaphore(1)
devices = []
brands = []
scraped = []
headers = ['2G bands', '3.5mm jack', '3G bands', '4G bands', 'Announced', 'Battery', 'Bluetooth', 'Body', 'Camera',
           'Card slot', 'Chipset', 'Colors', 'CPU', 'Dimensions', 'Display', 'EDGE', 'Expansion', 'Fans', 'Features',
           'GPRS', 'GPS', 'GPU', 'Internal', 'Loudspeaker', 'Name', 'NFC', "OS", 'Popularity', 'Price', 'Radio',
           'Released', 'Resolution', 'Sensors', 'SIM', 'Single', 'Size', 'Speed', 'Status', 'Storage', 'Talk time',
           'Type', 'URL', 'USB', 'Video', 'Weight', 'WLAN']


def level1(url):
    soup = getSoup(url)
    hrefs = []
    for a in soup.find('table').find_all('a'):
        if a['href'] not in brands:
            hrefs.append(a['href'])
    print(url, hrefs)
    with open("brands.txt", 'a') as bfile:
        bfile.write("\n".join(hrefs))


def level2(url):
    with thread:
        time.sleep(1)
        urls = []
        soup = getSoup(url)
        for li in soup.find('div', {"class": "makers"}).find_all('li'):
            device = li.find('a')['href']
            if device not in devices and device not in urls:
                urls.append(device)
        print(url, urls)
        addDevices(urls)
    nxt = soup.find('a', {"class": "pages-next"})
    if nxt is not None and "disabled" not in nxt['class']:
        level2(f"{gsm}/{nxt['href']}")


def level3(u):
    with thread:
        try:
            time.sleep(1)
            url = gsm + u
            print(url)
            soup = getSoup(url)
            if "Too Many Requests" in soup.text:
                print(url, "Too Many Requests")
                return
            mobile = {
                "Name": soup.find('h1', {"data-spec": "modelname"}).text,
                "URL": url
            }
            for li in soup.find('ul', {'class': "specs-spotlight-features"}).find_all('li')[1:]:
                mobile[li['class'][-1].replace("help-", "").strip().title()] = li.text.strip().replace("\n", "  ")
            for span in soup.find("li", {"class": "specs-brief pattern"}).find_all('span', {"data-spec": True}):
                mobile[span["data-spec"].replace("-hl", "").strip().title()] = span.text
            title = ""
            for tr in soup.findAll('tr')[1:]:
                if tr.find('a'):
                    title = tr.find('a').text.strip()
                if tr.find('td', {"class": "nfo"}) is not None:
                    if title not in mobile.keys():
                        mobile[title] = ""
                    else:
                        mobile[title] += "\n"
                    mobile[title] += tr.find('td', {"class": "nfo"}).text.strip()
            if "Os" in mobile.keys():
                mobile['OS'] = mobile['Os']
                del mobile['Os']
            append(mobile)
            scraped.append(u)
            with open("scraped.txt", 'a') as sfile:
                sfile.write(u + "\n")
        except:
            traceback.print_exc()
            with open("error.txt", 'a') as efile:
                efile.write(u + "\n")


def addDevices(hrefs):
    with semaphore:
        with open("devices.txt", 'a') as dfile:
            dfile.write("\n".join(hrefs))


def append(mobile):
    print(json.dumps(mobile, indent=4))
    with open("./json/"+mobile['URL'].replace(gsm, "").replace(".php", ".json"), "w") as jfile:
        json.dump(mobile, jfile, indent=4)
    with open("Output.csv", 'a',newline='') as outfile:
        csv.DictWriter(outfile, fieldnames=headers, extrasaction='ignore').writerow(mobile)


def getSoup(url):
    return BeautifulSoup(requests.get(url).content, 'lxml')


def checkfile(file):
    if not os.path.isfile(file):
        with open(file, "w") as dfile:
            dfile.write("")


def main():
    logo()
    global devices, brands, scraped
    if not os.path.isdir("json"):
        os.mkdir("json")
    if not os.path.isfile("Output.csv"):
        with open("Output.csv", 'a',newline='') as outfile:
            csv.DictWriter(outfile, fieldnames=headers).writeheader()
    checkfile("devices.txt")
    checkfile("brands.txt")
    checkfile("scraped.txt")
    with open('brands.txt') as bfile:
        brands = bfile.read().splitlines()
    level1(f"{gsm}makers.php3")
    with open('brands.txt') as bfile:
        brands = bfile.read().splitlines()
    with open('devices.txt') as dfile:
        devices = dfile.read().splitlines()
    for href in brands:
        # threading.Thread(target=level2,args=(f"{gsm}/{href}",)).start()
        level2(f"{gsm}/{href}", )
    with open('devices.txt') as dfile:
        devices = dfile.read().splitlines()
    with open('scraped.txt') as sfile:
        scraped = sfile.read().splitlines()
    for device in devices:
        if device not in scraped:
            threading.Thread(target=level3, args=(device,)).start()
            # break


def logo():
    os.system("color 0a")
    print(r"""
      ________  _________   _____       _____                               
     /  _____/ /   _____/  /     \     /  _  \_______   ____   ____ _____   
    /   \  ___ \_____  \  /  \ /  \   /  /_\  \_  __ \_/ __ \ /    \\__  \  
    \    \_\  \/        \/    Y    \ /    |    \  | \/\  ___/|   |  \/ __ \_
     \______  /_______  /\____|__  / \____|__  /__|    \___  >___|  (____  /
            \/        \/         \/          \/            \/     \/     \/ 
===================================================================================
            GSMarena.com scraper by http://github.com/evilgenius786
===================================================================================
[+] Scrapes all devices from GSM Arena
[+] Multithreaded
[+] Efficient
[+] Super fast
[+] Resumable
[+] CSV/JSON output
===================================================================================
""")


if __name__ == '__main__':
    main()
