import requests
from bs4 import BeautifulSoup
import time

# for URLCache
from shutil import copyfile
from pathlib import Path
import pickle
import sys

# for debugging only
import pprint

URLCache = {}
URLCacheTimeout = 24*60*60

ConfigFolder = Path(".scrape_pr")

OverrideSBNames = { 'HJB-Edition 2' : '008.1', 'HJB-Edition 1' : '018.1', 'Plophos 1' : '020.1', 'Plophos 2' : '020.2', 'Plophos 3' : '020.3', 'Plophos 4' : '020.4' }

def main():
    global OverrideSBNames

    urlbase = "https://www.perrypedia.de"
    start_url = "/wiki/Silberband-Synopse"

    HR_Data = {}
    SB_Data = {}
    maxHRNumber = 0

    init_urlcache_from_file()

    page = read_URL(urlbase + start_url)

    soup = BeautifulSoup(page, "html.parser")

    tables = soup.find_all("table",class_="perrypedia_std_table")

    break_all = False
    log_all = 0
    table_count = 0;
    for table in tables:
        if break_all:
            break
        table_count += 1
        rows = table.find_all("tr")
        if log_all > 0:
            print(f"Processing table {table_count} of {len(tables)}, with {len(rows)} rows, starting with {rows[1].find_all('td')[0]}",file=sys.stderr)
        first_row = True
        for row in rows:
            # First row is header, in each table
            if first_row:
                first_row = False
                continue
            if break_all:
                break
            columns = row.find_all("td")
#            log_all -= 1
            if log_all > 0:
                print(f"Processing row with {len(columns)} columns, starting with {columns[0]} ",file=sys.stderr)
#                pprint.pprint(row,stream=sys.stderr)
            if len(columns) == 5:
                col_HR = columns[0]
                col_SB = columns[1]
                SB_PageRange = columns[2].text.strip()
                SB_PageCount = columns[3].text.strip()
                SB_Chapters = columns[4].text.strip()

                HR_Number = ''
                HR_Name = ''
                HR_Author = ''
                HR_link = col_HR.find_all("a")
                if len(HR_link) == 1:
                    HR_Number = col_HR.text.replace(u'\xa0', u' ').replace("PR ","").strip()
                    HR_url = HR_link[0]["href"]

                    HR_Number_int = int(HR_Number)
                    if HR_Number_int > maxHRNumber:
                        maxHRNumber = HR_Number_int

                    HR_page = read_URL(urlbase + HR_url, -1)

                    if HR_page is None:
                        print("Unable to read page, cancelling", file=sys.stderr)
                        break_all = True;
                        break;

                    HR_soup = BeautifulSoup(HR_page, "html.parser")

                    tables2 = HR_soup.find_all("table")
                    found_table = False
                    for table in tables2:
                        if found_table:
                            continue;
                        rows2 = table.find_all("tr")
                        if len(rows2) == 0:
                            continue
                        cols = rows2[0].find_all("th")
                        if len(cols) == 0:
                            continue
                        if cols[0].text.startswith("Überblick"):
                            found_table = True
                        else:
                            continue

                        for row in rows2:
                            col_TD = row.find_all("td")
                            col_TH = row.find_all("th")

                            value = ""
                            if len(col_TH) > 0:
                                value = col_TH[0].text.strip()
                            elif len(col_TD) > 1:
                                value = col_TD[1].text.strip()
                            else:
                                continue
                            if len(col_TD):
                                if col_TD[0].text.startswith("Titel:"):
                                    HR_Name = value
                                elif col_TD[0].text.startswith("Autor:"):
                                    HR_Author = value

                this_HR = { 'id': HR_Number, 'title': HR_Name, 'author': HR_Author, 'page_range': SB_PageRange, 'page_count' : SB_PageCount, 'chapters': SB_Chapters }
                HR_Data[HR_Number] = this_HR

                SB_Number = col_SB.text.strip().rjust(3,'0')
                SB_Name = 'Excluded'
                SB_link = col_SB.find_all("a")

                if SB_Number == "00-":
                    SB_Number = "000"
                elif SB_Number in OverrideSBNames:
                    print(f"Overriding number {SB_Number}", file=sys.stderr)
                    SB_Name = SB_Number
                    SB_Number = OverrideSBNames[SB_Number]
                    SB_link = ""

                if not SB_Number in SB_Data:
                    if len(SB_link) == 1:
                        SB_url = SB_link[0]["href"]

                        SB_page = read_URL(urlbase + SB_url, -1)

                        if SB_page is None:
                            print("Unable to read page, cancelling", file=sys.stderr)
                            break_all = True;
                            break;

                        SB_soup = BeautifulSoup(SB_page, "html.parser")

                        tables3 = SB_soup.find_all("table")
                        found_table = False
                        for table in tables3:
                            if found_table:
                                continue;
                            rows3 = table.find_all("tr")
                            if len(rows3) == 0:
                                continue
                            cols = rows3[0].find_all("th")
                            if len(cols) == 0:
                                continue
                            if cols[0].text.startswith("Überblick"):
                                found_table = True
                            else:
                                continue

                            for row in rows3:
                                col_TD = row.find_all("td")
                                col_TH = row.find_all("th")

                                value = ""
                                if len(col_TH) > 0:
                                    value = col_TH[0].text.strip()
                                elif len(col_TD) > 1:
                                    value = col_TD[1].text.strip()
                                else:
                                    continue
                                if len(col_TD):
                                    if col_TD[0].text.startswith("Titel:"):
                                        SB_Name = value

                    this_SB = { 'id': SB_Number, 'title': SB_Name, 'contains': [] }
                    SB_Data[SB_Number] = this_SB

                SB_Data[SB_Number]["contains"].append(HR_Number)

                if len(SB_Data) % 20 == 0:
                    #break_all = True
                    #break
                    pass

    sortedSB = dict(sorted(SB_Data.items()))
    for oneSB in sortedSB:
        id = sortedSB[oneSB]['id']
        if id == "000":
            continue
        print(f"{id} {sortedSB[oneSB]['title']}")
        for oneHR in sortedSB[oneSB]["contains"]:
#           print(f"    {HR_Data[oneHR]['id'].rjust(4,'0')} {HR_Data[oneHR]['title']} - {HR_Data[oneHR]['author']} ({HR_Data[oneHR]['chapters']}, {HR_Data[oneHR]['page_count']})")
            print(f"    {HR_Data[oneHR]['id'].rjust(4,'0')} {HR_Data[oneHR]['title']} ({HR_Data[oneHR]['chapters']}, {HR_Data[oneHR]['page_count']})")

    excluded = SB_Data["000"]
    print(f"Excluded")
    for oneHR in excluded["contains"]:
        print(f"    {HR_Data[oneHR]['id'].rjust(4,'0')} {HR_Data[oneHR]['title']} - {HR_Data[oneHR]['author']}")

    print("Missing")
    for i in range(1,maxHRNumber):
        if not str(i) in HR_Data:
            print(str(i).rjust(4,'0'))

def init_urlcache_from_file():
    global URLCache
    URLCache.clear()
    try:
        with open(ConfigFolder / 'urlcache.pickle','rb') as cachefile:
            newURLCache = pickle.load(cachefile)
    except FileNotFoundError:
        return None

    timenow = int(time.time())
    for key, value in newURLCache.items():
        if value[0] < timenow - URLCacheTimeout:
            value[1] = None
        elif "HJB" in key:
            value[1] = None

    URLCache = { key: value for key, value in newURLCache.items() if value is not None }

    print(f"Read {len(URLCache)} entries from URL cache file, expired {len(newURLCache)-len(URLCache)} extries.", file=sys.stderr)

def init_urlcache_to_file():
    try:
        copyfile(ConfigFolder / 'urlcache.pickle',ConfigFolder / 'urlcache.bak')
    except FileNotFoundError:
        pass
    try:
        with open(ConfigFolder / 'urlcache.pickle','wb') as cachefile:
            pickle.dump(URLCache,cachefile)

        #print(f"Wrote {len(URLCache)} entries to URL cache file.")
    except:
        print("Error writing URL cache file, restoring backup", file=sys.stderr)
        copyfile(ConfigFolder / 'urlcache.pickle',ConfigFolder / 'urlcache.txt')

def read_URL(url,cacheTimeout=URLCacheTimeout):
    timenow = int(time.time())
    cacheEntry = URLCache.get(url,[-1,None])
    if cacheEntry[1] == None or (cacheTimeout > 0 and cacheEntry[0] < timenow - cacheTimeout):
        print(f"No or expired cache for {url}", file=sys.stderr)
        try:
            page = requests.get(url,timeout=10)
            URLCache[url] = [timenow,page.content]
            data = page.content
            init_urlcache_to_file()
        except requests.exceptions.Timeout:
            print(f"Timeout reading {url}", file=sys.stderr)
            return None
        time.sleep(1)
        return data
    else:
#        print(f"Retrieved {url} from cache")
        return cacheEntry[1]


if __name__ == "__main__":
# Call the main function
    main()

