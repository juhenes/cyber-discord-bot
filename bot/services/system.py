from datetime import datetime
from pathlib import Path
import shutil
import subprocess


def read_proc_file(path: str) -> str:
    """Read file content from container host mount or fallback to native path."""
    for candidate in (path, path.removeprefix("/host")):
        try:
            return Path(candidate).read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return "Unavailable"


def get_temperature() -> str:
    """Read SoC thermal sensor temperature."""
    raw = read_proc_file("/host/sys/class/thermal/thermal_zone0/temp")
    try:
        value = int(raw) / 1000.0
    except ValueError:
        return "Unavailable"

    if value >= 80:
        status = "Very hot"
    elif value >= 70:
        status = "Warm"
    else:
        status = "Normal"

    return f"{value:.1f}°C - {status}"


def get_memory() -> str:
    """Read memory utilization from meminfo."""
    content = read_proc_file("/host/proc/meminfo")
    if content == "Unavailable":
        return "Unavailable"

    values: dict[str, int] = {}
    for line in content.splitlines():
        name, _, value = line.partition(":")
        if name in {"MemTotal", "MemAvailable"}:
            try:
                values[name] = int(value.strip().split()[0])
            except (ValueError, IndexError):
                pass

    if "MemTotal" not in values or "MemAvailable" not in values:
        return "Unavailable"

    total = values["MemTotal"]
    used = total - values["MemAvailable"]
    used_gb = used / (1024 * 1024)
    total_gb = total / (1024 * 1024)
    percent = (used / total) * 100 if total > 0 else 0
    return f"{used_gb:.1f} GB / {total_gb:.1f} GB ({percent:.0f}%)"


def get_storage() -> str:
    """Read root filesystem disk usage."""
    try:
        total, used, free = shutil.disk_usage("/")
        used_gb = used / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        percent = (used / total) * 100 if total > 0 else 0
        return f"{used_gb:.1f}G / {total_gb:.1f}G ({percent:.0f}%)"
    except OSError:
        return "Unavailable"


def get_uptime() -> str:
    """Read system uptime from proc."""
    content = read_proc_file("/host/proc/uptime")
    try:
        seconds = float(content.split()[0])
    except (ValueError, IndexError):
        return "Unavailable"

    days, remainder = divmod(int(seconds), 86400)
    hours, minutes = divmod(remainder, 3600)
    minutes //= 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return "up " + " ".join(parts)


def get_power() -> str:
    """Check Raspberry Pi power and throttling status via vcgencmd."""
    try:
        output = subprocess.check_output(
            ["vcgencmd", "get_throttled"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        _, _, hex_val = output.partition("=")
        val = int(hex_val, 16)
        if val == 0:
            return "Normal"

        issues = []
        if val & 0x1:
            issues.append("Under-voltage detected")
        if val & 0x2:
            issues.append("Arm frequency capped")
        if val & 0x4:
            issues.append("Currently throttled")
        if val & 0x8:
            issues.append("Soft temp limit active")
        if not issues:
            if val & 0x10000:
                issues.append("Past under-voltage")
            if val & 0x20000:
                issues.append("Past frequency cap")
            if val & 0x40000:
                issues.append("Past throttling")
        return ", ".join(issues) if issues else f"Throttled ({hex(val)})"
    except (OSError, ValueError, subprocess.SubprocessError):
        return "Unavailable"
