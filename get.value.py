import sqlite3
import yfinance as yf
import pandas as pd
import unicodedata


#指定以上の文字数だと「...」で切り捨て
def truncate_by_width(text, max_width):
    current_width = 0
    result = []
    for char in str(text):
        char_width = (
            2 if unicodedata.east_asian_width(char) in ("W", "A", "F") else 1
        )
        if current_width + char_width > max_width - 1:
            result.append("…")
            break
        result.append(char)
        current_width += char_width
    return "".join(result)

conn = sqlite3.connect("stock.db")

cur = conn.cursor()

#SQLiteのファイル生成
cur.execute("""
CREATE TABLE IF NOT EXISTS stock (
    code TEXT,
    company_name TEXT,
    price REAL,
    volume INTEGER, 
    update_time TEXT
)
""")

from datetime import datetime
now = datetime.now()

# codes = 
#          #輸送用機器
#          #情報・通信業
#          #銀行業
#          #保険業
#          #卸売業
#          ]

df_codes = pd.read_sql_query(
    "SELECT code FROM watch_list", 
    conn
)

cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)

codes = df_codes["code"].tolist()

valid_codes = []

for code in codes:
    # print("取得中：", code)

    ticker = yf.Ticker(code)
    info = ticker.info
    company_name = info.get(
        "longName",
        "会社名取得失敗"
    )
    short_name = truncate_by_width(company_name, 20)

    #株価
    price = info.get(
        "currentPrice",
        None
    )
    if price is None:
        print(code, "取得失敗")
        continue

    #出来高
    volume = info.get(
        "volume", 
        0
    )

    hist = ticker.history(period="3mo")
    #25日線
    ma25 = hist["Close"].rolling(25).mean().iloc[-1]
    #75日線
    ma75 = hist["Close"].rolling(75).mean().iloc[-1]

    #20日平均出来高
    ave_volume = hist["Volume"].rolling(20).mean().iloc[-1]

    #ROE
    roe = info.get("returnOnEquity", None)
    roe_percent = (
        roe * 100
        if roe is not None
        else None
    )
    #PBR
    pbr = info.get("priceToBook", None)
    #時価総額
    market_cap = info.get("marketCap", None)
    market_cap_oku = (
        market_cap / 1000000000
        if market_cap 
        else 0
    )

    #取得失敗コード
    if (
        roe is not None
        and pbr is not None
        and market_cap is not None
    ):
        valid_codes.append(code)
        continue

    # print(code, company_name, price)

#株価取得企業の企業コードの入力
    cur.execute(
     """
     INSERT INTO stock
     VALUES (?, ?, ?, ?, ?)
     """,
        (
            code,
            company_name,
            price,
            volume, 
            now
        )
    )   

    #表形式で保存
    df = pd.read_sql_query(
        f"""
        SELECT * FROM stock 
        WHERE code = '{code}' 
        ORDER BY update_time DESC 
        LIMIT 1
        """,
        conn
    )

    if len(df) >= 2:

        latest_price = df.iloc[0]["price"]
        previous_price = df.iloc[1]["price"]

        difference = latest_price - previous_price

        change_rate = (
            difference / previous_price
        ) * 100

        if latest_price is None or previous_price is None:
            print(code, "価格取得失敗")
            continue

        if(
            latest_price <= 1000    #株価
            and change_rate > 5.0   #前日比
            and latest_price > ma25 #上昇トレンド
            and ma25 > ma75         
            and volume > ave_volume * 2 #出来高増加
            and roe_percent >= 10   #ROE10%以上
            and pbr <= 1.5          #PBR1.5以下
            and market_cap_oku >= 100   #時価総額100億以上
        ):
            # print(
            #     code,
            #     short_name,
            #     latest_price,
            #     previous_price,
            #     f"{change_rate:.2f}%"
            # )
            print(
                f"{code:<6} "
                f"{short_name:<20} "
                f"{latest_price:>10,} "
                f"{previous_price:>10,} "
                f"{change_rate:>7.2f}%"
            )

    # else:
    #     print(code, "履歴不足")

        # print(
        #     f"{code:<6} "
        #     f"{short_name:<20} "
        #     f"{latest_price:>10,} "
        #     f"{previous_price:>10,} "
        #     f"{change_rate:>7.2f}%"
        # )

    #条件付き表示
    # print(result.to_string(index=False))

    # # 表の表示
    # print(df.to_string(index=False))

#表の100行以降は削除
cur.execute("""
DELETE FROM stock
WHERE rowid NOT IN (
    SELECT rowid
    FROM stock
    ORDER BY update_time DESC
    LIMIT 150
)
""")

conn.commit()
conn.close()


print("保存完了")
print(now)
