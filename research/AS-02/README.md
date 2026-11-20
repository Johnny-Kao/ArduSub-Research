# AS-02 — SURFACE arming/spool behavior

**Status: NOT REPRODUCED / PARK.** No upstream issue or PR.

## Hypothesis

`ArduSub/mode_surface.cpp` sets `GROUND_IDLE` when disarmed, but unlike most modes does not explicitly call `set_desired_spool_state(THROTTLE_UNLIMITED)` while armed. The proposed failure was that arming while already in SURFACE mode might leave the motors unable to generate upward thrust.

## Full vehicle integration test

Source snapshot originally imported independently from ArduPilot; research test added in `Tools/autotest/ardusub.py` as `AS02SurfaceArmSpool`.

GitHub Actions: [Successful SITL run #44657535703](https://github.com/Johnny-Kao/ArduSub-Research/actions/runs/44657535703). Test logs and SITL binary archived with that run.

1. Boot SITL, arm and dive to ~12 m in ALT_HOLD; switch to SURFACE while armed. Observed ascent to approximately -8.913 m. **PASS.**
2. Reboot SITL, arm and dive to ~12 m, disarm underwater; switch to SURFACE while disarmed and arm again. Observed ascent to approximately -8.999 m. **PASS.**

Both tests completed without modifying production C++ source. This refutes the original assertion that the missing per-mode spool-state call by itself prevents normal ascent in these tested configurations.

## Limits

The result confirms vehicle-level ascent in the exercised SITL paths; it does not independently prove all individual thruster spool-state transitions or all hardware configurations. It is **not** grounds for claiming a safety bug.

## Action

Park AS-02. No production fix, upstream PR, issue, comment, or upstream write. Further work only if a new independently demonstrated scenario reveals real impact.
