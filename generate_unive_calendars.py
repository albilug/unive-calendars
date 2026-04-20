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


def download_with_retries(session, filename, title, url):
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            text = fetch_calendar(session, url)
            lines = validate_calendar(text)
            write_calendar(filename, rename_summary(lines, title))
            print(f"{filename}: updated")
            return True
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            print(
                f"{filename}: attempt {attempt}/{MAX_ATTEMPTS} failed: {exc}",
                file=sys.stderr,
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS * attempt)

    if Path(filename).exists():
        print(
            f"{filename}: keeping existing file after repeated download failures",
            file=sys.stderr,
        )
        return False

    raise RuntimeError(f"{filename}: cannot generate file: {last_error}")


def main():
    skipped = []
    with requests.Session() as session:
        for filename, (title, url) in COURSES.items():
            updated = download_with_retries(session, filename, title, url)
            if not updated:
                skipped.append(filename)

    if skipped:
        if len(skipped) == len(COURSES):
            raise SystemExit("All downloads failed; kept existing files.")
        print("UNIVE calendars generated with stale files: " + ", ".join(skipped))
    else:
        print("UNIVE calendars generated.")


if __name__ == "__main__":
    main()
