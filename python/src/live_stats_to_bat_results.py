from npb import PlayerProfile
import glob
import pandas as pd
import re
import time

# ----------------------------------------
# 打席結果JSONファイル一覧を取得
# ----------------------------------------
dir_path = '../live-stats/'
file_pattern = '2023-*-*-bat.json'

file_list = glob.glob(f"{dir_path}{file_pattern}")
file_list.sort()
print(file_list)


# 全打席結果データ(空データ)
bats_all = pd.DataFrame([])

# --------------------------------------------------
# 打席JSONファイルを1ファイルづつ読み込み
# --------------------------------------------------
for file in file_list:
    # ----------------------------------------
    # ファイル名から日付情報を読み込み
    # ----------------------------------------
    match = re.search(r'(([0-9]+)-([0-9]+)-([0-9]+))-bat', file)
    date = match.group(1)
    year = match.group(2)
    month = match.group(3)
    day = match.group(4)
    print(date, year, month, day)

    # ----------------------------------------
    # JSONファイルからデータフレーム化
    # ----------------------------------------
    df = pd.read_json(file)
    bats = pd.json_normalize(data=df.to_dict("records"))

    # ----------------------------------------
    # 必要なカラムだけ残す
    # ----------------------------------------
    cols = [
        'date', 'visitor', 'home', 'inning_num', 'top_bottom', 'batter_num',
        'before_score.top', 'before_score.bottom',
        'before_count.b', 'before_count.s', 'before_count.o',
        'after_score.top', 'after_score.bottom',
        'after_count.b', 'after_count.s', 'after_count.o',
        '1b.id', '1b.handed', '1b.name',
        '2b.id', '2b.handed', '2b.name',
        '3b.id', '3b.handed', '3b.name',
        'batter.id', 'batter.handed', 'batter.name', 'pitcher.id', 'pitcher.handed', 'pitcher.name',
        'direction', 'result',
        ]
    bat_results = bats[cols].copy()

    # ----------------------------------------
    # IDが入っている塁は1で、ランナーなしは0
    # ----------------------------------------
    bat_results['before_1b'] = 0
    bat_results.loc[bat_results['1b.id'].notna(), 'before_1b'] = 1

    bat_results['before_2b'] = 0
    bat_results.loc[bat_results['2b.id'].notna(), 'before_2b'] = 1

    bat_results['before_3b'] = 0
    bat_results.loc[bat_results['3b.id'].notna(), 'before_3b'] = 1
    # print(bat_results.head())

    # ----------------------------------------
    # 不要カラムの削除
    # ----------------------------------------
    drop_cols = [
        '1b.id', '1b.handed', '1b.name',
        '2b.id', '2b.handed', '2b.name',
        '3b.id', '3b.handed', '3b.name',
        'before_count.b', 'before_count.s',
        'after_count.b', 'after_count.s',
    ]
    bat_results.drop(drop_cols, axis=1, inplace=True)
    # print(bat_results)

    # ----------------------------------------
    # 塁情報をshiftしてbeforeをafterに変更
    # ----------------------------------------
    ren_cols = {
        'before_1b': 'after_1b', 'before_2b': 'after_2b', 'before_3b': 'after_3b',
    }
    after_base = bat_results[['before_1b', 'before_2b', 'before_3b']].shift(-1).fillna(0).rename(columns=ren_cols).astype(int)
    # after_base

    # ----------------------------------------
    # カラム名を変更
    # ----------------------------------------
    ren_cols = {
        'inning_num': 'inning',
        'before_count.o': 'before_out', 'after_count.o': 'after_out',
        'visitor': 'team.top', 'home': 'team.bottom',
        'batter_num': 'batter_number',
    }
    bat_results.rename(columns=ren_cols, inplace=True)

    # ----------------------------------------
    # データを結合
    # ----------------------------------------
    bat_results = pd.concat([bat_results, after_base], axis=1)
    # bat_results

    # ----------------------------------------
    # 得点情報を追加
    # ----------------------------------------
    def point(bat):
        if bat['top_bottom'] == 1: # 表
            return bat['after_score.top'] - bat['before_score.top']
        elif bat['top_bottom'] == 2: # 裏
            return bat['after_score.bottom'] - bat['before_score.bottom']
        else:
            return 0
    # イニングの取得得点
    bat_results['point'] = bat_results.apply(point, axis=1)

    # ----------------------------------------
    # カラムの順番を変更
    # ----------------------------------------
    re_cols = [
        'date', 'team.top', 'team.bottom', 'inning', 'top_bottom', 'batter_number', 
        'before_score.top', 'before_score.bottom',
        'after_score.top', 'after_score.bottom',
        'point', 
        'before_out', 'before_1b', 'before_2b', 'before_3b', 
        'after_out', 'after_1b', 'after_2b', 'after_3b',
        'batter.id', 'batter.handed', 'batter.name' ,
        'pitcher.id', 'pitcher.handed', 'pitcher.name',
        'direction', 'result',
    ]
    bat_results = bat_results.reindex(columns=re_cols)

    # ファイル保存
    bat_results.to_csv(f"../live-stats/bat-{date}.csv", index=False)

    # 全データに結合
    bats_all = pd.concat([bats_all, bat_results])


# ----------------------------------------
# 得点期待値ファイルを読み込み
# ----------------------------------------
re_filename = 're-2018.csv' # 2018年度版
rcs = pd.read_csv(f"../live-stats/{re_filename}")

# ----------------------------------------
# 打席結果の得点期待値を追加
# ----------------------------------------
def before_re(bat):
    rc = rcs.loc[(rcs['out']==bat['before_out']) & (rcs['1b']==bat['before_1b']) & (rcs['2b']==bat['before_2b']) & (rcs['3b']==bat['before_3b'])]['rc'].values[0]
    return rc

def after_re(bat):
    rc = rcs.loc[(rcs['out']==bat['after_out']) & (rcs['1b']==bat['after_1b']) & (rcs['2b']==bat['after_2b']) & (rcs['3b']==bat['after_3b'])]['rc'].values[0]
    return rc

bats_all['RE'] = 0.000
bats_all['RE'] = round(bats_all.apply(after_re, axis=1) - bats_all.apply(before_re, axis=1) + bats_all['point'], 4)

# ----------------------------------------
# ファイル保存
# ----------------------------------------
bats_all.to_csv(f"../live-stats/bat-{year}.csv", index=False)
# # 打者ID保存
# pd.DataFrame(bats_all['batter.id'].unique(), columns=['id']).to_csv(f"../live-stats/batter-id-{year}.csv", index=False)
# # 投手ID保存
# pd.DataFrame(bats_all['pitcher.id'].unique(), columns=['id']).to_csv(f"../live-stats/pitcher-id-{year}.csv", index=False)

# ----------------------------------------
# 既存の打者プロファイルを読み込む
# ----------------------------------------
batters = pd.read_csv(f"../live-stats/batter-profile-{year}.csv")

cols = ['id', 'team_code', 'number', 'name', 'ruby', 'height', 'weight', 'handed bat', 'handed pitch', 'pro year', 'birthday', 'age', 'birthplace', 'blood type']
for id in bats_all['batter.id'].unique():
    if batters['id'].isin([id]).sum() == 0:
        print(f"ID: {id}")
        profile = PlayerProfile(id)
        batter = pd.DataFrame([profile.profile()], columns=cols)
        batters = pd.concat([batters, batter])
        time.sleep(2)
    
batters.to_csv(f"../live-stats/batter-profile-{year}.csv", index=False)

# ----------------------------------------
# 既存の投手プロファイルを読み込む
# ----------------------------------------
pitchers = pd.read_csv(f"../live-stats/pitcher-profile-{year}.csv")

cols = ['id', 'team_code', 'number', 'name', 'ruby', 'height', 'weight', 'handed bat', 'handed pitch', 'pro year', 'birthday', 'age', 'birthplace', 'blood type']
for id in bats_all['pitcher.id'].unique():
    if pitchers['id'].isin([id]).sum() == 0:
        print(f"ID: {id}")
        profile = PlayerProfile(id)
        pitcher = pd.DataFrame([profile.profile()], columns=cols)
        pitchers = pd.concat([pitchers, pitcher])
        time.sleep(2)
    
pitchers.to_csv(f"../live-stats/pitcher-profile-{year}.csv", index=False)