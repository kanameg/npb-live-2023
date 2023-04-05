#!/bin/bash

FILE=./game_days.txt

while read LINE
do
    # スペースで分割
    ARR=(${LINE// / })

    # 月 日に分割
    m=${ARR[0]}
    d=${ARR[1]}

    # 0埋め
    M=$(printf "%02d\n" "${m}")
    D=$(printf "%02d\n" "${d}")

    # ダウンロード開始
    if [ ! -f ../pitcher-stats/2022-${M}-${D}.csv ]; then
        python -u pitcher_stats.py 2022 ${m} ${d} up 2>&1 | tee -a ../pitcher_stats.log
        echo "2022-${M}-${D} ダウンロード完了"
        st=$((${RANDOM} % 5 + 5))
        echo ${st}秒待
        sleep ${st}
    else
        echo "2022-${M}-${D} ダウンロード済み"
    fi
    
done < ${FILE}