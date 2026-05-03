---
description: Kill any running nova process, reset 2048 game state, and start a fresh nova run against the live emulator. Use when the live demo has gone stale or the agent has crashed.
allowed-tools: Bash
---

Restart the nova live stack against the running Pixel_6 emulator. Use when nova has crashed, hit the step cap, or you need a fresh game for visual verification.

**Pre-conditions (verify, don't assume):**

1. Pixel_6 AVD is booted and `adb devices` shows `emulator-5554 device`
2. The 2048 app (`com.idohoresh.nova2048`) is installed
3. Viewer dev server is running on :3000 (or doesn't matter if you're not watching)

**Sequence:**

1. **Kill any existing nova process:**
   ```bash
   pkill -f "uv run nova" 2>/dev/null
   sleep 1
   ```

2. **Reset 2048 to a fresh game.** `pm clear` doesn't fully reset Unity state (LESSONS.md), so for a TRULY fresh game cold-boot the emulator. For just a "new game" within the same Unity instance, kill + relaunch:
   ```bash
   adb shell am force-stop com.idohoresh.nova2048
   sleep 1
   adb shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
   sleep 4
   ```

3. **Start nova in the background, redirecting logs:**
   ```bash
   cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468/nova-agent
   UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run nova > /tmp/nova-run.log 2>&1 &
   echo "nova pid: $!"
   echo "$!" > /tmp/nova.pid
   ```

4. **Wait for first perception event to confirm nova is running:**
   ```bash
   until grep -q "perception.read" /tmp/nova-run.log 2>/dev/null; do sleep 1; done
   echo "nova is running. tail -f /tmp/nova-run.log to watch."
   ```

**Report back with:**
- nova PID
- Whether the first perception event landed
- Last perception event grid + score (proves the agent is making moves and OCR is reading them)

If nova crashes within ~5 seconds of starting, surface the traceback from `/tmp/nova-run.log` immediately. The most likely failure modes are documented in `LESSONS.md`:
- Pro daily quota exhausted (429) → switch deliberation model in `.env`
- Empty exported `ANTHROPIC_API_KEY` shadowing `.env` → fix env var
- New tile color not in OCR palette → silent misread; agent appears stuck
