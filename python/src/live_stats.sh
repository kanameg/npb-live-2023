#!/bin/bash

FILE=./game_days.txt

while read LINE
do
    # スペースで分割
    ARR=(${LINE// / })

    # 月 日に分割
    y=${ARR[0]}
    m=${ARR[1]}
    d=${ARR[2]}

    # 0埋め
    Y=$(printf "%04d\n" "${y}")
    M=$(printf "%02d\n" "${m}")
    D=$(printf "%02d\n" "${d}")

    # ダウンロード開始
    if [ ! -f ../live-stats/${Y}-${M}-${D}-bat.json ]; then
        python -u ./live_stats.py ${Y} ${M} ${D} 2>&1 | tee -a ../live_stats.log
        echo "${Y}-${M}-${D} ダウンロード完了"
        st=$((${RANDOM} % 10 + 10))
        echo ${st}秒待
        sleep ${st}
    else
        echo "${Y}-${M}-${D} ダウンロード済み"
    fi
    
done < ${FILE}