# 02 — The Pieces

> What hardware, software, and concepts the project relies on. Plain language. Examples for each.

Project Nova is made of several moving parts. Most have specialized names. This doc explains each part in plain terms, with a real-world analogy, so you understand what you're looking at.

## 1. The Android emulator

**What it is.** A program that runs on your computer (Mac/Windows/Linux) and pretends to be an Android phone. You can install apps on it, tap on its screen with your mouse, and the apps run as if they were on a real phone.

**Why we need it.** Nova plays a real Android-built version of 2048. We don't want to plug in a physical phone every time we run her — we'd burn through batteries, USB cables would fail, and capturing the screen would be annoying. The emulator gives us a phone-shaped target on the same machine as the agent code, so everything is fast and reliable.

**Real-world analogy.** Imagine if your laptop could open up a tiny "phone window" on your desktop, and that phone window was a real Android phone in every way except for the part where it costs money and breaks if you drop it. That's an emulator.

**What we'll use.** Android Studio's built-in emulator (free, official). Configured to run a 2048 .apk built from a forked Unity project.

## 2. ADB (Android Debug Bridge)

**What it is.** A command-line tool that lets your computer talk to an Android device or emulator. You type `adb` commands and the device responds.

**Why we need it.** Nova has to do two things to the emulator:
- **Capture the screen** so she can see what's on it (for the VLM to look at).
- **Send swipes** so she can take actions in the game.

Both of these are done with ADB commands.

Examples:
```
adb exec-out screencap -p > screenshot.png
adb shell input swipe 540 1500 540 500 100
```

The first one takes a screenshot. The second one swipes from the bottom of the screen to the top (i.e., swipe up).

**Real-world analogy.** ADB is like a remote control for the emulator. You don't have to click on the emulator window — your code can control it directly.

## 3. scrcpy

**What it is.** An open-source tool that mirrors an Android device's screen to your computer in real time, like a video stream. It also lets you see the device live.

**Why we need it.** ADB's `screencap` is fine for taking single screenshots, but for the **brain panel** (the live view that the user watches), we want a smooth, continuous video feed of the game — not a flickering screenshot updating every two seconds.

scrcpy gives us that smooth video. Nova's brain panel (right side of the demo) ingests the scrcpy stream and shows the game live, while the agent code uses ADB screenshots only when it needs to make a decision.

**Real-world analogy.** Imagine your phone's screen being mirrored to your TV via Chromecast. scrcpy is the same idea, but via USB/ADB instead of WiFi.

## 4. VLM (Vision-Language Model)

**What it is.** A type of AI model that can take **both images and text** as input and produce text as output. It can "look at" a picture and answer questions about it.

Examples of VLMs you might have heard of:
- Anthropic's Claude (with vision)
- OpenAI's GPT-4V
- Google's Gemini
- Open-source: Qwen-VL, LLaVA

**Why we need it.** Nova has to make decisions based on what's on the screen. A VLM is the simplest way to feed a screenshot of a 2048 board and a prompt like *"You are playing 2048. Which way should you swipe? Explain your reasoning."* and get back a structured answer.

**Real-world analogy.** Imagine showing a chess position to a human player and asking "what would you play here, and why?" The human looks at the picture and gives you both a move and an explanation. A VLM does the same, just faster and at scale.

**What we'll use.** Anthropic's Claude (with vision). Architecture is provider-agnostic so we can swap to GPT-4V or Gemini with a config change if needed.

**Cost.** VLMs charge per call. Roughly $0.005–0.05 per call depending on which model. Nova makes one call per move. A full 2048 game has 200–1000 moves. So one full game costs ~$1–50 depending on which model. Not free, but fine for development.

## 5. Vector database

**What it is.** A type of database that stores **embeddings** — long lists of numbers that represent the "meaning" of something — and lets you efficiently find which stored item is most similar to a query item.

**Why we need it.** Nova has to remember past board positions and retrieve "boards similar to the current one" quickly. We can't store boards as raw text and search them with `LIKE` queries — that would miss boards that are *meaningfully* similar but textually different.

Instead, we turn each board into an embedding (a numeric fingerprint of its meaning) and store those embeddings in a vector database. When Nova sees a new board, she turns it into an embedding and asks the database "which past boards have embeddings nearest to this one?" That's how she finds analogous past situations.

**Real-world analogy.** Imagine a librarian who has read every book and can instantly tell you "the books most similar in tone to this one you just described." A vector database is like that, but for any kind of data, not just books.

**What we'll use.** LanceDB. File-backed (no server needed), local, free, fast Rust core.

## 6. SQLite

**What it is.** A small, file-based database. Standard SQL, but stored as a single `.db` file on disk instead of running as a server.

**Why we need it.** Alongside the vector database, Nova needs a regular structured database for things like: timestamps, scores, importance ratings, action histories, reflection text. SQLite is the simplest possible choice.

**Real-world analogy.** A spreadsheet, but with the ability to ask complex questions of it.

## 7. WebSocket

**What it is.** A way for two programs to talk to each other in **real time** — both sides can send messages whenever they want, instead of just request-response.

**Why we need it.** The Nova agent (Python) and the brain panel viewer (a web page) run as separate processes. When the agent updates Nova's mood, retrieves a memory, or commits to a move, it needs to push that update to the viewer **immediately** so the user sees it live.

WebSockets are the standard way to do this. The agent broadcasts events; the viewer subscribes and renders.

**Real-world analogy.** A walkie-talkie connection between two people, where either can speak whenever — as opposed to a phone call where one person dials and waits for an answer.

## 8. Unity (the game engine)

**What it is.** A popular game-development framework. Lets you build 2D and 3D games and export them to lots of platforms (Windows, Mac, iOS, Android, web).

**Why we need it.** The 2048 game we play is built in Unity. We're forking an open-source Unity 2048 project (`stdbilly/2048_Unity`, MIT licensed) and exporting it to an Android APK so we can install it on the emulator.

**Real-world analogy.** Unity is like a Lego kit for making games. Other people have already built a Lego 2048; we're snapping it onto our shelf and pointing the camera at it.

## 9. Next.js / React (for the brain panel)

**What it is.** A framework for building modern web applications. React is the underlying UI library; Next.js is a popular framework that uses React.

**Why we need it.** The brain panel is a web page. We want it to be smooth, animated, beautiful. React + Next.js are the standard tools for that.

**Real-world analogy.** Think of it as the difference between writing a website by hand in raw HTML vs. using a tool like Figma to design and export it. React/Next.js give us prebuilt building blocks (buttons, animations, layout systems) that we can compose.

## 10. OBS (Open Broadcaster Software)

**What it is.** A free tool for recording and streaming video from your computer. Used by streamers and YouTubers everywhere.

**Why we need it.** When the demo is ready, we record a clip showing Nova playing the game with the brain panel visible. OBS can capture that combined view as a single clean video file, ready to post on LinkedIn.

**Real-world analogy.** A camera pointed at your screen, but with software-only quality — no actual camera needed.

## How they fit together

```
                  ┌────────────────────────────┐
                  │     YOUR COMPUTER (MAC)    │
                  └────────────────────────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ↓                      ↓                      ↓
┌─────────────┐      ┌─────────────────┐   ┌──────────────────┐
│  ANDROID    │      │   NOVA AGENT    │   │  BRAIN PANEL     │
│  EMULATOR   │  ←→  │   (Python)      │   │  (Next.js page)  │
│             │      │                 │   │                  │
│  running    │ ADB  │ - VLM (Claude)  │ ws│ - Live game feed │
│  the 2048   │      │ - vector DB     │ ─→│   (via scrcpy)   │
│  Unity APK  │ scrcpy- SQLite        │   │ - mood gauges    │
│             │  →   │ - affect logic  │   │ - memory feed    │
│             │      │ - reflection    │   │ - reasoning text │
└─────────────┘      └─────────────────┘   └──────────────────┘

                              ↓
                  ┌────────────────────────────┐
                  │  OBS captures the entire   │
                  │  screen as a video file →  │
                  │  posted to LinkedIn        │
                  └────────────────────────────┘
```

## Summary in one paragraph

The Android emulator runs the 2048 game. ADB lets the Nova agent control it (take screenshots, send swipes). scrcpy provides a smooth live video for the brain panel. Nova's brain is Python code that calls a VLM (Claude with vision) for decisions, stores memories in SQLite + a vector database, and runs all the affect/dopamine/trauma logic locally. The brain panel is a Next.js web page that subscribes to Nova's events over a WebSocket and renders her internal state in real time. OBS captures the whole thing as video.

That's all the pieces.
