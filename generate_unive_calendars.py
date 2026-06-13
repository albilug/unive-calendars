import sys
import time
from pathlib import Path

import requests

REQUEST_TIMEOUT = (10, 30)
MAX_ATTEMPTS = 4
RETRY_DELAY_SECONDS = 5
USER_AGENT = "unive-calendars/1.0 (+https://github.com/albilug/unive-calendars)"

COURSES = {
    "quantum1.ics": (
        "⚛️MQ Mod1",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510134",
    ),
    "quantum2.ics": (
        "⚛️MQ Mod2",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510135",
    ),
    "radiation.ics": (
        "☢️ Rad Mat",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510154",
    ),
    "innovation.ics": (
        "🚀 Innovation",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510137",
    ),
    "electronics.ics": (
        "🔌 Circuiti",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510152",
    ),
    "lab_electronics.ics": (
        "🧪 Lab Circuiti",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510150",
    ),
}


def fetch_calendar(session, url):
    response = session.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def validate_calendar(text):
    lines = text.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    if not non_empty_lines:
        raise ValueError("empty response")

    first_line = non_empty_lines[0].lstrip("\ufeff")
    if first_line != "BEGIN:VCALENDAR":
        raise ValueError("response is not an ICS calendar")

    if "END:VCALENDAR" not in non_empty_lines:
        raise ValueError("ICS calendar is incomplete")

    return lines


def rename_summary(lines, title):
    return [
        "SUMMARY:" + title if line.startswith("SUMMARY:") else line
        for line in lines
    ]


def write_calendar(filename, lines):
    path = Path(filename)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def is_transient(exc):
    """Connection/timeout errors are transient outages (typically unive.it
    dropping connections from GitHub's cloud IPs). HTTP errors and invalid
    content mean the source actually changed and must be surfaced."""
    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def download_with_retries(session, filename, title, url):
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            text = fetch_calendar(session, url)
            lines = validate_calendar(text)
            write_calendar(filename, rename_summary(lines, title))
            print(f"{filename}: updated")
            return "updated", None
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            print(
                f"{filename}: attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}",
                file=sys.stderr,
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS * attempt)

    if is_transient(last_error) and Path(filename).exists():
        print(
            f"{filename}: keeping existing file after transient connection "
            f"failures: {last_error}",
            file=sys.stderr,
        )
        return "transient", last_error

    # Real problem (bad URL, non-ICS response) or no existing file to fall
    # back on: report it so the workflow fails and we get notified.
    return "content", last_error


def main():
    transient_skipped = []
    failures = []
    with requests.Session() as session:
        for filename, (title, url) in COURSES.items():
            status, error = download_with_retries(session, filename, title, url)
            if status == "transient":
                transient_skipped.append(filename)
            elif status == "content":
                failures.append(f"{filename}: {error}")

    # Genuine problems (broken URL, non-ICS response, no fallback file) fail
    # the job so the breakage is noticed.
    if failures:
        raise SystemExit(
            "Calendar source problem (not a transient outage):\n  "
            + "\n  ".join(failures)
        )

    # Transient unive.it connection drops are tolerated: existing files are
    # kept, the job stays green, and the next run picks up fresh data.
    if transient_skipped:
        print(
            "Kept existing files after transient unive.it connection failures: "
            + ", ".join(transient_skipped)
        )
    else:
        print("UNIVE calendars generated.")


if __name__ == "__main__":
    main()
