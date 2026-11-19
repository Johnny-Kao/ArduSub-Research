# AS-01 — Pilot-input failsafe across 32-bit millisecond rollover

## Scope and status

- Research-only; no upstream PR, issue or commit.
- Source snapshot: ArduPilot/ardupilot `9d7be65cd63ae0ee722b002ccc606f0e8d97cd74`.
- Reproduction: **confirmed for the condition extracted directly from `ArduSub/failsafe.cpp`**.
- Full SITL, motor output and vehicle-level consequence: **NOT tested**.

## Observation

The production condition in `Sub::failsafe_pilot_input_check()` uses:

```cpp
if (AP_HAL::millis() <
    failsafe.last_pilot_input_ms +
    g.failsafe_pilot_input_timeout * 1000.0f)
```

In the 32-bit rollover case, the original condition can keep treating the last pilot input as recent after the configured 3-second timeout.

A separate source-level reproducer extracts the exact expression from the checked-out production file, compiles it with a minimal AP_HAL clock stub, and compares it against modulo-32-bit elapsed-time logic. It deliberately tests both regular and rollover cases.

## Verified test cases

| Case | Last input (ms) | Now (ms) | Baseline | Elapsed-time reference |
|---|---:|---:|---|---|
| Ordinary, within deadline | 100000 | 101000 | Fresh | Fresh |
| Ordinary, overdue | 100000 | 105000 | Expired | Expired |
| After wrap, within deadline | 4294966295 | 1000 | Fresh | Fresh |
| After wrap, overdue | 4294966295 | 5000 | **Fresh** | Expired |
| After wrap, long overdue | 4294966295 | 60000 | **Fresh** | Expired |

Reproduce using:

```bash
python3 research/AS-01/test_source_condition.py
```

CI: `.github/workflows/as01.yml`.

## Production-impact gating

The source condition is used by the 50-Hz pilot-input failsafe check, and the default `FS_PILOT_INPUT` setting is disarm with a three-second timeout. This alone does not demonstrate physical motor-output consequences.

Before promoting to a Smart PR candidate:

1. Verify whether 32-bit rollover of `AP_HAL::millis()` is surfaced as expected in an ArduSub SITL or representative HAL.
2. Exercise a normal pilot-input connection that stops transmitting `MANUAL_CONTROL` while GCS heartbeat remains active.
3. Check the expected disarm and state transitions, including loss-of-control telemetry and resulting motor outputs.
4. Verify the behavior on a corrected implementation and preserve a red/green comparison.
5. Confirm no underlying type, clock or deployment constraint invalidates the observed path; check existing upstream discussions **only after** completing independent validation.

Do not characterize the issue as a verified vehicle safety incident or CVE on the current evidence.

## Repository provenance

This is a standalone source snapshot (not a GitHub fork) copied from ArduPilot. The snapshot has an independent root commit and deliberately omits the original upstream `.github/workflows/` files, replacing them with isolated research CI. Submodule gitlinks are retained but submodule contents are not vendored. Follow original upstream license and attribution notices.
