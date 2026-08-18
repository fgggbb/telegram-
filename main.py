import os
import time
import asyncio
import re
from pyrogram import Client
from pyrogram.errors import FloodWait

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
TARGET_PHONE = os.getenv("TARGET_PHONE", "")
INTERVAL_HOURS = int(os.getenv("INTERVAL_HOURS", "20"))
BURST_COUNT = int(os.getenv("BURST_COUNT", "10"))


def extract_wait_seconds(error_str: str) -> int:
    match = re.search(r"(\d+)", error_str)
    return int(match.group(1)) if match else 3600


async def trigger(count: int = 1):
    success = 0
    for i in range(count):
        try:
            async with Client(":memory:", api_id=API_ID, api_hash=API_HASH) as app:
                await app.send_code_request(TARGET_PHONE)
                success += 1
                print(
                    f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✓ 触发请求成功 ({i + 1}/{count})"
                )
        except FloodWait as e:
            wait_hours = e.value / 3600
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⏳ 限制中，需等待 {e.value} 秒 ({wait_hours:.1f} 小时)"
            )
            return e.value + 3600, success
        except Exception as e:
            print(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✗ 错误: {e} ({i + 1}/{count})"
            )
            return INTERVAL_HOURS * 3600, success
    return INTERVAL_HOURS * 3600, success


if __name__ == "__main__":
    print(f"=== Telegram 限制保持脚本 ===")
    print(f"目标: {TARGET_PHONE} | 间隔: {INTERVAL_HOURS}h")

    while True:
        try:
            wait_seconds, success = asyncio.run(trigger(BURST_COUNT))
            print(f"本輪成功: {success}/{BURST_COUNT}")
            sleep_time = (
                wait_seconds
                if wait_seconds > INTERVAL_HOURS * 3600
                else INTERVAL_HOURS * 3600
            )

            if wait_seconds > INTERVAL_HOURS * 3600:
                print(f"检测到限制，等待 {sleep_time/3600:.1f} 小时后重试...")
            else:
                print(f"等待 {INTERVAL_HOURS} 小时后再次触发...")
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"循环异常: {e}")
            time.sleep(3600)
