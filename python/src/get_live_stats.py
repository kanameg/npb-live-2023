# -*- coding: utf-8 -*-
import datetime
import time
from typing import Dict, List, Optional, Tuple, TypedDict
import requests
from bs4 import BeautifulSoup
import re
import sys
import pandas as pd


RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
CYAN = '\033[36m'
UNDERLINE = '\033[4m'
BOLD = '\033[1m'
END = '\033[0m'



class PlayerInfo(TypedDict):
    """
    選手情報クラス
    """
    id: int
    name: str

class PitchCource(TypedDict):
    """
    投球コース
    """
    縦: int
    横: int

class PitchDetail(TypedDict):
    """
    投球詳細
    """
    番号: int
    投球数: int
    球種: str
    球速: Optional[int]
    コース: PitchCource
    結果: str


class Inning:
    """
    イニング情報クラス
    """ 
    def __init__(self, inning_number: int=1, top_bottom: int=1, bat_number: int=1, event_number: int=0) -> None:
        self.inning_number = inning_number
        self.top_bottom = top_bottom
        self.bat_number = bat_number
        self.event_number = event_number
        return

    # ------------------------------------------------------
    # 出力
    # ------------------------------------------------------
    def __repr__(self) -> str:
        return "IN: {}, TB: {}, BN: {}, EN: {}".format(self.inning_number, self.top_bottom, self.bat_number, self.event_number)
    

class GameSchedule:
    """
    試合スケジュール情報クラス
    """
    def __init__(self, date: datetime.date) -> None:
        # ------------------------------------------------------
        # Requests用のUser-agent
        # ------------------------------------------------------
        self._date = date
        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        url = "https://baseball.yahoo.co.jp/npb/schedule/?date={}".format(self._date.strftime("%Y-%m-%d"))
        print(url)
        res = requests.get(url, headers=requests_header)
        self._soup = BeautifulSoup(res.text, "lxml")
        return

    # ------------------------------------------------------
    # 当日の試合IDを取得
    # ------------------------------------------------------
    def game_ids(self) -> List[int]:
        ids = []
        if self.__check_game_day():            
            for link in self._soup.find_all(class_='bb-score__content'):
                if match := re.search(r'[0-9]{10}', link.attrs['href']):
                    id = int(match.group(0))
                    if '試合終了' in link.find(class_='bb-score__link').text:
                        ids.append(id)
        return ids

    # ------------------------------------------------------
    # ゲームのある日かどうかのチェック
    # ------------------------------------------------------
    def __check_game_day(self) -> bool:
        if no_data := self._soup.find(class_="bb-noData"):
            if "試合はありません" in no_data.text:
                return False
        return True
        

class GameEvent:
    """
    試合イベント情報クラス
    """
    def __init__(self, game_id: int, inning: Inning) -> None:
        # 状況と結果
        self.score: Dict[str, Optional[int]]
        self.sbo: Dict[str, Optional[int]]
        self.pitcher: Optional[PlayerInfo]
        self.batter: Optional[PlayerInfo]
        self.b1: Optional[PlayerInfo]
        self.b2: Optional[PlayerInfo]
        self.b3: Optional[PlayerInfo]
        self.direction: Optional[str]
        self.result: Optional[str]
        self.pitch_detail: List[PitchDetail]

        # ------------------------------------------------
        # インング情報を保存
        # ------------------------------------------------
        self._inning = inning
        self.inning_number: int = self._inning.inning_number
        self.top_bottom: int = self._inning.top_bottom
        self.bat_number:int = self._inning.bat_number
        self.event_number:int = self._inning.event_number

        self._direction_check = [
            "右中", "左中", "投", "捕", "一", "二", "三", "遊", "右", "中", "左",
        ]

        self._result_check = [
            '空三振', '見三振', 'バ三振', '暴振逃', '逸振逃',       # 三振系(3文字)
            '故意四', '犠打失', '犠飛失', '規則反',                 # 守備なし系(3文字)
            '四球', '死球', '打妨', '守妨',                         # 守備なし系 (2文字)
            'ゴロ', '犠飛', '邪飛', '併打', '犠打', '犠野', '野選', # アウト系(2文字)
            '飛', '直', '失',                                       # アウト系(1文字)
            '安', '２', '３', '走本', '本',                         # ヒット系
        ]

        requests_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        requests_header = {
            'User-Agent': requests_user_agent
        }
        # 打席ページを取得
        url = "https://baseball.yahoo.co.jp/npb/game/{}/score?index={:02}{:01}{:02}{:02}".format(
            game_id, self.inning_number, self.top_bottom, self.bat_number, self.event_number
        )
        print(url)
        try: 
            res = requests.get(url, headers=requests_header)
        except requests.exceptions.RequestException as e:
            print("requests error occur {}".format(e))
        self._soup = BeautifulSoup(res.text, "lxml")

        # 受信HTMLを解析開始
        # ------------------------------------------------
        # チーム情報を保存
        # ------------------------------------------------
        self.visitor_team = self.__visitor_team()
        self.home_team = self.__home_team()

        # ------------------------------------------------
        # 次イベントのチェック
        # ------------------------------------------------
        # フラグ
        self.game_end = False
        self.inning_end = False
        self.batter_box_end = False
        # イベント系フラグ
        self.steal_success = False
        self.steal_failure = False

        if self.__check_error_page():       # エラーページ
            # ページ読み込みエラー (ありえないパターン)
            print(RED + "Page Error" + END)
            exit(0)
        else:
            if self.__check_game_end():
                self.game_end = True
            elif self.__check_inning_end():
                self.inning_end = True
            else:
                pass
        # ------------------------------------------------
        # イベントチェック
        # ------------------------------------------------
        self.__check_events()

        # ------------------------------------------------
        # 継続もしくは打席完了の場合
        # ------------------------------------------------
        if self.game_end:
            # 試合終了ページは何もしない
            pass
        else:
            # ------------------------------------------------
            # フィールド選手を取得
            # ------------------------------------------------
            self._home_members = self.__home_members()
            self._visitor_members = self.__visitor_members()
            # ------------------------------------------------
            # 投球一覧を取得
            # ------------------------------------------------
            self._total_balls = self.__total_balls()
            # ------------------------------------------------
            # フィールド状況取得
            # ------------------------------------------------
            self.score = self.__score()
            self.sbo = self.__sbo()
            self.b1 = self.__b1()
            self.b2 = self.__b2()
            self.b3 = self.__b3()
            
            self.batter_box_end = self.__check_batter_box_end()
            # ------------------------------------------------
            # 打席完了の場合
            # ------------------------------------------------
            if self.batter_box_end:
                # ------------------------------------------------
                # 投手・打者を取得
                # ------------------------------------------------
                self.pitcher = self.__pitcher()
                self.batter = self.__batter()
                # ------------------------------------------------
                # 打席結果を取得
                # ------------------------------------------------
                self.direction, self.result = self.__direction_and_result()
                self.pitch_detail = self.__pitch_detail()
                print(BLUE + "打席{}終了".format(self.bat_number) + END)
        return

    def __check_error_page(self) -> bool:
        """取得ページがエラーページかのチェック"""
        yf_error = self._soup.find(class_="yf-error__title")
        if yf_error:
            error = True
        else:
            error = False
        return error

    def __check_inning_end(self) -> bool:
        """イニング終了かどうかのチェック"""
        next_inning_number, next_top_bottom, _, _ = self.__next_index()
        if next_inning_number != self.inning_number or next_top_bottom != self.top_bottom:
            return True
        else: 
            return False

    def __visitor_team(self) -> str:
        """ビジターチーム名を取得"""
        bb_team = self._soup.find_all(class_="bb-gameScoreTable__team")
        team: str = bb_team[0].text
        return team

    def __home_team(self) -> str:
        """ホームチーム名を取得"""
        bb_team = self._soup.find_all(class_="bb-gameScoreTable__team")
        team: str = bb_team[1].text
        return team

    def __home_members(self) -> List[PlayerInfo]:
        """ホーム出場選手の一覧を取得"""
        members = []
        tables = self._soup.find(id='pitchesDetail').find_all('section')[0].find_all('table')
        trs = tables[0].find_all('tr')[1:]
        for tr in trs:
            tds = tr.find_all('td')
            name = tds[2].text
            if match := re.search(r'[0-9]+', tds[2].find('a').attrs['href']):
                id = int(match.group(0))
            info: PlayerInfo = {'name': name, 'id': id}
            members.append(info)
        print(f"members: {members}")
        return members

    def __visitor_members(self) -> List[PlayerInfo]:
        """ビジター出場選手の一覧を取得"""
        members = []
        tables = self._soup.find(id='pitchesDetail').find_all('section')[-1].find_all('table')
        trs = tables[0].find_all('tr')[1:]
        for tr in trs:
            tds = tr.find_all('td')
            name = tds[2].text
            if match := re.search(r'[0-9]+', tds[2].find('a').attrs['href']):
                id = int(match.group(0))
            info: PlayerInfo = {'name': name, 'id': id}
            members.append(info)
        print(f"members: {members}")
        return members

    def __short_name_to_info(self, short_name, top_bottom) -> Optional[PlayerInfo]:
        """選手略名から選手IDと名前を取得"""
        if top_bottom == 1:
            members = self._visitor_members
        else:
            members = self._home_members

        info: Optional[PlayerInfo] = None
        for member in members:
            if short_name in member['name'].replace(' ', ''):  # スペース削除した名前と部分一致をチェック
                id = member['id']
                name = member['name']
                info = {'id': id, 'name': name}
        return info
    
    def __score(self) -> Dict[str, Optional[int]]:
        """現在のスコアを取得"""
        score_t = score_b = None
        score = self._soup.find(class_="score")
        if score:
            tds = score.find_all("td")
            score_t = int(tds[1].text)
            score_b = int(tds[3].text)
        return {"表": score_t, "裏": score_b}

    def __sbo(self) -> Dict[str, Optional[int]]:
        """現在のボールカウントを取得"""
        s = b = o = None
        sbo = self._soup.find(class_="sbo")
        if sbo:
            b = len(sbo.find(class_="b").find("b").text)
            s = len(sbo.find(class_="s").find("b").text)
            o = len(sbo.find(class_="o").find("b").text)
        return {"S": s, "B": b, "O": o}

    def __pitcher(self) -> Optional[PlayerInfo]:
        """投手のIDと名前を取得"""
        info: Optional[PlayerInfo] = None
        if pitcher := self._soup.find(id=["pitcherL", "pitcherR"]):        
            a = pitcher.find(class_='nm_box').find("a")
            if match := re.search(r"[0-9]+", a.attrs['href']):
                id = int(match.group(0))
            name = a.text
            handed = batter.find(class_='dominantHand').text
            info = {'id': id, 'handed': handed, 'name': name}
        return info

    def __batter(self) -> Optional[PlayerInfo]:
        """打者のIDと名前を取得"""
        info: Optional[PlayerInfo] = None
        if batter := self._soup.find(id="batter"):
            a = batter.find(class_='nm_box').find("a")
            if match := re.search(r"[0-9]+", a.attrs['href']):
                id = int(match.group(0))
            name = batter.find(class_='nm_box').find("a").text
            handed = batter.find(class_='dominantHand').text
            info = {'id': id, 'handed': handed, 'name': name}
            print(f"batter: {info}")
        return info

    def __b1(self) -> Optional[PlayerInfo]:
        """1塁走者のIDと名前を取得"""
        info: Optional[PlayerInfo] = None
        base = self._soup.find(id="base1")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self._inning.top_bottom)
        return info

    def __b2(self) -> Optional[PlayerInfo]:
        """2塁走者のIDと名前を取得"""
        info: Optional[PlayerInfo] = None
        base = self._soup.find(id="base2")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self._inning.top_bottom)
        return info

    def __b3(self) -> Optional[PlayerInfo]:
        """3塁走者のIDと名前を取得"""
        info: Optional[PlayerInfo] = None
        base = self._soup.find(id="base3")
        if base:
            text = base.text.strip()
            short_name = re.findall(r'[0-9]+ (.+)', text)[0]
            info = self.__short_name_to_info(short_name, self._inning.top_bottom)
        return info
    
    # ---------------------------------------------------------
    # 次URLのインング情報を取得
    # ---------------------------------------------------------
    def __next_index(self) -> Tuple[int, int, int, int]:
        index = self._soup.find(id="btn_next").attrs['index']
        inning_number = int(index[0:2])
        top_bottom = int(index[2])
        bat_number = int(index[3:5])
        event_number = int(index[6])
        return inning_number, top_bottom, bat_number, event_number

    # ---------------------------------------------------------
    # 次イニング情報を取得
    # ---------------------------------------------------------
    def next_inning(self) -> Inning:
        inning_number, top_bottom, bat_number, event_number = self.__next_index()
        next_inning = Inning(inning_number, top_bottom, bat_number, event_number)
        return next_inning

    def __result_text(self) -> str:
        """現在の結果文字列を取得"""
        text = ""
        span = self._soup.find(id="result").find("span")
        if span:
            text = span.text
        return text

    def __result_note_text(self) -> str:
        """現在の結果備考文字列を取得"""
        text = ""
        em = self._soup.find(id="result").find("em")
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

    def __check_steal_success(self) -> bool:
        """盗塁成功のチェック"""
        return self.__check_note_text("盗塁成功（")

    def __check_steal_failure(self) -> bool:
        """盗塁失敗のチェック"""
        return self.__check_note_text("盗塁失敗（")

    def __check_pick_up_success(self) -> bool:
        """けん制成功のチェック"""
        return self.__check_note_text("けん制")

    def __check_touch_out(self) -> bool:
        """走者タッチアウトのチェック"""
        return self.__check_note_text("タッチアウト")
    
    def __check_advance_base(self) -> bool:
        """走者進塁のチェック"""
        return self.__check_note_text("進塁")

    def __check_base_running_mistake(self) -> bool:
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
        # 盗塁失敗
        if self.__check_steal_failure():
            self.steal_failure = True
            pass
        # タッチアウト
        if self.__check_touch_out():
            pass
        # けん制死
        if self.__check_pick_up_success():
            pass
        # 走塁死(盗塁ではない)
        if self.__check_base_running_mistake():
            pass
        
        # ---------------------------------------------------------
        # 進塁系イベント
        # ---------------------------------------------------------
        # 盗塁成功
        if self.__check_steal_success():
            self.steal_success = True
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

    
    def __total_balls(self) -> List[str]:
        """投球一覧を取得"""
        total_balls = []
        # 打者が途中で交代するとballlistが複数あるのでfind_allで取得
        ball_lists = self._soup.find_all(class_="balllist")
        if ball_lists:
            for ball_list in ball_lists:
                balls = list(map(lambda td: str(td.text), ball_list.find_all("td")))
                total_balls.extend(balls)
        # データがない場合は無球で申告敬遠のみ ここ少し微妙?
        # if "敬遠" in self.__result_text():
        if self.__check_intentional_walk():
            total_balls.append("故意四")

        return total_balls

    def __direction_and_result(self) -> Tuple[Optional[str], Optional[str]]:
        """打球方向と結果を取得"""
        direction = None
        result = None
        if len(self._total_balls):
            last_pich = self._total_balls[-1]
            for check in self._result_check:
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

    # ---------------------------------------------------------
    # 打席終了チェック(打席結果がある場合は打席終了)
    # ---------------------------------------------------------
    def __check_batter_box_end(self) -> bool:
        _, result = self.__direction_and_result()
        if result == None:
            return False
        else:
            return True

    # ---------------------------------------------------------
    # 投球詳細結果を取得
    # ---------------------------------------------------------
    def __pitch_detail(self) -> List[PitchDetail]:
        details = []
        cources = []

        tables = self._soup.find(id='pitchesDetail').find_all('section')[1].find_all('table')
        if len(tables) >= 3:
            spans = tables[0].find('tbody').find('tr').find('td').find_all('span', class_='bb-icon__ballCircle')
            for span in spans:
                pos_text = span.attrs['style']
                m = re.findall(r'[0-9]+', pos_text)
                cource: PitchCource = {
                    '縦': int(m[0]),
                    '横': int(m[1])
                }
                cources.append(cource)

            trs = tables[2].find('tbody').find_all('tr')
            if len(cources) != len(trs):   # データ不足の場合はエラーをログに出す
                print('投球データ長不整合エラー')

            for tr, cource in zip(trs, cources):
                tds = tr.find_all('td')
                count = int(tds[0].text.strip())
                total_count = int(tds[1].text)
                kind = tds[2].text
                if tds[3].text == '-':
                    speed = None
                else:
                    if match := re.search(r'[0-9]+', tds[3].text):
                        speed = int(match.group(0))
                result = tds[4].text.strip().split("\n")[0]
                detail: PitchDetail = {
                    '番号': count,
                    '投球数': total_count,
                    '球種': kind,
                    '球速': speed,
                    'コース': cource,
                    '結果': result
                }
                details.append(detail)
        return details








# ------------------------------------------------------
# メインの先頭
# ------------------------------------------------------
if __name__ == '__main__':

    # ------------------------------------------------------
    # 取得日付
    # ------------------------------------------------------
    args = sys.argv
    if str.isdecimal(args[1]) and str.isdecimal(args[2]) and str.isdecimal(args[3]):
        year = int(args[1])
        month = int(args[2])
        day = int(args[3])
    else:
        print("Date numebr is not deciaml! year={}, month={}, day={}".format(args[1], args[2], args[3]))
        exit(0)

    # ------------------------------------------------------
    # 指定日のゲーム情報を取得
    # ------------------------------------------------------
    date = datetime.date(year, month, day)
    date_text = date.strftime("%Y-%m-%d")

    inning_sleep = 2 # 秒
    game_sleep = 10 # 秒

    # ------------------------------------------------------
    # ゲームID一覧を取得
    # ------------------------------------------------------
    schedule = GameSchedule(date)
    game_ids = schedule.game_ids()
    print("取得試合ID一覧: {}".format(game_ids))

    batter_box_result = []
    for game_id in game_ids:
        print(GREEN + "試合ID:{} 取得開始".format(game_id) + END)
        print("-"*80)
        # event取得
        inning = Inning()  # イニング情報初期化
        event = GameEvent(game_id, inning)
        while not event.game_end:
            # イング情報
            inning_number = event.inning_number
            top_bottom = event.top_bottom
            bat_number = event.bat_number

            # スコアとカウント
            score = event.score
            sbo = event.sbo

            # 走者情報
            b1 = event.b1
            b2 = event.b2
            b3 = event.b3
            if event.batter_box_end:
                pitcher = event.pitcher # 投手
                batter = event.batter   # 打者

                # 打席結果
                direction = event.direction
                result = event.result
                # 投球結果
                pitch_detail = event.pitch_detail

                batter_box = [date_text, game_id, inning_number, top_bottom, bat_number, score, sbo, batter, pitcher, b1, b2, b3, direction, result, pitch_detail]
                batter_box_result.append(batter_box)

                # イニング終了 (攻守交代)
                if event.inning_end:
                    print("{}回 {} ".format(event.inning_number, ["表", "裏"][event.top_bottom-1]) + 
                        BOLD + [event.visitor_team, event.home_team][event.top_bottom-1] + END + 
                        "の攻撃終了 {}秒待ち".format(inning_sleep))
                    print("-"*80)
                    time.sleep(inning_sleep)
            else:
                pass
                
            # event更新
            next_inning = event.next_inning()
            event = GameEvent(game_id, next_inning)
        # 試合終了
        print(GREEN + "試合ID:{} 取得終了 {}秒待ち".format(game_id, game_sleep) + END)
        print("-"*80)
        time.sleep(game_sleep)

    
    # ---------------------------------------------
    # DataFrameに変換後JSON出力
    # ---------------------------------------------
    batter_box_columns = [
        "試合日", "試合ID", "回", "表裏", "打者数", "スコア", "カウント", "打者", "投手",
        "1塁走者", "2塁走者", "3塁走者", "打球方向", "結果", "投球詳細",
    ]    
    bat_df = pd.DataFrame(batter_box_result, columns=batter_box_columns)
    bat_df.to_json("./live-stats/{}-bat.json".format(date_text), orient='records', force_ascii=False)

    # 終了
    print(GREEN + "{} 全ゲーム取得終了 !!".format(date_text) + END)
        