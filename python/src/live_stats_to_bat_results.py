from bs4 import BeautifulSoup 
import glob
import pandas as pd
import re
import requests
import time



# 打席結果JSONファイル一覧を取得
dir_path = '../live-stats/'
file_pattern = '2023-*-*-bat.json'

file_list = glob.glob(f"{dir_path}{file_pattern}")
file_list.sort()
print(file_list)


class PlayerProfile:
    def __init__(self, id) -> None:
        self._id = id
        # Yahooからデータを取得
        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        url = f"https://baseball.yahoo.co.jp/npb/player/{self._id}/"
        print(f"URL: {url}")
        try: 
            res = requests.get(url, headers=requests_header)
        except requests.exceptions.RequestException as e:
            print("requests error occur {} ({})".format(e))
        soup = BeautifulSoup(res.text, "lxml")
        
        # チーム名
        bb = soup.find(class_='bb-head01__title')
        self._team = bb.text if bb else None
        # print(f"チーム: {self._team}")

        # 名前
        bb = soup.find(class_='bb-profile__name').find('h1')
        self._name = bb.text if bb else None
        # print(f"名前: {self._name}")
        
        # ルビ
        bb = soup.find(class_='bb-profile__name').find('rt')
        if bb:
            if match := re.search(r"（(.+)）", bb.text):
                self._ruby = match.group(1)
            else:
                self._ruby = None             
        else:
            self._ruby = None
        # print(f"ふりがな: {self._ruby}")

        # 背番号
        bb = soup.find(class_='bb-profile__number')
        self._number = bb.text if bb else None
        # print(f"背番号: {self._number}")

        # ボジション
        bb = soup.find(class_='bb-profile__position')
        self._position = bb.text if bb else None
        # print(f"ボジション: {self._position}")

        # 詳細情報
        plist = soup.find_all(class_='bb-profile__list')            

        # 出身地
        bb = soup.find_all(class_='bb-profile__text')
        self._birthplace = bb[0].text if bb[0] else None
        # print(f"出身地: {self._birthplace}")

        # 誕生日
        if bb[1]:
            if match := re.search(r"([0-9]+)年([0-9]+)月([0-9]+)日（([0-9]+)歳）", bb[1].text):
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                age = int(match.group(4))
                self._birthday = f"{year:04}-{month:02}-{day:02}"
                self._age = age
            else:
                self._birthday = None
                self._age = None
        else:
            self._birthday = None
            self._age = None
        # print(f"誕生日: {self._birthday}")
        # print(f"年齢: {self._age}")

        # 身長
        if bb[2]:
            if match := re.search(r"([0-9]+)cm", bb[2].text):
                self._height = int(match.group(1))
            else:
                self._height = None
        else:
            self._height = None
        # print(f"身長: {self._height}")

        # 体重
        if bb[3]:
            if match := re.search(r"([0-9]+)kg", bb[3].text):
                self._weight = int(match.group(1))
            else:
                self._weight = None
        else:
            self._weight = None
        # print(f"体重: {self._weight}")

        # 血液型
        if bb[4]:
            if match := re.search(r"([ABO]+)", bb[4].text):
                self._blood_type = match.group(1)
            else:
                self._blood_type = None
        else:
            self._blood_type = None
        # print(f"血液型: {self._blood_type}")

        # 投打
        if bb[5]:
            if match := re.search(r"(.)投げ(.)打ち", bb[5].text):
                self._handed_pitch = match.group(1)
                self._handed_bat = match.group(2)
            else:
                self._handed_pitch = None
                self._handed_bat = None
        else:
            self._handed_pitch = None
            self._handed_bat = None
        # print(f"投: {self._handed_pitch}")
        # print(f"打: {self._handed_bat}")

        # 通算年
        for pl in plist:
            if (pl.find(class_='bb-profile__title').text == 'プロ通算年'):
                if match := re.search(r"([1-9][0-9]*)年", pl.find(class_='bb-profile__text').text):
                    self._year = int(match.group(1))
                    break
                else:
                    self._year = None
            else:
                self._year = None
        # print(f"通算年: {self._year}")
        pass

    """
    public method
    """
    def profile(self):
        # ID チーム名, 背番号, 名前, ふりがな, 
        return [
            self._id, self._team, self._number, self._name, self._ruby,
            self._height, self._weight,
            self._handed_pitch, self._handed_bat, self._year , 
            self._birthday, self._age, self._birthplace, self._blood_type
        ]





bats_all = pd.DataFrame([])

for file in file_list:
    match = re.search(r'(([0-9]+)-([0-9]+)-([0-9]+))-bat', file)
    date = match.group(1)
    year = match.group(2)
    month = match.group(3)
    day = match.group(4)
    print(date, year, month, day)

    df = pd.read_json(file)
    bats = pd.json_normalize(data=df.to_dict("records"))

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

    # 必要なカラムだけ残す
    bat_results = bats[cols].copy()

    # IDが入っている塁は1で、ランナーなしは0
    bat_results['before_1b'] = 0
    bat_results.loc[bat_results['1b.id'].notna(), 'before_1b'] = 1

    bat_results['before_2b'] = 0
    bat_results.loc[bat_results['2b.id'].notna(), 'before_2b'] = 1

    bat_results['before_3b'] = 0
    bat_results.loc[bat_results['3b.id'].notna(), 'before_3b'] = 1
    # print(bat_results.head())

    # 不要カラムの削除
    drop_cols = [
        '1b.id', '1b.handed', '1b.name',
        '2b.id', '2b.handed', '2b.name',
        '3b.id', '3b.handed', '3b.name',
        'before_count.b', 'before_count.s',
        'after_count.b', 'after_count.s',
    ]
    bat_results.drop(drop_cols, axis=1, inplace=True)
    # print(bat_results)

    # 塁情報をshiftしてbeforeをafterに変更
    ren_cols = {
        'before_1b': 'after_1b', 'before_2b': 'after_2b', 'before_3b': 'after_3b',
    }
    after_base = bat_results[['before_1b', 'before_2b', 'before_3b']].shift(-1).fillna(0).rename(columns=ren_cols).astype(int)
    # after_base

    # カラム名を変更
    ren_cols = {
        'inning_num': 'inning',
        'before_count.o': 'before_out', 'after_count.o': 'after_out',
        'visitor': 'team.top', 'home': 'team.bottom',
        'batter_num': 'batter_number',
    }
    bat_results.rename(columns=ren_cols, inplace=True)

    # データを結合
    bat_results = pd.concat([bat_results, after_base], axis=1)
    # bat_results

    # 得点情報を追加
    def point(bat):
        if bat['top_bottom'] == 1:
            return bat['after_score.top'] - bat['before_score.top']
        elif bat['top_bottom'] == 2:
            return bat['after_score.bottom'] - bat['before_score.bottom']
        else:
            return 0

    bat_results['point'] = bat_results.apply(point, axis=1)

    # カラムの順番を変更
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



rcs = pd.read_csv('../live-stats/rc2018.csv')


def before_rc(bat):
    rc = rcs.loc[(rcs['out']==bat['before_out']) & (rcs['1b']==bat['before_1b']) & (rcs['2b']==bat['before_2b']) & (rcs['3b']==bat['before_3b'])]['rc'].values[0]
    return rc

def after_rc(bat):
    rc = rcs.loc[(rcs['out']==bat['after_out']) & (rcs['1b']==bat['after_1b']) & (rcs['2b']==bat['after_2b']) & (rcs['3b']==bat['after_3b'])]['rc'].values[0]
    return rc

bats_all['rc'] = 0.000
bats_all['rc'] = round(bats_all.apply(after_rc, axis=1) - bats_all.apply(before_rc, axis=1) + bats_all['point'], 4)

# ファイル保存
bats_all.to_csv(f"../live-stats/bat-{year}.csv", index=False)
# 打者ID保存
pd.DataFrame(bats_all['batter.id'].unique(), columns=['id']).to_csv(f"../live-stats/batter-id-{year}.csv", index=False)
# 投手ID保存
pd.DataFrame(bats_all['pitcher.id'].unique(), columns=['id']).to_csv(f"../live-stats/pitcher-id-{year}.csv", index=False)


# 既存の打者プロファイルを読み込む
batters = pd.read_csv(f"../live-stats/batter-profile-{year}.csv")

cols = ['id', 'team', 'number', 'name', 'ruby', 'height', 'weight', 'handed bat', 'handed pitch', 'pro year', 'birthday', 'age', 'birthplace', 'blood type']
for id in bats_all['batter.id'].unique():
    if batters['id'].isin([id]).sum() == 0:
        print(f"ID: {id}")
        profile = PlayerProfile(id)
        batter = pd.DataFrame([profile.profile()], columns=cols)
        batters = pd.concat([batters, batter])
        time.sleep(2)
    
batters.to_csv(f"../live-stats/batter-profile-{year}.csv", index=False)


# 既存の投手プロファイルを読み込む
pitchers = pd.read_csv(f"../live-stats/pitcher-profile-{year}.csv")

cols = ['id', 'team', 'number', 'name', 'ruby', 'height', 'weight', 'handed bat', 'handed pitch', 'pro year', 'birthday', 'age', 'birthplace', 'blood type']
for id in bats_all['pitcher.id'].unique():
    if pitchers['id'].isin([id]).sum() == 0:
        print(f"ID: {id}")
        profile = PlayerProfile(id)
        pitcher = pd.DataFrame([profile.profile()], columns=cols)
        pitchers = pd.concat([pitchers, pitcher])
        time.sleep(2)
    
pitchers.to_csv(f"../live-stats/pitcher-profile-{year}.csv", index=False)