# AS-03 — SURFTRAK not transitioned by depth-sensor failsafe

Status: **source-path confirmed, vehicle behavior not yet tested**. No upstream write.

## Independent source-first finding

When the vehicle has a detected depth sensor which becomes unhealthy, `Sub::failsafe_sensors_check()` in `ArduSub/failsafe.cpp` reports `Depth sensor error!` and switches to MANUAL only if:

```cpp
control_mode == Mode::Number::ALT_HOLD ||
control_mode == Mode::Number::SURFACE ||
sub.flightmode->requires_GPS()
```

`ModeSurftrak` derives from `ModeAlthold` but does **not** override its mode requirements. `ModeAlthold` declares `requires_altitude() == true` and `requires_GPS() == false`; `SURFTRAK` is a distinct mode number. Therefore the listed condition is false when SURFTRAK is active, and the failsafe does not request MANUAL.

SURFTRAK continues to run `run_pre()`, `control_range()` and `D_update_controller()` while armed. It is an altitude-dependent control mode, unlike MANUAL.

Relevant source:
- `ArduSub/failsafe.cpp`: `Sub::failsafe_sensors_check()`
- `ArduSub/mode.h`: `ModeSurftrak : public ModeAlthold`
- `ArduSub/mode_surftrak.cpp`: `ModeSurftrak::run()` and `control_range()`
- `ArduSub/sensors.cpp`: `sensor_health.depth = barometer.healthy(depth_sensor_idx)`
- `ArduSub/Sub.cpp`: failsafe check on 50-Hz loop

## Impact hypothesis and next evidence gate

In a normal SURFTRAK mission, depth-pressure sensor failure is detected, yet unlike ALT_HOLD and GPS-dependent modes the flight mode does not transition to MANUAL. The impact on actual thrust/depth control is **unverified**.

SITL Red/Green comparison:
1. Start a submerged armed vehicle with healthy depth sensor in ALT_HOLD; induce `SIM_BARO_DISABLE` and record sensor status, failsafe event, mode transition and motor outputs.
2. Re-run with SURFTRAK and healthy rangefinder before inducing the same failure.
3. Verify mode remains SURFTRAK only on the baseline and whether vertical control operates on invalid/stale depth state.
4. Apply candidate fix only in separate research test branch, and verify both routes transition safely without undesired effects.

No claim of a proven physical safety incident or accepted upstream defect until SITL evidence. Do not file PR or issue without explicit user authorization.
