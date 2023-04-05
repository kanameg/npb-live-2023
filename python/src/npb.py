# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import datetime
import time
import pandas as pd
import requests
import re
import sys
from typing import List, Optional, Tuple


RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
END = '\033[0m'

class Schedule:
    """
    試合スケジュール情報クラス
    """
    def __init__(self, date: datetime.date) -> None:
        # ------------------------------------------------------
        # Requests用のUser-agent
        # ------------------------------------------------------
        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        url = "https://baseball.yahoo.co.jp/npb/schedule/?date={}".format(date.strftime("%Y-%m-%d"))
        print(url)
        res = requests.get(url, headers=requests_header)
        self.__soup = BeautifulSoup(res.text, "lxml")
        return

    def __check_game_day(self) -> bool:
        """ゲームがある日かどうかのチェック"""
        if no_data := self.__soup.find(class_="bb-noData"):
            if "試合はありません" in no_data.text:
                return False
        return True

    def game_ids(self) -> List[int]:
        """当日の試合終了した試合IDを取得"""
        ids = []
        if self.__check_game_day():            
            for link in self.__soup.find_all(class_='bb-score__content'):
                if match := re.search(r'[0-9]{10}', link.attrs['href']):
                    id = int(match.group(0))
                    if '試合終了' in link.find(class_='bb-score__link').text:
                        ids.append(id)
        return ids


class Score:
    """
    スコアクラス
    """
    top: int
    bottom: int
    def __init__(self, top: int=0, bottom: int=0) -> None:
        self.top = top
        self.bottom = bottom
        pass

    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))

class Count:
    """
    ボールカウントクラス
    """
    s: int
    b: int
    o: int
    def __init__(self, s:int=0, b:int=0, o:int=0) -> None:
        self.s = s
        self.b = b
        self.o = o
        pass

    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))

class Inning:
    """
    イニング情報クラス
    """ 
    inning_num: int         # イニング
    top_bottom: int         # 1:表 2:裏
    batter_num: int         # 打者数
    event_num: int          # イベント数
    before_out: int         # 前イベントのアウトカウント
    before_score: Score     # 前のスコア
    def __init__(self, inning_num: int=1, top_bottom: int=1, batter_num: int=1, event_num: int=0, before_out: int=0, before_score: Score=Score(0, 0)) -> None:
        self.inning_num = inning_num
        self.top_bottom = top_bottom
        self.batter_num = batter_num
        self.event_num = event_num
        self.before_out = before_out
        self.before_score = before_score
        pass

    def index(self) -> str:
        """URL用のインデックス"""
        return "{:02}{}{:02}{:02}".format(self.inning_num, self.top_bottom, self.batter_num, self.event_num)

    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))

class Cource:
    """
    投球コースクラス
    """
    top: int
    left: int
    def __init__(self, top:int, left:int) -> None:
        self.top = top
        self.left = left
        return

    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))

class Pitch:
    """
    投球詳細クラス
    """
    number:int
    number_of: int
    kind: str
    speed: Optional[int]
    cource: Cource
    result: str
    def __init__(self, number:int, number_of:int, kind:str, speed:Optional[int], cource:Cource, result:str) -> None:
        self.number = number
        self.number_of = number_of
        self.kind = kind
        self.speed = speed
        self.cource = cource
        self.result = result

    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))

class PlayerInfo:
    """
    プレイヤー情報クラス
    """
    id: int
    name: str
    handed: str

    def __init__(self, id:int, handed:Optional[str]=None, name:Optional[str]=None) -> None:
        self.id = id
        self.handed = handed
        self.name = name
        # if name is None:
        #     # requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        #     # requests_header = {
        #     #     'User-Agent': requests_user_agent
        #     # }
        #     # url = "https://baseball.yahoo.co.jp/npb/player/{}/".format(self.id)
            
        #     # try:
        #     #     res = requests.get(url, headers=requests_header)
        #     # except requests.exceptions.RequestException as e:
        #     #     print("requests error occur {} ({})".format(e, self.__class__))
        #     # self._soup = BeautifulSoup(res.text, "lxml")
        #     # self.name = self._soup.find(class_="bb-profile__name").find('h1').text
        #     self.name = None
        # else:
        #     self.name = name
        pass
            
    def __repr__(self) -> str:
        kvs = [f"{key}: {value!r}" for key, value in self.__dict__.items()]
        return "{} ({})".format(type(self).__name__, ", ".join(kvs))


class Event:
    """
    打席イベントクラス
    """
    """イニング情報"""
    game_id: int
    inning_num: int
    top_bottom: int
    batter_num: int
    event_num: int

    """状況"""
    visitor_team: str
    home_team: str
    before_score: Score
    after_score: Score
    before_count: Count
    after_count: Count

    """フィールド選手"""
    batter: PlayerInfo
    pitcher: PlayerInfo
    b1_runner: PlayerInfo
    b2_runner: PlayerInfo
    b3_runner: PlayerInfo
    steal_success_runners: List[PlayerInfo]
    steal_failure_runners: List[PlayerInfo]

    """打席結果"""
    direction: str
    result: str
    pitches: List[Pitch]

    """発生状況フラグ"""
    game_end: bool = False
    inning_end: bool = False
    batter_box_end: bool = False
    steal_success: bool = False
    steal_failure: bool = False

    def __init__(self, game_id:int, inning:Inning) -> None:
        self.game_id = game_id
        self.inning_num = inning.inning_num
        self.top_bottom = inning.top_bottom
        self.batter_num = inning.batter_num
        self.event_num = inning.event_num

        self.before_count = Count(0, 0, inning.before_out)
        self.before_score = inning.before_score

        self.__direction_check = [
            "右中", "左中", "右", "中", "左",                       # 外野
            "投", "捕", "一", "二", "三", "遊",                     # 内野
        ]

        self.__result_check = [
            '空三振', '見三振', 'バ三振', '暴振逃', '逸振逃',       # 三振系(3文字)
            '故意四', '犠打失', '犠飛失', '規則反',                 # 守備なし系(3文字)
            '四球', '死球', '打妨', '守妨',                         # 守備なし系 (2文字)
            'ゴロ', '犠飛', '邪飛', '併打', '犠打', '犠野', '野選', # アウト系(2文字)
            '飛', '直', '失',                                       # アウト系(1文字)
            '安', '２', '３', '走本', '本',                         # ヒット系
        ]


        # Yahooからデータを取得
        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        url = "https://baseball.yahoo.co.jp/npb/game/{}/score?index={}".format(self.game_id, inning.index())
        print(url)
        try: 
            res = requests.get(url, headers=requests_header)
        except requests.exceptions.RequestException as e:
            print("requests error occur {} ({})".format(e, self.__class__))
        self.__soup = BeautifulSoup(res.text, "lxml")


        # 受信HTMLを解析開始
        """ページがエラー 処理を終了"""
        if self.__check_error_page():
            # ページ読み込みエラー (ありえないパターン)
            print(RED + "!!! Page Error !!!" + END)
            exit(0)

        """チーム名を取得"""
        self.visitor_team, self.home_team = self.__team_name()

        """フィールドへの出場選手情報を取得"""
        self.__players = self.__field_palyers()

        """全投球結果一覧"""
        self.__results = self.__all_results()

        """試合状況"""
        self.after_score = self.__score()
        self.after_count = self.__count()
        self.b1_runner = self.__b1_runner()
        self.b2_runner = self.__b2_runner()
        self.b3_runner = self.__b3_runner()
        
        """フラグ(試合終了、インング終了、打席終了)チェック"""
        if self.__check_game_end():
            self.game_end = True
        if self.__check_inning_end():
            self.inning_end = True
        if self.__check_batter_box_end():
            self.batter_box_end = True

        """イベントチェック"""
        self.__check_events()

        """打席結果"""
        self.direction, self.result = self.__direction_and_result()

        """打者 投手"""
        self.pitcher = self.__pitcher()
        self.batter = self.__batter()

        """投球詳細"""
        self.pitches = self.__pitch_detail()
        return

    """
    public method
    """
    def next_event(self) -> 'Event':
        """次のイベントを取得"""
        next_event = None
        if next_inning := self.next_inning():
            next_event = Event(self.game_id, next_inning)
        return next_event

    def next_inning(self) -> Optional[Inning]:
        """次のイング情報を取得"""
        inning = None
        if next := self.__soup.find(id="btn_next"):
            index = next.attrs['index']
            inning_num = int(index[0:2])
            top_bottom = int(index[2])
            batter_num = int(index[3:5])
            event_num = int(index[6])
            before_out = 0 if self.after_count.o == 3 else self.after_count.o # 3アウトの時は0に変更
            before_score = self.after_score
            inning = Inning(inning_num, top_bottom, batter_num, event_num, before_out, before_score)
        return inning

    """
    private method
    """
    def __check_error_page(self) -> bool:
        """取得ページがエラーページかのチェック"""
        if yf_error := self.__soup.find(class_="yf-error__title"):
            error = True
        else:
            error = False
        return error

    def __check_inning_end(self) -> bool:
        """イニング終了かどうかのチェック"""
        if next_inning := self.next_inning():
            next_inning_num = next_inning.inning_num
            next_top_bottom = next_inning.top_bottom
            if next_inning_num != self.inning_num or next_top_bottom != self.top_bottom:
                return True
        else: 
            return False

    def __team_name(self) -> Tuple[str, str]:
        """チーム名を取得"""
        visitor = home = None
        if bb_team := self.__soup.find_all(class_="bb-gameScoreTable__team"):
            visitor = bb_team[0].text
            home = bb_team[1].text
        return visitor, home

    def __field_palyers(self) -> List[List[PlayerInfo]]:
        """フィールド出場選手一覧を取得"""
        players = []
        h = self.__soup.find(id='pitchesDetail').find_all('section')[0].find_all('table')
        v = self.__soup.find(id='pitchesDetail').find_all('section')[-1].find_all('table')
        for tables in [v, h]:
            infos = []
            trs = tables[0].find_all('tr')[1:]
            for tr in trs:
                tds = tr.find_all('td')
                name = tds[2].text
                if match := re.search(r'[0-9]+', tds[2].find('a').attrs['href']):
                    id = int(match.group(0))
                handed = tds[3].text
                info = PlayerInfo(id, handed, name)
                infos.append(info)
            players.append(infos)
        return players

    def __all_results(self) -> List[str]:
        """投球一覧を取得"""
        results = []
        # 打者が途中で交代するとballlistが複数あるのでfind_allで取得
        if ball_lists := self.__soup.find_all(class_="balllist"):
            for ball_list in ball_lists:
                balls = list(map(lambda td: str(td.text), ball_list.find_all("td")))
                results.extend(balls)
        # 敬遠でデータがない場合は無球で申告敬遠
        if self.__check_intentional_walk():
            results.append("故意四")
        return results

    def __direction_and_result(self) -> Tuple[Optional[str], Optional[str]]:
        """打球方向と結果を取得"""
        direction = None
        result = None
        if len(self.__results):
            last_pich = self.__results[-1]
            for check in self.__result_check:
                p = last_pich.find(check)
                if p == 0:
                    direction = None
                    result = check
                    break
                elif p > 0:
                    direction = last_pich[:p]
                    result = check
                    break
                else:
                    pass
        return direction, result

    def __short_name_to_info(self, short_name, top_bottom) -> Optional[PlayerInfo]:
        """選手略名から選手IDと名前を取得"""
        players = self.__players[top_bottom-1]

        info = None
        for player in players:
            if match := re.search(r'^' + short_name, player.name.replace(' ', '')):
            # if short_name in player.name.replace(' ', ''):  # スペース削除した名前と部分一致をチェック
                info = player
        return info
    
    def __score(self) -> Score:
        """現在のスコアを取得"""
        top = bottom = None
        if score := self.__soup.find(class_="score"):
            tds = score.find_all("td")
            top = int(tds[1].text)
            bottom = int(tds[3].text)
            score = Score(top, bottom)
        return score

    def __count(self) -> Count:
        """現在のボールカウントを取得"""
        s = b = o = None
        if sbo := self.__soup.find(class_="sbo"):
            b = len(sbo.find(class_="b").find("b").text)
            s = len(sbo.find(class_="s").find("b").text)
            o = len(sbo.find(class_="o").find("b").text)
            count = Count(s, b, o)
        return count

    def __pitcher(self) -> Optional[PlayerInfo]:
        """投手のIDと名前を取得"""
        info = None
        if pitcher := self.__soup.find(id=["pitcherL", "pitcherR"]):
            if a := pitcher.find(class_='nm_box').find("a"):     
                if match := re.search(r"[0-9]+", a.attrs['href']):
                    id = int(match.group(0))
                name = a.text
                handed = re.search(r"(.)投", pitcher.find(class_='dominantHand').text).group(1)
                info = PlayerInfo(id=id, handed=handed, name=name)
                print(f"投手: {info.__dict__}")
        return info

    def __batter(self) -> Optional[PlayerInfo]:
        """打者のIDと名前を取得"""
        info = None
        if batter := self.__soup.find(id="batter"):
            if a := batter.find(class_='nm_box').find("a"):
                if match := re.search(r"[0-9]+", a.attrs['href']):
                    id = int(match.group(0))
                name = a.text
                handed = re.search(r"(.)打", batter.find(class_='dominantHand').text).group(1)
                info = PlayerInfo(id, handed, name)
                print(f"打者: {info.__dict__}")
        return info

    def __b1_runner(self) -> Optional[PlayerInfo]:
        """1塁走者のIDと名前を取得"""
        info = None
        base = self.__soup.find(id="base1")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self.top_bottom)
        return info

    def __b2_runner(self) -> Optional[PlayerInfo]:
        """2塁走者のIDと名前を取得"""
        info = None
        base = self.__soup.find(id="base2")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self.top_bottom)
        return info

    def __b3_runner(self) -> Optional[PlayerInfo]:
        """3塁走者のIDと名前を取得"""
        info = None
        base = self.__soup.find(id="base3")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self.top_bottom)
        return info
    

    """
    結果と備考文字列を解析する関数
    """
    def __result_text(self) -> str:
        """現在の結果文字列を取得"""
        text = ""
        span = self.__soup.find(id="result").find("span")
        if span:
            text = span.text
        return text

    def __result_note_text(self) -> str:
        """現在の結果備考文字列を取得"""
        text = ""
        em = self.__soup.find(id="result").find("em")
        if em:
            text = em.text
        return text

    def __check_result_text(self, pattern: str) -> bool:
        """結果文字列に指定のパターンがあるかチェック"""
        if pattern in self.__result_text():
            print("event(result): ", CYAN + pattern + END)
            return True
        else:
            return False

    def __check_note_text(self, pattern: str) -> bool:
        """結果備考文字列に指定のパターンがあるかチェック"""
        if pattern in self.__result_note_text():
            print("event(note): ", CYAN + pattern + END)
            return True
        else:
            return False

    def __check_game_end(self) -> bool:
        """試合終了のチェック '試合終了'があるかチェック """
        return self.__check_result_text("試合終了")

    def __check_pinch_hitter(self) -> bool:
        """代打のチェック"""
        return self.__check_result_text("【代打】")

    def __check_change_pitcher(self) -> bool:
        """継投のチェック"""
        return self.__check_result_text("【継投】")

    def __check_change_defense(self) -> bool:
        """守備交代のチェック"""
        return self.__check_result_text("【守備】")

    def __check_change_runner(self) -> bool:
        """代走のチェック"""
        return self.__check_result_text("【代走】")

    def __check_intentional_walk(self) -> bool:
        """敬遠のチェック"""
        return self.__check_result_text("敬遠")

    def __check_balk(self) -> bool:
        """ボークのチェック"""
        return self.__check_result_text("ボーク")

    def __check_pick_off(self) -> bool:
        return self.__check_result_text("けん制 アウト")

    def __check_steal_success(self) -> bool:
        """盗塁成功のチェック"""
        return self.__check_note_text("盗塁成功（")

    def __check_steal_failure(self) -> bool:
        """盗塁失敗のチェック"""
        return self.__check_note_text("盗塁失敗（")

    # def __check_pick_off(self) -> bool:
    #     """けん制のチェック"""
    #     return self.__check_note_text("けん制")

    def __check_touch_out(self) -> bool:
        """走者タッチアウトのチェック"""
        return self.__check_note_text("タッチアウト")
    
    def __check_advance_base(self) -> bool:
        """走者進塁のチェック"""
        return self.__check_note_text("進塁")

    def __check_running_mistake(self) -> bool:
        """走者走塁失敗のチェック"""
        return self.__check_note_text("走塁死")

    def __check_wild_pich(self) -> bool:
        """暴投のチェック"""
        return self.__check_note_text("暴投")

    def __check_passed_ball(self) -> bool:
        """捕逸のチェック"""
        return self.__check_note_text("捕逸")

    def __check_bad_throw(self) -> bool:
        """悪送球のチェック"""
        return self.__check_note_text("悪送球")
    

    def __check_events(self) -> None:
        """イベントのチェック"""
        # ---------------------------------------------------------
        # 交代系イベント
        # ---------------------------------------------------------
        # 代打
        if self.__check_pinch_hitter():
            pass
        # 継投
        if self.__check_change_pitcher():
            pass
        # 代走
        if self.__check_change_runner():
            pass
        # 守備交代
        if self.__check_change_defense():
            pass

        # ---------------------------------------------------------
        # アウト系イベント
        # ---------------------------------------------------------
        # 牽制アウト
        if self.__check_pick_off():
            pass
        # 盗塁失敗
        if self.__check_steal_failure():
            self.steal_failure = True
            self.steal_failure_runners = self.__note_event_players('盗塁失敗')
            pass
        # タッチアウト
        if self.__check_touch_out():
            pass
        # 走塁死(盗塁ではない)
        if self.__check_running_mistake():
            pass
        
        # ---------------------------------------------------------
        # 進塁系イベント
        # ---------------------------------------------------------
        # 盗塁成功
        if self.__check_steal_success():
            self.steal_success = True
            self.steal_success_runners = self.__note_event_players('盗塁成功')
            pass
        # 進塁(盗塁ではない)
        if self.__check_advance_base():
            pass

        # ---------------------------------------------------------
        # 失策系イベント
        # ---------------------------------------------------------
        # 暴投
        if self.__check_wild_pich():
            pass
        # 捕逸
        if self.__check_passed_ball():
            pass
        # 悪送球
        if self.__check_bad_throw():
            pass
        # ボーク
        if self.__check_balk():
            # ボークは進塁なので打席継続
            pass

    def __steal_success_runners(self) -> List[PlayerInfo]:
        """盗塁成功したランナー情報"""
        infos = []
        note = self.__result_note_text()
        if short_names := re.findall(r"盗塁成功（(.+?)）", note):
            for short_name in short_names:
                info = self.__short_name_to_info(short_name, self.top_bottom)
                infos.append(info)
        return infos

    def __steal_failure_runners(self) -> List[PlayerInfo]:
        """盗塁失敗したランナー情報"""
        infos = []
        note = self.__result_note_text()
        if short_names := re.findall(r"盗塁失敗（(.+?)）", note):
            for short_name in short_names:
                info = self.__short_name_to_info(short_name, self.top_bottom)
                infos.append(info)
        return infos

    def __note_event_players(self, pattarn) -> List[PlayerInfo]:
        """イベントの発生した選手情報"""
        infos = []
        note = self.__result_note_text()
        if short_names := re.findall(r"{}（(.+?)）".format(pattarn), note):
            for short_name in short_names:
                info = self.__short_name_to_info(short_name, self.top_bottom)
                infos.append(info)
        return infos


    def __check_batter_box_end(self) -> bool:
        """
        打席終了のチェック(打席結果がある場合は打席終了)
        """
        _, result = self.__direction_and_result()
        if result == None:
            return False
        else:
            return True

    def __pitch_detail(self) -> List[Pitch]:
        pitches = []
        cources = []

        tables = self.__soup.find(id='pitchesDetail').find_all('section')[1].find_all('table')
        if len(tables) >= 3:
            spans = tables[0].find('tbody').find('tr').find('td').find_all('span', class_='bb-icon__ballCircle')
            for span in spans:
                pos_text = span.attrs['style']
                m = re.findall(r'[0-9]+', pos_text)
                top = int(m[0])
                left = int(m[1])
                cource = Cource(top, left)
                cources.append(cource)

            trs = tables[2].find('tbody').find_all('tr')
            if len(cources) != len(trs):   # データ不足の場合はエラーをログに出す
                print('投球データ長不整合エラー')

            for tr, cource in zip(trs, cources):
                tds = tr.find_all('td')
                number = int(tds[0].text.strip())
                number_of = int(tds[1].text)
                kind = tds[2].text
                if tds[3].text == '-':
                    speed = None
                else:
                    if match := re.search(r'[0-9]+', tds[3].text):
                        speed = int(match.group(0))
                result = tds[4].text.strip().split("\n")[0]
                pitch = Pitch(number, number_of, kind, speed, cource, result)
                pitches.append(pitch)
        return pitches
# end of class Event:





if __name__ == '__main__':
    """メイン処理"""

    args = sys.argv
    print(args)
    if len(args) > 1:
        if str.isdecimal(args[1]):
            game_id = int(args[1])
        else:
            print("Game ID numebr is not deciaml! ID={}".format(args[1]))
            exit(0)        
    else:
        game_id = 2021011388
    
    inning_sleep = 2 #秒
    game_sleep = 10 #秒

    batter_box_stats = []
    inning = Inning()
    event = Event(game_id, inning)
    while not event.game_end:
        """データ取得"""
        print("Score:       ", event.score)
        print("Count:       ", event.count)
        print("Batter:      ", event.batter)
        print("Pitcher:     ", event.pitcher)
        print("1B:          ", event.b1_runner)
        print("2B:          ", event.b2_runner)
        print("3B:          ", event.b3_runner)
        print("Direction:   ", event.direction)
        print("Result:      ", event.result)
        print("Pitches:     ", event.pitches)
        if event.inning_end:
            """イニング終了時処理"""
            print("{}回 {} ".format(event.inning_num, ["表", "裏"][event.top_bottom-1]) + 
                BOLD + [event.visitor_team, event.home_team][event.top_bottom-1] + END + 
                "の攻撃終了 {}秒待ち".format(inning_sleep))
            print("-"*80)
            time.sleep(inning_sleep)
        if event.batter_box_end:
            batter_box_stat = [
                event.game_id, event.visitor_team, event.home_team, event.inning_num, event.top_bottom, event.batter_num,
                event.score, event.count, event.batter, event.pitcher,
                event.b1_runner, event.b2_runner, event.b3_runner, event.direction, event.result, event.pitches
                ]
            batter_box_stats.append(batter_box_stat)
        event = event.next_event()
    
    # PandasでJSONに保存
    batter_box_columns = [
        "id", "visitor", "home", "inning_num", "top_bottom", "batter_num",
        "score", "count", "batter", "pitcher",
        "1b", "2b", "3b", "direction", "result", "pitches",
    ]
    bat_box_df = pd.DataFrame(batter_box_stats, columns=batter_box_columns)
    bat_box_df.to_json("./{}-bat.json".format(event.game_id), orient='records', force_ascii=False)




