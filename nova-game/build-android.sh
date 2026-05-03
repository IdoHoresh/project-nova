#!/usr/bin/env bash
# Helper script to install the built APK on the running emulator.
set -e

APK="${1:-$HOME/Desktop/2048_Unity/build/nova2048.apk}"
DEVICE_ID="${ADB_DEVICE_ID:-emulator-5554}"

if [[ ! -f "$APK" ]]; then
    echo "❌ APK not found at $APK"
    echo "   Build it from Unity first; see nova-game/README.md"
    exit 1
fi

echo "→ Installing $APK on $DEVICE_ID"
adb -s "$DEVICE_ID" install -r "$APK"
echo "→ Launching"
adb -s "$DEVICE_ID" shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
