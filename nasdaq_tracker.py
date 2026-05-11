#!/usr/bin/env python3
"""
Nasdaq 100 实时指数追踪器 (含走势曲线)
使用 yfinance 获取 Nasdaq 100 (^NDX) 的盘中数据，并绘制实时走势曲线。
"""

import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from matplotlib import style

# ---------- 配置 ----------
TICKER_SYMBOL = "^NDX"
REFRESH_INTERVAL_MS = 15000          # 数据刷新间隔（毫秒）
ROLLING_WINDOW_MINUTES = 390         # 展示的时间窗口（分钟），390 = 6.5h 完整交易时段
JST = ZoneInfo("Asia/Tokyo")
EST = ZoneInfo("US/Eastern")

# 颜色方案
COLOR_UP = "#00C853"
COLOR_DOWN = "#FF1744"
COLOR_BG = "#1a1a2e"
COLOR_GRID = "#2a2a4a"
COLOR_TEXT = "#e0e0e0"
COLOR_LINE = "#00BCD4"


def fetch_ticker():
    """初始化并返回 Ticker 对象"""
    try:
        return yf.Ticker(TICKER_SYMBOL)
    except Exception as e:
        print(f"Failed to init ticker: {e}")
        sys.exit(1)


def fetch_intraday(ticker):
    """获取今日盘中数据（2分钟K线）"""
    try:
        return ticker.history(period="1d", interval="2m")
    except Exception:
        return None


def fetch_quote(ticker):
    """获取当前报价快照"""
    try:
        f = ticker.fast_info
        return {
            "price": f.get("lastPrice"),
            "prev_close": f.get("regularMarketPreviousClose"),
            "high": f.get("dayHigh"),
            "low": f.get("dayLow"),
        }
    except Exception:
        return None


def format_change(price, prev_close):
    """计算涨跌额和涨跌幅"""
    if price is None or prev_close is None or prev_close == 0:
        return None, None
    chg = price - prev_close
    chg_pct = (chg / prev_close) * 100
    return chg, chg_pct


def market_status():
    """返回当前市场状态标签"""
    now_est = datetime.now(EST)
    weekday = now_est.weekday()  # 0=Mon ... 6=Sun
    hm = now_est.hour * 60 + now_est.minute

    if weekday >= 5:
        return "周末休市"
    if hm < 4 * 60:
        return "盘前 (pre-market)"
    if hm < 9 * 60 + 30:
        return "盘前 (pre-market)"
    if hm < 16 * 60:
        return "盘中 (market open)"
    if hm < 20 * 60:
        return "盘后 (after-hours)"
    return "已收盘"


def setup_plot():
    """初始化 matplotlib 图表"""
    style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.tick_params(colors=COLOR_TEXT, labelsize=9)
    ax.yaxis.set_tick_params(labelright=True)
    ax.tick_params(axis="y", labelright=True, labelleft=True)
    ax.grid(True, color=COLOR_GRID, linestyle="--", linewidth=0.5, alpha=0.7)

    fig.tight_layout(pad=3)
    return fig, ax


def update(frame, ticker, ax, fig):
    """动画更新回调：拉取最新数据并刷新图表"""
    df = fetch_intraday(ticker)
    quote = fetch_quote(ticker)

    ax.clear()
    ax.set_facecolor(COLOR_BG)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.tick_params(colors=COLOR_TEXT, labelsize=9)
    ax.yaxis.set_tick_params(labelright=True)
    ax.tick_params(axis="y", labelright=True, labelleft=True)
    ax.grid(True, color=COLOR_GRID, linestyle="--", linewidth=0.5, alpha=0.7)

    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    status = market_status()

    if quote is None or quote["price"] is None:
        ax.text(0.5, 0.5, "无法获取数据，请检查网络", transform=ax.transAxes,
                ha="center", va="center", fontsize=16, color=COLOR_TEXT)
        ax.set_title(f"Nasdaq 100 (^NDX)  |  JST {now_jst}  |  {status}",
                     color=COLOR_TEXT, fontsize=13, fontweight="bold")
        return

    price = quote["price"]
    prev_close = quote["prev_close"]
    day_high = quote["high"]
    day_low = quote["low"]
    chg, chg_pct = format_change(price, prev_close)

    # 确定涨跌颜色
    if chg is not None:
        accent = COLOR_UP if chg > 0 else COLOR_DOWN if chg < 0 else COLOR_TEXT
    else:
        accent = COLOR_TEXT

    # 绘制走势曲线
    if df is not None and not df.empty and "Close" in df.columns:
        closes = df["Close"].dropna()
        if len(closes) >= 2:
            times = closes.index.to_pydatetime()
            values = closes.values
            ax.plot(times, values, color=COLOR_LINE, linewidth=1.8, zorder=3)
            ax.fill_between(times, values, values.min(), alpha=0.15, color=COLOR_LINE)

            # 标记当前价
            ax.scatter(times[-1], values[-1], color=accent, s=80, zorder=5, edgecolors="white", linewidths=1)
            ax.annotate(
                f" {values[-1]:,.0f}",
                (times[-1], values[-1]),
                textcoords="offset points", xytext=(8, 0),
                fontsize=10, color=accent, fontweight="bold", va="center",
            )

    # 组装标题
    status_text = f"Nasdaq 100 (^NDX)  |  JST {now_jst}  |  {status}"
    ax.set_title(status_text, color=COLOR_TEXT, fontsize=13, fontweight="bold")

    # 左上角信息面板
    info_lines = [f"实时价格: {price:,.2f}"]
    if chg is not None:
        arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "→")
        info_lines.append(f"涨跌: {arrow} {chg:+,.2f}  ({chg_pct:+.2f}%)")
    if day_high is not None:
        info_lines.append(f"今日最高: {day_high:,.2f}")
    if day_low is not None:
        info_lines.append(f"今日最低: {day_low:,.2f}")
    info_lines.append(f"前日收盘: {prev_close:,.2f}" if prev_close else "前日收盘: N/A")

    info_text = "\n".join(info_lines)
    ax.text(0.02, 0.97, info_text, transform=ax.transAxes,
            fontsize=10, color=COLOR_TEXT, va="top", ha="left",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="black", alpha=0.55, edgecolor=COLOR_GRID))

    # 右下角刷新时间
    ax.text(0.98, 0.02, f"刷新: {now_jst}", transform=ax.transAxes,
            fontsize=8, color="#666", va="bottom", ha="right")


def main():
    print("正在启动 Nasdaq 100 实时走势图...")
    print(f"刷新间隔: {REFRESH_INTERVAL_MS // 1000}s")
    print("关闭图表窗口即可退出。")

    ticker = fetch_ticker()
    fig, ax = setup_plot()

    ani = animation.FuncAnimation(
        fig,
        lambda frame: update(frame, ticker, ax, fig),
        interval=REFRESH_INTERVAL_MS,
        cache_frame_data=False,
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
