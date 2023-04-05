# -*- coding: utf-8 -*-
from calendar import month
from bs4 import BeautifulSoup 
import datetime
import glob
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

# ------------------------------------------------------
# 打席情報を読み込む 複数ファイル
# ------------------------------------------------------
path = "../batter-stats"
# month = 3
# files = glob.glob(path + "/2022-{:02}-*.csv".format(month))
files = glob.glob(path + "/2022-*-*.csv")
print("ファイル数: ", len(files))

df_list = []
for filename in files:
    df = pd.read_csv(filename)
    df_list.append(df)

batter_stats = pd.concat(df_list, axis=0, ignore_index=True)
     
"""PandasでCSVに保存"""
batter_stats_columns = [
    '試合日', '試合ID', '選手名', '選手ID', '打率', '打数', '得点', '安打', '打点', '三振', '四球', '死球', '犠打', '盗塁', '失策', '本塁打'
]
batter_stats_df = pd.DataFrame(batter_stats, columns=batter_stats_columns)
batter_stats_df = batter_stats_df.sort_values(['試合日', '試合ID'])
# batter_stats_df.to_csv("../batter-stats/2022-{:02}-batter-stats.csv".format(month), index=False)
batter_stats_df.to_csv("../batter-stats/2022-batter-stats.csv", index=False)


