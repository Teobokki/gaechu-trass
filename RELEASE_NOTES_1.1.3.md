# EPISODIA 1.1.3 — real Romanian voice

Fixes Romanian narration sounding English-accented.

- **음성 언어 (TTS language) selector** in the maker bar: Auto / 한국어 / 日本語 / English / Română — Emil (M) / Română — Alina (F). Default Auto. Force Romanian regardless of diacritics.
- **Smarter auto-detect**: plain-ASCII Romanian (e.g. "Buna ziua, acesta este un test in limba romana.") is now recognised via common Romanian words, not just diacritics.
- **Real Romanian voices online**: edge-tts ro-RO-EmilNeural (male) and ro-RO-AlinaNeural (female).
- **True offline Romanian**: bundled Piper ro_RO (mihai-medium, CC0) narrates with a real Romanian accent when there is no internet — no more English SAPI fallback for Romanian.
- Windows SAPI now refuses to read Romanian with a non-Romanian voice.

Ships Setup + a single portable exe (no zip).
