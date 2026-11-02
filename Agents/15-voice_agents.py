import asyncio
import os

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv, find_dotenv

from voice_core import DEFAULT_INSTRUCTIONS, DEFAULT_MODEL, SAMPLE_RATE, run_turn

load_dotenv(find_dotenv(), override=True)


def record_from_mic() -> np.ndarray:
    print("Recording... press Enter to stop.")
    chunks: list[np.ndarray] = []

    def callback(indata, frames, time, status):
        chunks.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback):
        input()

    return np.concatenate(chunks, axis=0).flatten()


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Add OPENAI_API_KEY=sk-... to the .env file first.")

    input("Press Enter to start recording your question...")
    audio = record_from_mic()

    turn = await run_turn(
        audio,
        SAMPLE_RATE,
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        voice="coral",
        instructions=DEFAULT_INSTRUCTIONS,
        history=[],
    )

    print(f"\nYou said: {turn.transcription}")
    print(f"Agent: {turn.reply}")
    sd.play(turn.audio, samplerate=SAMPLE_RATE)
    sd.wait()


if __name__ == "__main__":
    asyncio.run(main())
