"""Decide what to do at the current time — smart cadence logic.

Called every 10 minutes by the GitHub Actions workflow.
Returns a list of jobs to execute this tick.

Schedule (all times in Asia/Bangkok / ICT):
  - Quiet hours 04:30 - 06:30 → nothing
  - Hourly compact brief at HH:00 (most hours)
  - 10-min interval briefs at market open/close windows:
      Thai open  09:55, 10:05, 10:15
      Thai close 16:25, 16:35
      US open    21:25, 21:35, 21:45
      US close   03:55, 04:05, 04:15
  - Full brief 4 times daily: 07:00, 13:00, 21:00, 04:30
  - Alert + command poll every tick (every 10 min)
  - Weekly recap Friday 18:00
"""
from datetime import datetime
from zoneinfo import ZoneInfo

ICT = ZoneInfo("Asia/Bangkok")


def now_ict() -> datetime:
    return datetime.now(ICT)


def is_quiet(t: datetime) -> bool:
    """Quiet hours: 04:30 - 06:30 ICT (no scheduled briefs)."""
    hm = t.hour * 60 + t.minute
    return 270 <= hm < 390  # 04:30 = 270, 06:30 = 390


def pick_jobs(t: datetime | None = None) -> list[str]:
    """Return list of jobs to run at time t.

    Possible jobs:
      'full_brief'    — long Market Brief (4x/day)
      'hourly_brief'  — short compact brief
      'tenmin_brief'  — pre/post market 10-min interval brief
      'alert_check'   — always (runner/price/thb/vix)
      'command_poll'  — always (Telegram command listener)
      'weekly_recap'  — Friday 18:00
    """
    t = t or now_ict()
    jobs = ["alert_check", "command_poll"]  # always

    if is_quiet(t):
        return jobs  # only alerts + command during quiet

    hm = (t.hour, t.minute)
    weekday = t.weekday()  # 0=Mon, 4=Fri, 6=Sun

    # Full brief: 4 fixed times
    if hm in {(7, 0), (13, 0), (21, 0)} or hm == (4, 30):
        jobs.append("full_brief")
        return jobs

    # 10-min interval briefs (market open/close)
    tenmin_times = {
        (9, 55), (10, 5), (10, 15),     # Thai open
        (16, 25), (16, 35),              # Thai close
        (21, 25), (21, 35), (21, 45),    # US open
        (3, 55), (4, 5), (4, 15),        # US close
    }
    if hm in tenmin_times:
        jobs.append("tenmin_brief")
        return jobs

    # Hourly compact brief at HH:00 (unless full brief already covered above)
    if t.minute == 0:
        jobs.append("hourly_brief")

    # Weekly recap: Friday 18:00
    if weekday == 4 and hm == (18, 0):
        jobs.append("weekly_recap")

    return jobs


if __name__ == "__main__":
    # Useful for debugging schedule decisions
    t = now_ict()
    print(f"Now (ICT): {t.strftime('%a %H:%M')}")
    print(f"Quiet: {is_quiet(t)}")
    print(f"Jobs:  {pick_jobs(t)}")
