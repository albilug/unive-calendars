import requests

COURSES = {
    "quantum1.ics": (
        "⚛️ Q.Mod. 1",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510134",
    ),
    "quantum2.ics": (
        "⚛️   Mod.22",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510135",
    ),
    "radiation.ics": (
        "☢️Rad-Mat",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510154",
    ),
    "innovation.ics": (
        "🚀 Impr. & Inn.",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510137",
    ),
    "electronics.ics": (
        "🔌 CME",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510152",
    ),
    "lab_electronics.ics": (
        "🔌🧪 Lab CME",
        "https://www.unive.it/data/ajax/Didattica/generaics?cache=-1&afid=510150",
    ),
}

for filename, (title, url) in COURSES.items():
    data = requests.get(url).text.splitlines()

    new_lines = []
    for line in data:
        if line.startswith("SUMMARY:"):
            new_lines.append("SUMMARY:" + title)
        else:
            new_lines.append(line)

    with open(filename, "w") as f:
        for l in new_lines:
            f.write(l + "\n")

print("UNIVE calendars generated.")
