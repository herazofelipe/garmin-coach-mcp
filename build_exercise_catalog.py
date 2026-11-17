#!/usr/bin/env python3
"""Generate garmin_exercise_catalog.json from Garmin's official `garmin-fit-sdk` package.

The catalog (exercise categories and names that Garmin Connect accepts in strength
workouts) is derived from the FIT SDK profile, whose license does not allow
redistributing SDK material. So this repo does not ship the JSON: the Docker build
runs this script, which installs Garmin's package under its own license and writes
the file inside your image only.

Usage:  pip install "garmin-fit-sdk>=21,<22" && python build_exercise_catalog.py
"""
import json
import sys
from pathlib import Path

try:
    from garmin_fit_sdk.profile import Profile
except ImportError:
    sys.exit("garmin-fit-sdk is not installed: pip install 'garmin-fit-sdk>=21,<22'")

types = Profile["types"]
catalog = {
    cat.upper(): sorted(n.upper() for n in types.get(f"{cat}_exercise_name", {}).values())
    for cat in types["exercise_category"].values()
}
out = Path(__file__).with_name("garmin_exercise_catalog.json")
out.write_text(json.dumps(catalog, indent=0, sort_keys=True))
print(f"{out.name}: {len(catalog)} categories, {sum(map(len, catalog.values()))} exercises")
