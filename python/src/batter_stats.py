# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup 
import datetime
from npb import Schedule
import pandas as pd
import re
import requests
import sys
import time

RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
END = '\033[0m'

if __name__ == '__main__':
    """メイン処理"""

    # 日付取得
    args = sys.argv
    if str.isdecimal(args[1]) and str.isdecimal(args[2]) and str.isdecimal(args[3]):
        year = int(args[1])
        month = int(args[2])
        day = int(args[3])
    else:
        print("Date numebr is not deciaml! year={}, month={}, day={}".format(args[1], args[2], args[3]))
        exit(0)

    date = datetime.date(year, month, day)
    date_text = date.strftime("%Y-%m-%d")

    schedule = Schedule(date)
    game_ids = schedule.game_ids()
    print("取得試合ID一覧: {}".format(game_ids))
    
    game_sleep = 3 #秒

    batter_stats = []
    for game_id in game_ids:

        # Yahooからデータを取得
        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        url = "https://baseball.yahoo.co.jp/npb/game/{}/stats".format(game_id)
        print(url)
        try: 
            res = requests.get(url, headers=requests_header)
        except requests.exceptions.RequestException as e:
            print("requests error occur {} ({})".format(e))
        soup = BeautifulSoup(res.text, "lxml")

        stat_tables = soup.find_all(class_="bb-statsTable")
        for stat_table in stat_tables:
            rows = stat_table.find('tbody').find_all(class_="bb-statsTable__row")
            for row in rows:
                id = None
                datas = row.find_all(class_="bb-statsTable__data")
                if a := datas[1].find('a'):
                    if match := re.search(r'[0-9]+', a.attrs['href']):
                        id = int(match.group(0))
                name = datas[1].text
                if datas[2].text == '-':
                    avg = 0.0
                else:
                    avg = float(datas[2].text)
                ab = int(datas[3].text)
                r = int(datas[4].text)
                h = int(datas[5].text)
                rbi = int(datas[6].text)
                so = int(datas[7].text)
                bb = int(datas[8].text)
                hbp = int(datas[9].text)
                sh = int(datas[10].text)
                sb = int(datas[11].text)
                e = int(datas[12].text)
                hr = int(datas[13].text)
                batter_stats.append([date_text, game_id, name, id, avg, ab, r, h, rbi, so, bb, hbp, sh, sb, e, hr])

        """試合終了時処理"""
        print("{} 試合取得終了 {}秒待ち".format(game_id, game_sleep))
        print("-"*80)
        time.sleep(game_sleep)        


    """PandasでCSVに保存"""
    batter_stats_columns = [
        '試合日', '試合ID', '選手名', '選手ID', '打率', '打数', '得点', '安打', '打点', '三振', '四球', '死球', '犠打', '盗塁', '失策', '本塁打'
    ]
    batter_stats_df = pd.DataFrame(batter_stats, columns=batter_stats_columns)
    batter_stats_df.to_csv("../batter-stats/{}.csv".format(date_text), index=False)


