# nova-game — forked Unity 2048

The actual Unity project lives outside this repo (it's a fork of
[stdbilly/2048_Unity](https://github.com/stdbilly/2048_Unity), MIT).

## Setup

1. Fork https://github.com/stdbilly/2048_Unity to your GitHub account.
2. Clone it next to `project-nova`: `git clone <your-fork> ~/Desktop/2048_Unity`.
3. Open in Unity Hub with Unity 6.0.4 LTS (plan originally specified Unity
   2022 LTS; Unity 6 is the current LTS line and upgrades the 2018-era
   project in-place — verified working).
4. Switch build target to Android (Build Profiles → Android → Switch Platform).
5. Player Settings (Android tab):
   - Override Default Package Name ☑
   - Package Name `com.idohoresh.nova2048`
   - Minimum API Level: Android 7.1 'Nougat' (API 25) — Unity 6 floor;
     plan asked for 24 but Unity 6 dropped that target. Emulator runs
     API 34 so this is fine.
   - Target API Level: Android 14.0 (API 34)
   - Scripting Backend: IL2CPP
   - Target Architectures: ARM64 only
6. Add the game scene to the Scene List in Build Profiles.
7. Build → output to `~/Desktop/2048_Unity/build/nova2048.apk`.

## Install on emulator

Boot an Android emulator (Android Studio → Device Manager → Pixel 6 API 34 → ▶).
Then:

```bash
./build-android.sh
```

The agent's `ADB_DEVICE_ID` env var must match the emulator (usually `emulator-5554`).

## Emulator preconditions

Before running the agent, the emulator state must be pinned. Run:

    ./nova-game/pin-emulator-state.sh

This locks: portrait orientation, 440 dpi, 1.0× animation scales, screen-on,
no soft-keyboard popups, and confirms 2048 is the foreground app. The agent's
OCR auto-calibrator handles minor scale drift, but auto-rotation, animation-off,
and screen-dim cannot be recovered from in-loop — they have to be pre-pinned.

If the agent reports `CalibrationError: no square grid contour found`, the
emulator probably isn't in 2048 (or the screen is dimmed). Re-run the pin script.
