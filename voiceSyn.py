from Simpler_Kokoro import SimplerKokoro
from gtts import gTTS
from gtts.tts import gTTSError
import edge_tts
import asyncio
import wave
from piper import PiperVoice
import onnxruntime as ort
from faster_whisper import WhisperModel
import os

options_list = ["kokoro", "edge_tts", "gtts", "piper"]

# Ensure Clips directory exists and switch into it
CLIPS_DIR = "Clips"
os.makedirs(CLIPS_DIR, exist_ok=True)
os.chdir(CLIPS_DIR)

# Load Whisper ONCE (reusable)
whisper_model = WhisperModel("base", compute_type="int8")


# -------- Main --------

def main(string, provider):
    print(f"Selected: {provider}")

    if provider not in options_list:
        print("Provider not found. Choose from:", options_list)
        return

    if not string.strip():
        print("Empty input text")
        return

    # Decide file extension
    ext = ".wav" if provider == "piper" else ".mp3"
    output = f"voice{ext}"

    try:
        if provider == "kokoro":
            output = kokoro_main(string, output)
        elif provider == "gtts":
            output = gtts_main(string, output)
        elif provider == "piper":
            output = piper_main(string, output)
        elif provider == "edge_tts":
            output = asyncio.run(edge_tts_main(string, output))
    except Exception as e:
        print(f"{provider} failed: {e}")
        return

    if not output or not os.path.exists(output):
        print("No valid audio file generated")
        return

    # Kokoro already creates subtitles
    if provider == "kokoro":
        print(f"Audio: {output}")
        print(f"Subtitles: {output}.srt")
        return

    # Generate subtitles
    srt_file = os.path.splitext(output)[0] + ".srt"
    audio_to_srt(output, srt_file)

    print(f"Audio: {output}")
    print(f"Subtitles: {srt_file}")


# -------- Providers --------

async def edge_tts_main(string, output):
    communicate = edge_tts.Communicate(string, "en-US-AriaNeural", rate="-25%")
    await communicate.save(output)
    return output


def gtts_main(string, output):
    try:
        tts = gTTS(string, lang="en")
        tts.save(output)
        return output
    except gTTSError as e:
        print(f"gTTS error: {e}")
        return None


def kokoro_main(string, output):
    sk = SimplerKokoro()

    voices = sk.list_voices()
    english_prefixes = ("af_", "am_", "bf_", "bm_", "ef_", "em_")
    english_voices = [v for v in voices if v.name.lower().startswith(english_prefixes)]

    if not english_voices:
        raise Exception("No English voices found")

    voice = english_voices[0]
    print(f"Using voice: {voice.name}")

    sk.generate(
        text=string,
        voice=voice.name,
        output_path=output,
        write_subtitles=True,
        subtitles_path='subtitle.srt',
        subtitles_word_level=True
    )

    return output


def piper_main(string, output):
    session_options = ort.SessionOptions()
    session_options.intra_op_num_threads = 8
    session_options.inter_op_num_threads = 2

    model_path = os.path.abspath("../en_US-lessac-medium.onnx")
    voice = PiperVoice.load(model_path)

    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(voice.config.sample_rate)
        voice.synthesize(string, wav_file)

    return output


# -------- Subtitles --------

def audio_to_srt(input_audio, output_srt):
    segments, _ = whisper_model.transcribe(input_audio, vad_filter=True)

    def format_time(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(
                f"{i}\n"
                f"{format_time(seg.start)} --> {format_time(seg.end)}\n"
                f"{seg.text.strip()}\n\n"
            )

    return output_srt
