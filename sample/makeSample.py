import pandas as pd
import random
import os
from datetime import datetime, timedelta

# 設定
num_rows = 200
products = ["Flagship-X1", "MidRange-M2", "Entry-E3", "RF-Test-Jig", "Antenna-Module"]
prices = [120000, 65000, 30000, 15000, 8000]

# 区切り文字：半角スペース4つ
SEP = "    "

def generate_sample_file(headers, filename):
    data = []
    start_date = datetime(2026, 4, 1)
    
    for _ in range(num_rows):
        p_idx = random.randint(0, len(products) - 1)
        qty = random.randint(1, 50)
        u_price = prices[p_idx]
        sales = qty * u_price
        royalty = int(sales * 0.05)
        date = (start_date + timedelta(days=random.randint(0, 14))).strftime('%Y/%m/%d')
        
        # データを文字列のリストにする
        row = [date, products[p_idx], str(qty), str(u_price), str(sales), str(royalty)]
        data.append(row)
    
    # ファイル書き出し (to_csvを使わず、手動で結合して書き込む)
    try:
        with open(filename, 'w', encoding='utf-8-sig') as f:
            # ヘッダーを書き込み
            f.write(SEP.join(headers) + '\n')
            # 各行を書き込み
            for row in data:
                f.write(SEP.join(row) + '\n')
        print(f"作成完了: {filename}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# 保存先フォルダを確保
os.makedirs('sample', exist_ok=True)

# --- 3つの異なるヘッダーパターンで生成 ---

# パターン1: 日本語（標準）
generate_sample_file(
    ['日付', '商品名', '数量', '製品単価', '売上', 'ロイヤリティ'], 
    'sample/sales_sample_A.txt'
)

# パターン2: 日本語（表記揺れ）
generate_sample_file(
    ['売上日', '製品名', '個数', '単価', '集計金額', '手数料'], 
    'sample/sales_sample_B.txt'
)

# パターン3: 英語（表記揺れ）
generate_sample_file(
    ['Date', 'ItemName', 'Qty', 'UnitPrice', 'TotalSales', 'RoyaltyFee'], 
    'sample/sales_sample_C.txt'
)