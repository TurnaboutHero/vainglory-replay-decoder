# Replay playback stability: one variable at a time (2026-10-05)

## Question

Earlier Windows runs could not say why a replay crashed, returned home, or played through. The runs
that succeeded and failed differed in executable, replay, launch method, playback speed and attached
memory observer all at once ([acceptance](WINDOWS_REPLAY_ACCEPTANCE_2026-09-10.md),
[failure](WINDOWS_REPLAY_FAILURE_2026-09-08.md)). This experiment fixes everything except one
condition per row.

## Fixed conditions

- Machine and client: KHH-Inspiron, Windows 11 22631, console session 1 (WTS unlock check before every
  input), 3072x1920. Steam client `Vainglory.exe` SHA-256 `659f9eed…`.
- Replay: C16, a 171-section 5v5 recording of 28:23. Before every entry it is injected into a fresh
  practice slot with vgrplay, and all 171 section hashes are verified. The slot is restored from hashed
  backups afterwards.
- Launch: direct process start with `SteamAppId=1025580`, identical for both executables.
- Speed: two `+` clicks right after the replay HUD appears, which gives 5x. 4x is not a step.
- Evidence: game-window screenshot every 5 s, process liveness and exit code, new crashpad dumps.

The protocol was written before the first run. Three amendments are recorded:
- The speed step is 5x, not the planned 4x.
- A stray background `find` ran during E1b–E2b. E1b and E2a share that load, so the executable
  comparison is unaffected.
- The first E4 attempt was void because the harness lost the PID before injection, so the practice
  recording played. It was rerun as E4r.

## Results

| run | executable | observer | seek | outcome | detail |
|---|---|---|---|---|---|
| E1a | original | none | none | **process_exit** | still on the loading screen 15–19 s after the replay click; `0xC0000005` |
| E1b | original | none | none | **process_exit** | still on the loading screen 14–19 s after the click; `0xE06D7363` |
| E2a | LAA copy | none | none | **result_screen** | 28:10 postgame scoreboard |
| E2b | LAA copy | none | none | **result_screen** | identical final scoreboard |
| E3 | LAA copy | 1 Hz VirtualQueryEx | none | **result_screen** | identical final scoreboard |
| E4r | LAA copy | none | timeline click to 14:19 | **result_screen** | identical final scoreboard |

The LAA copy differs from the original executable by one byte: `IMAGE_FILE_LARGE_ADDRESS_AWARE` set in
the PE characteristics (SHA-256 `d6717c15…`).

## Why the original executable fails here

Both new crashpad dumps from the original executable show a 32-bit process at the 2 GB user-space
ceiling (`0x7fff0000`), with about 1.55 GB in use and the largest free region 64–120 KB:

- E1a: access violation reading address 0 at `Vainglory.exe+0x572352`. This is a null dereference
  under address-space exhaustion; the allocation call itself is not identified.
- E1b: C++ exception `std::bad_alloc` thrown from KERNELBASE, with the same throw-info address as the
  2026-10-02 dump.

The LAA run with the observer (E3) shows the same phase from the other side. Use rose from 1.34 GB to
1.53 GB after the replay click, and 13–21 s after the click the process first committed memory above
2 GB. That is the window in which both original-executable runs died. Throughout E3 the largest free
region stayed at 1.9 GB or more, and peak reserved plus committed was 1.6 GB.

## Conclusions for this setup

- The large-address-aware flag alone flipped the outcome: 2/2 process exits became 2/2 result screens.
  Loading C16 needs address space above the 2 GB ceiling that the original executable is limited to.
- The attached memory observer and a mid-game seek did not prevent a result screen (1/1 each).
- The 2026-09-10 home-menu return was not reproduced. Its cause stays open.

## Limits

One replay, one machine, six valid runs. These show which variable flips the outcome here. They are not
a crash rate, and they don't show that all long recordings need LAA. Screenshots and dumps contain player
and session data and stay with the private run records (`D:\VG_EVAL\playback`). The protocol, command
logs and memory series are kept there too.

For replay-driven validation (track 3 and final-screen checks), use the LAA copy and record its hash.
The Steam installation itself was not modified.
