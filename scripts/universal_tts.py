import asyncio
import json
import os
import re
import ssl

import websockets
from utils.config import CONFIG


# --- 1. 自动配置提取器 ---
def get_jy_local_config():
    """自动从本地剪映目录探测 device_id 和 iid"""
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        return "1053764930506284", "2314914062247833"

    jy_user_data = os.path.join(local_app_data, r"JianyingPro\User Data")
    config = {"device_id": "1053764930506284", "iid": "2314914062247833"}

    ttnet_path = os.path.join(jy_user_data, r"TTNet\tt_net_config.config")
    if os.path.exists(ttnet_path):
        try:
            with open(ttnet_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                match = re.search(r"device_id&#\*(\d+)", content)
                if match:
                    config["device_id"] = match.group(1)
        except Exception:
            pass

    log_dir = os.path.join(jy_user_data, "Log")
    if os.path.exists(log_dir):
        logs = sorted(
            [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".log")],
            key=os.path.getmtime,
            reverse=True,
        )
        for log_path in logs[:5]:
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    chunk = f.read(1000000)
                    match_iid = re.search(r"iid=(\d+)", chunk)
                    if match_iid:
                        config["iid"] = match_iid.group(1)
                        break
            except Exception:
                continue
    return config["device_id"], config["iid"]


# --- 2. 剪映 (SAMI) WebSocket ---
APP_KEY = "IZjhUeAYwP"
APP_ID = "3704"


def _build_ssl_context() -> ssl.SSLContext:
    """
    默认启用证书校验。仅在显式设置 JY_TTS_INSECURE_SSL=1 时降级，
    用于排查本地证书环境问题。
    """
    if CONFIG.tts_insecure_ssl:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        print("[!] WARNING: TLS verification disabled by JY_TTS_INSECURE_SSL=1", flush=True)
        return ctx
    return ssl.create_default_context()


async def _run_sami_tts(text, speaker, output_file, dev_id, iid):
    ws_url = f"wss://sami.bytedance.com/internal/api/v2/ws?device_id={dev_id}&iid={iid}"
    headers = {
        "User-Agent": f"JianyingPro/5.9.0.11632 (Windows 10.0.19045; app_id:3704; device_id:{dev_id})"
    }
    ssl_context = _build_ssl_context()

    try:
        async with websockets.connect(
            ws_url, additional_headers=headers, ssl=ssl_context, open_timeout=20
        ) as ws:
            task_id = f"ai_gen_{os.urandom(4).hex()}"
            start_msg = {
                "app_id": APP_ID,
                "appkey": APP_KEY,
                "event": "StartTask",
                "namespace": "TTS",
                "task_id": task_id,
                "message_id": task_id + "_0",
                "payload": json.dumps(
                    {
                        "text": text,
                        "speaker": speaker,
                        "audio_config": {
                            "format": "ogg_opus",
                            "sample_rate": 24000,
                            "bit_rate": 64000,
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            }
            await ws.send(json.dumps(start_msg, ensure_ascii=False, separators=(",", ":")))
            await ws.send(
                json.dumps({"appkey": APP_KEY, "event": "FinishTask", "namespace": "TTS"})
            )

            audio_data = bytearray()
            while True:
                try:
                    resp_raw = await asyncio.wait_for(ws.recv(), timeout=15)
                except asyncio.TimeoutError:
                    return False, "SAMI Timeout"

                if isinstance(resp_raw, str):
                    resp = json.loads(resp_raw)
                    event = resp.get("event")
                    if event == "TaskFailed":
                        return (
                            False,
                            f"SAMI Error: {resp.get('status_text')} (Code: {resp.get('status_code')})",
                        )
                    if event == "TaskFinished":
                        break
                else:
                    audio_data.extend(resp_raw)

            if audio_data:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                return True, output_file
            return False, "No audio"
    except Exception as e:
        return False, str(e)


# --- 3. 微软 (Edge-TTS) Fallback ---
async def _run_edge_tts(text, output_file, voice="zh-CN-YunxiNeural"):
    try:
        import edge_tts

        actual_path = output_file
        if output_file.endswith(".ogg") and not output_file.endswith(".mp3"):
            actual_path = output_file + ".mp3"

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(actual_path)
        return True, actual_path
    except Exception as e:
        return False, f"Edge-TTS Error: {str(e)}"


# --- 4. 统一调用接口 ---
async def generate_voice(text: str, output_path: str, speaker: str = "zh_male_huoli"):
    """
    智能 TTS 生成器 (Skill 内置版)
    优先使用剪映音色，失败则回退微软 Edge-TTS。
    """
    dev_id, iid = get_jy_local_config()
    print(f"[*] Intelligent TTS Trace: speaker={speaker}, dev={dev_id}, iid={iid}", flush=True)

    # 尝试剪映
    ok, res = await _run_sami_tts(text, speaker, output_path, dev_id, iid)
    if ok:
        print(f"[+] SAMI Success: {res}", flush=True)
        return res
    else:
        print(f"[!] SAMI Failed: {res}. Using Edge-TTS as fallback...", flush=True)

    # 回退微软
    voice = "zh-CN-YunxiNeural" if "male" in speaker else "zh-CN-XiaoxiaoNeural"
    ok_edge, res_edge = await _run_edge_tts(text, output_path, voice)
    if ok_edge:
        print(f"[+] Edge-TTS Success: {res_edge}", flush=True)
        return res_edge

    return None


if __name__ == "__main__":
    asyncio.run(generate_voice("测试智能配音系统集成成功。", "test.ogg"))
