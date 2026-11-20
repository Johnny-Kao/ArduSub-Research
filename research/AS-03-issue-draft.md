# Sub: SURFTRAK remains active after the depth sensor fails

## Observed behavior

In ArduSub SITL, disabling the depth sensor while the vehicle is armed in SURFTRAK (mode 21) produces `Depth sensor error!`, but the vehicle **remains in SURFTRAK**, which continues using the vertical position controller.

The same depth-sensor failure in ALT_HOLD triggers the expected transition to MANUAL (mode 19).

## Reproduction (SITL, no hardware required)

1. Build the ArduSub SITL vehicle.
2. Dive to -8 m with the motors armed in ALT_HOLD.
3. Enter SURFTRAK (custom mode 21).
4. Set `SIM_BARO_DISABLE=1`, wait for `Depth sensor error!`.
5. Read `HEARTBEAT.custom_mode`: it remains **21**, armed.
6. Repeat from ALT_HOLD without switching to SURFTRAK: the mode correctly changes to **19** (MANUAL).

Recorded independent comparison: [GC #44682590280](https://github.com/Johnny-Kao/ArduSub-Research/actions/runs/44682590280) (ALT_HOLD positive control PASS; SURFTRAK RED).

## Likely cause

`Sub::failsafe_sensors_check()` in `ArduSub/failsafe.cpp` switches to MANUAL only for explicit ALT_HOLD / SURFACE or modes with `requires_GPS() == true`. SURFTRAK is a distinct mode that inherits `ModeAlthold::requires_altitude() == true` but `requires_GPS() == false`, so the condition does not match.

## Candidate change and validation

Adding SURFTRAK to the depth-failsafe mode condition results in MANUAL after the same simulated fault. This **Red/Green** was validated in the research-only branch [`research/as03-depth-failsafe-green`](https://github.com/Johnny-Kao/ArduSub-Research/commit/952c81842480af682f985642d9154484bede1015), with the clean passing SITL [GC #44677919864](https://github.com/Johnny-Kao/ArduSub-Research/actions/runs/44677919864).

Would it make sense to include SURFTRAK in this depth-sensor failsafe condition, or would maintainers prefer using the flight mode's altitude requirement as the predicate?

The test establishes an incorrect safety-mode transition, not a measured runaway or physical damage event. Related [#32099](https://github.com/ArduPilot/ardupilot/pull/32099) concerns **depth exceeding configured limits**, rather than **loss of depth-sensor health**.

Research only — no upstream changes proposed in this draft.
