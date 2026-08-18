import os
import time
import asyncio
import re

# Python 3.14+ no longer auto-creates an event loop; pyrogram 2.0.106
# calls asyncio.get_event_loop() at import time, so set one explicitly.
asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client
from pyrogram.errors import FloodWait

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
TARGET_PHONE = os.getenv("TARGET_PHONE", "")
BURST_COUNT = int(os.getenv("BURST_COUNT", "10"))
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL", "60"))          # 最小觸發間隔（秒）
BUFFER_SECONDS = int(os.getenv("BUFFER_SECONDS", "60"))      # FloodWait 解除後的緩衝（秒）
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL", str(24 * 3600)))  # 單次等待上限（秒）


def extract_wait_seconds(error_str: str) -> int:
    match = re.search(r"(\d+)", error_str)
    return int(match.group(1)) if match else 3600


async def trigger(count: int = 1):
    """連續觸發 count 次。返回 (flood_seconds, success)。"""
    success = 0
    for i in range(count):
        try:
            app = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
            await app.connect()
            try:
                await app.send_code(TARGET_PHONE)
            finally:
                await app.disconnect()
            success += 1
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✓ 触发请求成功 ({i + 1}/{count})"
            )
        except FloodWait as e:
            wait_hours = e.value / 3600
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⏳ 限制中，需等待 {e.value} 秒 ({wait_hours:.1f} 小时)"
            )
            return e.value, success
        except Exception as e:
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✗ 错误: {e} ({i + 1}/{count})"
            )
            return 0, success
    return 0, success


if __name__ == "__main__":
    print(f"=== Telegram 限制保持脚本（动态调度） ===")
    print(
        f"目标: {TARGET_PHONE} | Burst: {BURST_COUNT} | 最小间隔: {MIN_INTERVAL}s | 缓冲: {BUFFER_SECONDS}s | 上限: {MAX_INTERVAL/3600:.1f}h"
    )

    last_flood = 0
    dynamic_interval = MIN_INTERVAL

    while True:
        try:
            flood_seconds, success = asyncio.run(trigger(BURST_COUNT))
            print(f"本輪成功: {success}/{BURST_COUNT}")

            if flood_seconds > 0:
                # 觸發了 FloodWait → 動態等待：限制解除 + 緩衝後立即再觸發，
                # 讓 FloodWait 持續存在並逐步累積（256 → 512 → 900 → 1h → ...）
                last_flood = flood_seconds
                dynamic_interval = MIN_INTERVAL
                sleep_time = min(flood_seconds + BUFFER_SECONDS, MAX_INTERVAL)
                print(
                    f"检测到限制 {flood_seconds}s，动态等待 {sleep_time}s 后再次触发（维持限制累积）..."
                )
            else:
                # 未觸發 FloodWait → 動態縮短間隔，逼近限制閾值
                if last_flood > 0:
                    dynamic_interval = MIN_INTERVAL
                else:
                    dynamic_interval = max(dynamic_interval // 2, MIN_INTERVAL)
                sleep_time = dynamic_interval
                print(f"未触发限制，动态间隔 {sleep_time}s 后再次触发...")

            time.sleep(sleep_time)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"循环异常: {e}")
            time.sleep(60)
