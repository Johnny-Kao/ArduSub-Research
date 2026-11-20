# Sub: GUIDED terrain failsafe announces recovery but never runs the AUTO recovery timeout

## Observed behavior

With an armed ArduSub in GUIDED following an ABOVE_TERRAIN waypoint, an out-of-range downward rangefinder triggers the terrain failsafe. ArduSub logs `Failsafe terrain triggered` and `Attempting auto failsafe recovery`, but **after more than the configured 10-second recovery timeout it remains in GUIDED and armed**, without a recovery-timeout action.

An equivalent out-of-range fault during an **AUTO terrain mission** correctly logs `Terrain failsafe recovery timeout!` and disarms using the default terrain-failsafe action.

## Reproduce using ArduSub SITL (no hardware)

A reproducible test is implemented in `Tools/autotest/ardusub.py` in [the research repository](https://github.com/Johnny-Kao/ArduSub-Research). It uses the existing synthetic seafloor Lua rangefinder driver, with a research-only `SCR_USER3=-101` fault-injection switch that reports `RangeFinder::Status::OutOfRangeHigh` instead of incorrectly continuing to report `Good`.

GUIDED case:
1. Enable the synthetic seafloor rangefinder, arm and dive to about -15 m.
2. Enter GUIDED and send a `SET_POSITION_TARGET_GLOBAL_INT` waypoint in `MAV_FRAME_GLOBAL_TERRAIN_ALT`, approximately 30 m away. Verify waypoint acceptance using `NAV_CONTROLLER_OUTPUT`.
3. Inject an out-of-range rangefinder status (`SCR_USER3=-101` in the research fixture).
4. Wait 16 simulated seconds; collect `STATUSTEXT`, mode, and armed state.

**GUIDED RED**, [GC #44682590280](https://github.com/Johnny-Kao/ArduSub-Research/actions/runs/44682590280):
```
Failsafe terrain triggered
Attempting auto failsafe recovery
AS04 state: mode=GUIDED armed=True
AS04 RED: terrain recovery started but GUIDED still armed after 16s without fallback
```

AUTO positive control:
1. Use the same synthetic seafloor and sensor-injection mechanism.
2. Arm and enter AUTO with the existing synthetic terrain waypoint mission.
3. Inject the same out-of-range rangefinder state and wait 16 simulated seconds.

**AUTO GREEN**, [GC #44683779429](https://github.com/Johnny-Kao/ArduSub-Research/actions/runs/44683779429):
```
Failsafe terrain triggered
Attempting auto failsafe recovery
Terrain failsafe recovery timeout!
AS04 AUTO CONTROL: mode=AUTO armed=False
```

## Likely cause

`Sub::failsafe_terrain_check()` permits both `AUTO` and `GUIDED`. `Sub::failsafe_terrain_on_event()` invokes `sub.mode_auto.auto_terrain_recover_start()` regardless of active flight mode.

That function sets `sub.auto_mode = Auto_TerrainRecover`, but `auto_terrain_recover_run()` (including its 10-second timeout and fallback to `failsafe_terrain_act()`) is called exclusively through `ModeAuto::run()`. While the active flight mode is GUIDED, `ModeGuided::run()` runs instead; the AUTO recovery state is not executed.

## Suggested direction / maintainer question

There are at least two possible fixes:

1. **Small safety fix:** when the active mode is GUIDED, do not start an AUTO-only recovery state; call `failsafe_terrain_act()` directly (the configured HOLD/SURFACE/DISARM action).
2. **Preserve recovery behavior:** share or explicitly dispatch the recovery controller and timeout in GUIDED as well as AUTO, with appropriate state management.

Would maintainers prefer immediate configured failsafe action in GUIDED, or a genuine GUIDED terrain-recovery state with its own timeout? We can prepare the minimal fix and regression test in the preferred direction.

These SITL results prove the missed safety-state transition and recovery timeout, not a physical accident or demonstrated uncontrolled motion. Research only; upstream remains unchanged.
