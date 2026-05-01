#!/usr/bin/env bash
# Pre-flight: pin every emulator state that could break perception.
# Idempotent — safe to run before every agent session.
set -e

DEVICE_ID="${ADB_DEVICE_ID:-emulator-5554}"
ADB="adb -s $DEVICE_ID"

echo "→ Pinning emulator state on $DEVICE_ID"

# 1. ORIENTATION — lock to portrait. Auto-rotation must be OFF or scrcpy/OCR
#    sees a sideways grid the moment the emulator decides to flip.
$ADB shell settings put system accelerometer_rotation 0      # disable auto-rotate
$ADB shell settings put system user_rotation 0               # 0 = portrait

# 2. DISPLAY DENSITY — fix DPI so the OCR's auto-calibrated bbox doesn't drift
#    between sessions. 440 dpi is the Pixel 6 default; pinning it explicitly
#    survives an OS update that changes the default.
$ADB shell wm density 440

# 3. ANIMATION SCALES — set to 1.0 for the visual-stability check to time
#    correctly. Some Android dev presets ship at 0.5x or off, which makes
#    the swipe animation invisible to the pixel-diff loop.
$ADB shell settings put global window_animation_scale 1.0
$ADB shell settings put global transition_animation_scale 1.0
$ADB shell settings put global animator_duration_scale 1.0

# 4. DISPLAY ALWAYS ON (during dev sessions only) so the screen doesn't dim
#    mid-game and corrupt OCR's color sampling.
$ADB shell svc power stayon true

# 5. DISABLE SOFT KEYBOARD popups that occasionally overlay the game.
$ADB shell settings put secure show_ime_with_hard_keyboard 0

# 6. STATUS BAR — verify it's the standard height. If a notification or
#    alarm icon shifts the layout, OCR auto-calibration handles it (it
#    looks for a square contour, not absolute coords) — but log a warning
#    so a human can investigate if the warning fires repeatedly.
HEIGHT=$($ADB shell wm size | awk -F'[ x]' '/Physical/ {print $4}' | tr -d '\r')
if [ "$HEIGHT" != "2400" ]; then
    echo "  ⚠️  Physical display height is $HEIGHT (expected 2400). OCR will recalibrate, but verify this is intentional."
fi

# 7. VERIFY 2048 IS THE FOREGROUND APP (don't run agent against a launcher
#    or a stale dialog).
FOREGROUND=$($ADB shell dumpsys window | grep -E 'mCurrentFocus' | awk '{print $NF}' | tr -d '}')
if [[ ! "$FOREGROUND" == *"nova2048"* ]]; then
    echo "  ⚠️  2048 is not the foreground app (got: $FOREGROUND)."
    echo "     Launching now…"
    $ADB shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
    sleep 2
fi

echo "✓ Emulator state pinned"
