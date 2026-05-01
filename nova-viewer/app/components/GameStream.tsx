export function GameStream() {
  return (
    <section className="aspect-[9/16] w-full bg-zinc-950 rounded-lg border border-zinc-800 flex items-center justify-center">
      <div className="text-center text-zinc-500 text-sm">
        <p className="mb-2">Live game stream</p>
        <p className="text-xs">
          Run{" "}
          <code className="bg-zinc-800 px-1 rounded">
            scrcpy --serial $ADB_DEVICE_ID
          </code>{" "}
          in a terminal.
        </p>
        <p className="text-xs mt-1">
          For demo: capture both windows with OBS.
        </p>
      </div>
    </section>
  );
}
