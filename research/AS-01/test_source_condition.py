#!/usr/bin/env python3
"""AS-01: compile and execute the condition extracted from ArduSub/failsafe.cpp.

This is an isolated regression reproducer, NOT a full ArduSub SITL flight test.
A successful run means that the expected baseline defect was reproduced.
"""
from pathlib import Path
import re
import subprocess
import tempfile

source = Path("ArduSub/failsafe.cpp").read_text()
match = re.search(
    r"if\s*\(\s*(AP_HAL::millis\(\)\s*<\s*"
    r"failsafe\.last_pilot_input_ms\s*\+\s*"
    r"g\.failsafe_pilot_input_timeout\s*\*\s*1000\.0f)\s*\)",
    source,
)
if not match:
    raise SystemExit("INCONCLUSIVE: baseline source condition changed; review required")

expression = match.group(1)
cpp = r"""
#include <cstdint>
#include <cstdio>
#include <limits>
namespace AP_HAL {
    std::uint32_t current_ms = 0;
    std::uint32_t millis() { return current_ms; }
}
struct { std::uint32_t last_pilot_input_ms; } failsafe;
struct { float failsafe_pilot_input_timeout = 3.0f; } g;
bool baseline_fresh() { return EXPR; }
bool elapsed_fresh() {
    return std::uint32_t(AP_HAL::millis() - failsafe.last_pilot_input_ms) < 3000U;
}
int main() {
    struct Case { const char* name; std::uint32_t last, now; bool expected_fresh, expect_disagreement; };
    const std::uint32_t max = std::numeric_limits<std::uint32_t>::max();
    const Case cases[] = {
        {"normal-before-timeout", 100000U, 101000U, true, false},
        {"normal-after-timeout", 100000U, 105000U, false, false},
        {"wrap-still-fresh", max - 1000U, 1000U, true, false},
        {"wrap-overdue", max - 1000U, 5000U, false, true},
        {"wrap-long-overdue", max - 1000U, 60000U, false, true}
    };
    for (const auto& tc : cases) {
        failsafe.last_pilot_input_ms = tc.last;
        AP_HAL::current_ms = tc.now;
        bool baseline = baseline_fresh();
        bool elapsed = elapsed_fresh();
        bool disagreement = baseline != elapsed;
        std::printf("%s: baseline_fresh=%d elapsed_fresh=%d expected_fresh=%d\\n",
                    tc.name, baseline, elapsed, tc.expected_fresh);
        if (elapsed != tc.expected_fresh || disagreement != tc.expect_disagreement) return 1;
    }
    std::puts("AS-01 REPRODUCED: original source condition misses timeout across millis wrap");
    return 0;
}
""".replace("EXPR", expression)
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "as01.cpp"
    executable = Path(td) / "as01"
    path.write_text(cpp)
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
         str(path), "-o", str(executable)],
        check=True,
    )
    subprocess.run([str(executable)], check=True)
