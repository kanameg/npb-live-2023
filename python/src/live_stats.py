# -*- coding: utf-8 -*-
import sys
import datetime
from npb import Inning, Schedule, Event
import time
import pandas as pd

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
    
    inning_sleep = 2 #秒
    game_sleep = 10 #秒

    batter_box_stats = []
    steal_stats = []

    for game_id in game_ids:
        event = Event(game_id, Inning())
        while not event.game_end:
 
            if event.batter_box_end:
                """打席終了時処理"""
                batter_box_stat = [
                    date_text, event.game_id, event.visitor_team, event.home_team, event.inning_num, event.top_bottom, event.batter_num,
                    event.before_score, event.after_score, event.before_count, event.after_count, event.batter, event.pitcher,
                    event.b1_runner, event.b2_runner, event.b3_runner, event.direction, event.result, event.pitches
                ]
                batter_box_stats.append(batter_box_stat)

            if event.steal_success:
                """盗塁成功時処理"""
                for steal_runner in event.steal_success_runners:
                    steal_stat = [
                        date_text, event.game_id, event.visitor_team, event.home_team, event.inning_num, event.top_bottom, event.batter_num,
                        event.before_score, event.after_score, event.before_count, event.after_count, 1, steal_runner, event.batter, event.pitcher,
                        event.b1_runner, event.b2_runner, event.b3_runner, event.pitches
                    ]
                    steal_stats.append(steal_stat)
                pass
            
            if event.steal_failure:
                """盗塁失敗時処理"""
                for steal_runner in event.steal_failure_runners:
                    steal_stat = [
                        date_text, event.game_id, event.visitor_team, event.home_team, event.inning_num, event.top_bottom, event.batter_num,
                        event.before_score, event.after_score, event.before_count, event.after_count, 0, steal_runner, event.batter, event.pitcher,
                        event.b1_runner, event.b2_runner, event.b3_runner, event.pitches
                    ]
                    steal_stats.append(steal_stat)
                pass

            if event.inning_end:
                """イニング終了時処理"""
                print("{}回{} ".format(event.inning_num, ["表", "裏"][event.top_bottom-1]) + 
                    BOLD + [event.visitor_team, event.home_team][event.top_bottom-1] + END + 
                    "の攻撃終了 {}秒待ち".format(inning_sleep))
                print("-"*80)
                time.sleep(inning_sleep)
            """次のイベント"""
            event = event.next_event()

        """試合終了時処理"""
        print(BOLD + event.visitor_team + " - " + event.home_team + END + "試合終了 {}秒待ち".format(game_sleep))
        print("-"*80)
        time.sleep(game_sleep)        


    """PandasでJSONに保存"""
    batter_box_columns = [
        "date", "id", "visitor", "home", "inning_num", "top_bottom", "batter_num",
        "before_score", "after_score", "before_count", "after_count", "batter", "pitcher",
        "1b", "2b", "3b", "direction", "result", "pitches",
    ]
    bat_box_df = pd.DataFrame(batter_box_stats, columns=batter_box_columns)
    bat_box_df.to_json("../live-stats/{}-bat.json".format(date_text), orient='records', force_ascii=False)

    steal_columns = [
        "date", "id", "visitor", "home", "inning_num", "top_bottom", "batter_num",
        "before_score", "after_score", "before_count", "after_count", "success", "runner", "batter", "pitcher",
        "1b", "2b", "3b", "pitches",
    ]
    steal_df = pd.DataFrame(steal_stats, columns=steal_columns)
    steal_df.to_json("../live-stats/{}-sb.json".format(date_text), orient='records', force_ascii=False)

