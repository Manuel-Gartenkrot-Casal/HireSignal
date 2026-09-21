import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hire_signal.db import col_jobs

n = 0
for d in col_jobs.find({"source": None}):
    src = (d.get("sources") or [d.get("ats") or "unknown"])[0]
    col_jobs.update_one({"_id": d["_id"]}, {"$set": {"source": src}})
    n += 1
print("reparados:", n)

from collections import Counter

f = Counter(d["source"] for d in col_jobs.find({}, {"source": 1}))
print("por fuente:", dict(f))
print("con 2+ fuentes:", col_jobs.count_documents({"sources.1": {"$exists": True}}))