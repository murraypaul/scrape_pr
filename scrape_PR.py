import requests
from bs4 import BeautifulSoup

def main():
    urlbase = "https://www.perrypedia.de"
    start_url = "/wiki/Silberband-Synopse"

    HR_Data = {}
    SB_Data = {}

    page = requests.get(urlbase + start_url)

    soup = BeautifulSoup(page.content, "html.parser")

    tables = soup.find_all("table",class_="perrypedia_std_table")

    break_all = False
    for table in tables:
        if break_all:
            break
        rows = table.find_all("tr")
        first_row = True
        for row in rows:
            # First row is header, in each table
            if first_row:
                first_row = False
                continue
            columns = row.find_all("td")
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

                    HR_page = requests.get(urlbase + HR_url)

                    HR_soup = BeautifulSoup(HR_page.content, "html.parser")

                    tables = HR_soup.find_all("table")
                    found_table = False
                    for table in tables:
                        if found_table:
                            continue;
                        rows = table.find_all("tr")
                        if len(rows) == 0:
                            continue
                        cols = rows[0].find_all("th")
                        if len(cols) == 0:
                            continue
                        if cols[0].text.startswith("Überblick"):
                            found_table = True
                        else:
                            continue

                        for row in rows:
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

                SB_Number = col_SB.text.strip()
                if SB_Number == "-":
                    SB_Number = ""
                elif SB_Number.startswith("HJB-Edition"):
                    SB_Number = ""
                SB_Name = 'Excluded'
                SB_link = col_SB.find_all("a")
                if not SB_Number in SB_Data:
                    if len(SB_link) == 1:
                        SB_url = SB_link[0]["href"]

                        SB_page = requests.get(urlbase + SB_url)

                        SB_soup = BeautifulSoup(SB_page.content, "html.parser")

                        tables = SB_soup.find_all("table")
                        found_table = False
                        for table in tables:
                            if found_table:
                                continue;
                            rows = table.find_all("tr")
                            if len(rows) == 0:
                                continue
                            cols = rows[0].find_all("th")
                            if len(cols) == 0:
                                continue
                            if cols[0].text.startswith("Überblick"):
                                found_table = True
                            else:
                                continue

                            for row in rows:
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

                #if len(SB_Data) > 12:
                #    break_all = True
                #    break

    for oneSB in SB_Data:
        id = SB_Data[oneSB]['id'].rjust(3,'0')
        if id == "000":
            continue
        print(f"{id} {SB_Data[oneSB]['title']}")
        for oneHR in SB_Data[oneSB]["contains"]:
            print(f"    {HR_Data[oneHR]['id'].rjust(4,'0')} {HR_Data[oneHR]['title']} - {HR_Data[oneHR]['author']} ({HR_Data[oneHR]['chapters']}, {HR_Data[oneHR]['page_count']})")

    excluded = SB_Data[""]
    print(f"Excluded")
    for oneHR in excluded["contains"]:
        print(f"    {HR_Data[oneHR]['id'].rjust(4,'0')} {HR_Data[oneHR]['title']} - {HR_Data[oneHR]['author']}")



if __name__ == "__main__":
# Call the main function
    main()
