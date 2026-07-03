import datetime

from .i18n import t


def fmt_clock(sec):
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_dur(sec):
    sec = int(sec)
    h, m = sec // 3600, (sec % 3600) // 60
    hu, mu, su = t("u_h"), t("u_m"), t("u_s")
    if h:
        return f"{h}{hu} {m}{mu}" if m else f"{h}{hu}"
    if m:
        return f"{m}{mu}"
    return f"{sec}{su}"


def fmt_est(minutes):
    return fmt_dur(int(minutes) * 60)


def day_of(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def task_label(t_):
    est = t_.get("est")
    if est:
        return t_["name"] + t("task_est_suffix", dur=fmt_est(est))
    return t_["name"]


def parse_task_line(line):
    line = str(line).strip()
    if not line:
        return None, 0
    if "," in line:
        nm, _, rest = line.partition(",")
        digits = "".join(c for c in rest if c.isdigit())
        return nm.strip(), (int(digits) if digits else 0)
    parts = line.rsplit(None, 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0].strip(), int(parts[1])
    return line, 0
