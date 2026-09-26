"""离线中文语音合成：Kokoro-82M（sherpa-onnx 版，中英混读），带磁盘缓存。"""
import hashlib
import re
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL_REPO = "csukuangfj/kokoro-multi-lang-v1_0"
MODEL_DIR = ROOT / "voices" / "kokoro-multi-lang-v1_0"
CACHE_DIR = ROOT / "build" / "tts"

SPEAKER = 50   # zm_yunxi：普通话男声
SPEED = 0.95   # 稍慢一点，讲解更清楚

_tts = None


def ensure_model():
    if not (MODEL_DIR / "model.onnx").exists():
        from huggingface_hub import snapshot_download

        print(f"下载语音模型 {MODEL_REPO} ...")
        snapshot_download(MODEL_REPO, local_dir=str(MODEL_DIR), ignore_patterns=["lexicon-gb-en.txt"])
    return MODEL_DIR


def _load():
    global _tts
    if _tts is None:
        import sherpa_onnx

        d = ensure_model()
        cfg = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=str(d / "model.onnx"), voices=str(d / "voices.bin"), tokens=str(d / "tokens.txt"),
                    data_dir=str(d / "espeak-ng-data"), dict_dir=str(d / "dict"),
                    lexicon=f"{d / 'lexicon-us-en.txt'},{d / 'lexicon-zh.txt'}"),
                num_threads=2),
            rule_fsts=f"{d / 'phone-zh.fst'},{d / 'date-zh.fst'},{d / 'number-zh.fst'}",
            max_num_sentences=1)
        _tts = sherpa_onnx.OfflineTts(cfg)
    return _tts


def clean_for_speech(text: str) -> str:
    # 引号、书名号等对发音没有帮助，去掉以免产生奇怪的停顿
    text = re.sub(r"[“”‘’「」《》\"]", "", text)
    text = text.replace("——", "，").replace("……", "，")
    return text.strip()


def synth(text: str) -> tuple[Path, float]:
    """合成一句话，返回 (wav 路径, 时长秒)。相同文本只合成一次。"""
    spoken = clean_for_speech(text)
    key = hashlib.sha1(f"{MODEL_REPO}|{SPEAKER}|{SPEED}|{spoken}".encode()).hexdigest()[:16]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{key}.wav"
    if not path.exists():
        audio = _load().generate(spoken, sid=SPEAKER, speed=SPEED)
        pcm = (np.clip(np.asarray(audio.samples), -1, 1) * 32767).astype(np.int16)
        tmp = path.with_suffix(f".{id(pcm)}.tmp")
        with wave.open(str(tmp), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(audio.sample_rate)
            wf.writeframes(pcm.tobytes())
        tmp.rename(path)
    with wave.open(str(path), "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()
    return path, duration
