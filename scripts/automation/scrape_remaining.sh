#!/bin/bash
# 全大会スクレイピング（修正版）

echo "=== 全大会スクレイピング開始 ==="
echo ""

# 成功した大会
SUCCESSFUL_COMPETITIONS=(
    "m6n"
    "w6n"
    "u6n"
    "premier"
    "urc"
    "wr"
    "jrlo"
)

# 未実装/失敗する大会
PENDING_COMPETITIONS=(
    "epcr-challenge"
    "epcr-champions"
    "t14"
    "srp"
    "trc"
    "ans"
    "nc"
)

# 成功した大会をスキップして確認のみ
echo "✅ 既にスクレイピング済みの大会:"
for comp in "${SUCCESSFUL_COMPETITIONS[@]}"; do
    echo "  - $comp"
done
echo ""

# 残りの大会を試行
echo "🔄 残りの大会をスクレイピング:"
for comp in "${PENDING_COMPETITIONS[@]}"; do
    echo "------------------------------------------------"
    echo "🔄 スクレイピング中: $comp"
    python -m src.main "$comp" 2>&1 | tail -15
    
    if [ $? -eq 0 ]; then
        echo "✅ $comp: 成功"
    else
        echo "❌ $comp: 失敗"
    fi
    echo ""
done

echo "=== 全大会スクレイピング完了 ==="
echo ""
echo "📊 結果確認:"
find data/matches -name "*.json" -type f | sort
