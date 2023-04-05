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

    pitcher_stats = []
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

        stat_tables = soup.find_all(class_="bb-scoreTable")
        for stat_table in stat_tables:
            rows = stat_table.find_all(class_="bb-scoreTable__row")
            for row in rows:
                datas = row.find_all(class_="bb-scoreTable__data")
                point = datas[0].text.strip()           # ポイント 勝,負,H,S
                id = 0
                if a := datas[1].find('a'):
                    if match := re.search(r'[0-9]+', a.attrs['href']):
                        id = int(match.group(0).strip())
                name = datas[1].text.strip()
                if datas[2].text.strip() == '-':
                    era = 0.0
                else:
                    era = float(datas[2].text.strip())      # 防御率 Earned Run Average
                ip = float(datas[3].text.strip())         # 投球回数 Innings Pitched
                np = int(datas[4].text.strip())         # 投球数 Number of Pitches
                tbf = int(datas[5].text.strip())        # 対戦打者数 Total Batters Faced
                h = int(datas[6].text.strip())          # 被安打 Hits
                hr = int(datas[7].text.strip())         # 被本塁打 Home Runs
                so = int(datas[8].text.strip())         # 奪三振数 StrikeOuts
                bb = int(datas[9].text.strip())         # 与四球 Bases On Balls
                hbp = int(datas[10].text.strip())       # 与死球 Hit By Pitch
                balk = int(datas[11].text.strip())      # ボーク Balk
                r = int(datas[12].text.strip())         # 失点 Run
                er = int(datas[12].text.strip())        # 自責点 Earned Runs

                pitcher_stats.append([date_text, game_id, name, id, point, era, ip, np, tbf, h, hr, so, bb, hbp, balk, r, er])

        """試合終了時処理"""
        print("{} 試合取得終了 {}秒待ち".format(game_id, game_sleep))
        print("-"*80)
        time.sleep(game_sleep)        


    """PandasでCSVに保存"""
    pitcher_stats_columns = [
        '試合日', '試合ID', '選手名', '選手ID', 'ポイント', '防御率', '投球回', '投球数', '対戦打者', '被安打', '被本塁打', '奪三振', '与四球', '与死球', 'ボーク', '失点', '自責点'
    ]
    pitcher_stats_df = pd.DataFrame(pitcher_stats, columns=pitcher_stats_columns)
    pitcher_stats_df.to_csv("../pitcher-stats/{}.csv".format(date_text), index=False)


