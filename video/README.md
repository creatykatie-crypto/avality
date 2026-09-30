# Avality — "Time, found." (30 s brand film)

**Deliverable:** `avality.mp4`, 1920×1080 at 60 fps, H.264 + AAC stereo, 30.0 s.

## Brief (assumed; no brief or assets were supplied)
- **Subject:** Avality, read as *availability*: it finds the meeting time that works for everyone.
- **One idea:** Avality finds the gap in everyone's calendar.
- **One feeling:** relief.
- **Audience:** people who lose time to scheduling back-and-forth.

## Visual system
| Role | Value | Why |
|---|---|---|
| Paper | `#F5F5F7` | A quiet, neutral surround |
| Ink | `#1D1D1F` (plus tints for the three people) | Busy time stays grey and low-contrast |
| Free | `#1FAF6E` | The only colour in the film, so it only ever means "free" |
| Type | Inter 400–650, one family | Neutral and very legible at display sizes |

## Score
96 BPM ("effortless flow"): 1 beat is 0.625 s, 1 bar is 2.5 s, and each scene lasts two bars. Every cue in `scene.html` is set with `b(n)`, which converts a beat number to seconds, so the picture and the music share one clock.
Harmony: Am9 → Fmaj9 (the problem) · Dm9 → G9sus (the search) · Cmaj9 (the answer).

## Shot list
| Time | Beat | Picture | Sound |
|---|---|---|---|
| 0.0–4.4 | 0–7 | A message thread piles up on the off-white paper: "Does Tuesday work?" / "I'm out Tuesday." / … / "Let me check…". Bubbles land on beats and push the stack up. | Soft Am9 pad; a quiet rising blip on each bubble |
| 4.4–5.6 | 7–9 | **Transition from the action:** each bubble morphs (position, size, radius, colour) into a busy block on a Mon–Fri week while the grid lines draw in. | Airy whoosh |
| 5.6–9.4 | 9–15 | The rest of the week fills in, in three grey lanes (three people). Caption: "Three calendars. One meeting." | Arpeggio starts |
| 10.0–11.6 | 16–18.5 | A thin green scan line sweeps left to right. Busy blocks dim behind it. | Drums enter; a soft sweep |
| 11.9–15.0 | 19–24 | The one shared gap (Thu 2:30–3:15) springs open in green. Caption: "Avality finds the gap." **Hold.** | Two-note bell at the reveal |
| 15.0–16.4 | 24–26 | The rest of the week fades out. The green slot grows into a white meeting card. | — |
| 16.4–19.4 | 26–31 | Card: "Design review · Thursday, 2:30 PM · 45 min · Everyone's free." The three avatars each get a green tick. A pointer taps **Confirm**, which turns green: **Booked**. | Three rising ticks, one click |
| 19.4–24.9 | 31–40 | The card lifts away. "Everyone's **free.**" arrives one word per beat, then "Finally." **Long hold.** | Drums drop out; the pad thins so the line can land |
| 25.0–29.1 | 40–46.6 | Logo mark: three grey lanes rise, then a green bar crosses them (the gap). The mark slides left as "Avality" enters, then "Time, found." appears. | Cmaj9 resolve; C-major bell |
| 29.1–30.0 | 46.6–48 | Fade to paper. | Tail fades out |

## Rebuild
```bash
npm install                       # playwright-core (uses the preinstalled Chromium)
pip install numpy scipy imageio-ffmpeg
cd video
python3 audio.py                  # → out/score.wav
node render.mjs video 60          # → out/picture.mp4
node render.mjs stills 5 12 18    # optional storyboard frames
FF=$(python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())")
$FF -i out/picture.mp4 -i out/score.wav -c:v copy -c:a aac -b:a 256k -movflags +faststart avality.mp4
```
To rebrand the film, edit the copy in `scene.html` (`CHAT`, the captions, the card), the three colours at the top, or `CHORDS` in `audio.py`.
