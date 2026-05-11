#!/usr/bin/env python3
"""
Nasdaq 100 リアルタイム指数トラッカー
yfinance ライブラリを使用して Nasdaq 100 (^NDX) の最新情報を取得し、
現在値・変動幅・日中取引レンジなどを表示します。
"""

import sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


def main():
    # yfinance のインポートを試みる（インストールされていない場合は案内を表示）
    try:
        import yfinance as yf
    except ImportError:
        print("【エラー】yfinance がインストールされていません。")
        print("以下のコマンドを実行してインストールしてください：")
        print("  pip install yfinance")
        sys.exit(1)

    # Nasdaq 100 のティッカーシンボル（指数の場合は先頭に ^ が付く）
    ticker_symbol = "^NDX"
    ticker = yf.Ticker(ticker_symbol)

    # 株価情報を取得（fast_info は軽量かつ高速）
    try:
        fast = ticker.fast_info
    except Exception as e:
        print(f"【エラー】データ取得に失敗しました: {e}")
        print("ネットワーク接続を確認するか、しばらく時間を置いてから再試行してください。")
        sys.exit(1)

    # 現在値と前日終値の取得
    current_price = fast.get("lastPrice", None)
    previous_close = fast.get("regularMarketPreviousClose", None)

    # 日中の取引レンジ（高値と安値）
    day_high = fast.get("dayHigh", None)
    day_low = fast.get("dayLow", None)

    # 日本時間での現在時刻を整形
    jst = ZoneInfo("Asia/Tokyo")
    now_jst = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    # 結果の表示
    print("=" * 55)
    print("  Nasdaq 100 リアルタイム指数 (^NDX)")
    print("=" * 55)
    print(f"  取得時刻 (JST) : {now_jst}")

    # current_price、previous_close の表示
    if current_price is not None:
        print(f"  現在値         : {current_price:,.2f} ポイント")

        if previous_close is not None and previous_close != 0:
            change = current_price - previous_close
            change_pct = (change / previous_close) * 100
            arrow = "▲" if change > 0 else ("▼" if change < 0 else "→")
            print(f"  前日比         : {arrow} {change:+,.2f} ポイント ({change_pct:+.2f}%)")

        if day_high is not None and day_low is not None:
            print(f"  日中高値       : {day_high:,.2f} ポイント")
            print(f"  日中安値       : {day_low:,.2f} ポイント")
    else:
        print("  現在値を取得できませんでした。市場が休場の可能性があります。")

    print("=" * 55)


if __name__ == "__main__":
    main()
