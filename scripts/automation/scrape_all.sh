#!/bin/bash
# 全大会スクレイピングシェルスクリプト

echo "======================================================================"
echo "全大会スクレイピング開始"
echo "======================================================================"

COMPETITIONS=(
    "world-rugby-internationals:World Rugby Internationals"
    "gallagher-premiership:Gallagher Premiership"
    "urc:United Rugby Championship"
    "rugby-championship:The Rugby Championship"  
    "autumn-nations-series:Autumn Nations Series"
    "super-rugby-pacific:Super Rugby Pacific"
    "epcr-champions:EPCR Champions Cup"
    "epcr-challenge:EPCR Challenge Cup"
    "top14:Top 14"
    "league-one:Japan Rugby League One"
    "six-nations:Six Nations"
    "six-nations-women:Women's Six Nations"
    "six-nations-u20:U20 Six Nations"
)

SUCCESS=0
FAILED=()

for item in "${COMPETITIONS[@]}"; do
    IFS=':' read -r comp_id comp_name <<< "$item"
    
    echo ""
    echo "======================================================================"
    echo "スクレイピング中: $comp_name ($comp_id)"
    echo "======================================================================"
    
    if python -m src.main "$comp_id"; then
        echo "✅ $comp_name 完了"
        ((SUCCESS++))
    else
        echo "❌ $comp_name 失敗"
        FAILED+=("$comp_name")
    fi
done

echo ""
echo "======================================================================"
echo "スクレイピング完了サマリー"
echo "======================================================================"
echo "✅ 成功: $SUCCESS/${#COMPETITIONS[@]}大会"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "❌ 失敗した大会:"
    for comp in "${FAILED[@]}"; do
        echo "  - $comp"
    done
    exit 1
else
    echo ""
    echo "🎉 全大会のスクレイピングが成功しました！"
    exit 0
fi
