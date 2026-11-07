"""Regenerate seed.py's EVENTS / ANNOUNCEMENTS from docs/starter-data.json.

The hosted site imports docs/starter-data.json; the optional Flask app seeds
itself from seed.py. Keeping two copies by hand meant they drifted, so seed.py
is now generated from the single JSON source of truth.

    python tools/sync_seed.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(ROOT, "docs", "starter-data.json")
SEED = os.path.join(ROOT, "seed.py")


def pystr(s):
    return json.dumps(str(s), ensure_ascii=False)


def as_date(v):
    """'YYYY-MM-DD' -> date(y, m, d), or None."""
    if not v:
        return "None"
    return f"date({v[0:4]}, {int(v[5:7])}, {int(v[8:10])})"


def build_block(data):
    ev = []
    for e in data["events"]:
        ev.append(f"""    dict(
        title={pystr(e['title'])},
        category={pystr(e['category'])},
        short_description={pystr(e['shortDescription'])},
        description={pystr(e['description'])},
        organizer={pystr(e['organizer'])},
        venue={pystr(e['venue'])},
        event_date={as_date(e['eventDate'])},
        end_date={as_date(e.get('endDate'))},
        start_time={pystr(e.get('startTime', ''))},
        end_time={pystr(e.get('endTime', ''))},
        registration_deadline={as_date(e.get('registrationDeadline'))},
        capacity={int(e.get('capacity') or 0)},
        fee={int(e.get('fee') or 0)},
        team_size={pystr(e.get('teamSize', 'Individual'))},
        contact_email={pystr(e.get('contactEmail', ''))},
        accent={pystr(e.get('accent', 'teal'))},
        is_featured={bool(e.get('isFeatured'))},
        is_published={bool(e.get('isPublished', True))},
    ),""")

    ann = []
    for a in data["announcements"]:
        ann.append(f"""    dict(
        title={pystr(a['title'])},
        body={pystr(a['body'])},
        category={pystr(a['category'])},
        is_pinned={bool(a.get('isPinned'))},
        is_published={bool(a.get('isPublished', True))},
    ),""")

    return """# --------------------------------------------------------------------------- #
#  Events - the campus's real, documented events and programmes.
#  GENERATED from docs/starter-data.json by tools/sync_seed.py so the Flask app
#  and the hosted site never drift apart. Edit the JSON, then re-run the tool.
# --------------------------------------------------------------------------- #
EVENTS = [
""" + "\n".join(ev) + """
]

# --------------------------------------------------------------------------- #
#  Announcements - starter notices based on documented campus activity.
# --------------------------------------------------------------------------- #
ANNOUNCEMENTS = [
""" + "\n".join(ann) + """
]

"""


def main():
    data = json.load(open(JSON, encoding="utf-8"))
    src = open(SEED, encoding="utf-8").read()

    start_marker = "# --------------------------------------------------------------------------- #\n#  Events"
    start = src.index(start_marker)
    end = src.index("def seed(")
    out = src[:start] + build_block(data) + src[end:]

    compile(out, SEED, "exec")          # fail loudly rather than write broken code
    open(SEED, "w", encoding="utf-8").write(out)
    print(f"seed.py regenerated: {len(data['events'])} events, "
          f"{len(data['announcements'])} announcements")


if __name__ == "__main__":
    main()
