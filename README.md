[README.md](https://github.com/user-attachments/files/33904572/README.md)
日本株スクリーニングツール
Python・SQLite・yfinanceを使用して 日本株の株価を取得するプログラムです。

機能
ウォッチリスト銘柄の株価取得
SQLiteへの保存
前回比計算
出来高取得
ROE取得
PBR取得
時価総額取得
移動平均線(25日、75日)計算
条件に一致した銘柄の表示
使用ライブラリ
pip install yfinance pandas
実行方法
python get_value.py
DB構造
stock

code
company_name
price
volume
update_time
