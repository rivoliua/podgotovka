#!/usr/bin/env python3
"""Download openly licensed Biblical-language resources for the "Анатомия души" project.

Only public-domain / Creative Commons sources are fetched. Commercial lexica
(BDAG, TDNT, Louw-Nida, HALOT) are NOT included and must be obtained legally
(see README_open_sources.md).

Usage:  python3 scripts/fetch_open_sources.py [OUT_DIR] [--with-lxx]   (default OUT_DIR: ./open_sources)
        --with-lxx also downloads the Septuagint repo (~700 MB)
Needs:  git (network access to github.com).
"""
import subprocess, sys, shutil
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
WITH_LXX = "--with-lxx" in sys.argv
OUT = Path(ARGS[0] if ARGS else "open_sources").resolve()

# name, repo, sparse paths (None = whole repo), licence note
SOURCES = [
    ("strongs", "openscriptures/strongs", ["greek", "hebrew"],
     "Strong's Greek/Hebrew dictionaries (1890, public domain; JSON CC-BY-SA)"),
    ("bdb-hebrew-lexicon", "openscriptures/HebrewLexicon", None,
     "Brown-Driver-Briggs + index to Strong's/TWOT (BDB public domain)"),
    ("stepbible-lexicons", "STEPBible/STEPBible-Data", ["Lexicons"],
     "TBESG/TBESH brief lexicons and full LSJ (CC BY 4.0, Tyndale House)"),
    ("abbott-smith", "translatable-exegetical-tools/Abbott-Smith", None,
     "Abbott-Smith Manual Greek Lexicon of the NT (1922, public domain)"),
    ("sblgnt-morphgnt", "morphgnt/sblgnt", None,
     "Greek New Testament (SBLGNT) with morphology (CC BY 4.0 / CC BY-SA)"),
    ("wlc-hebrew-ot", "openscriptures/morphhb", ["wlc"],
     "Westminster Leningrad Codex Hebrew OT with morphology (text public domain)"),
    ("lxx-rahlfs", "eliranwong/LXX-Rahlfs-1935", None,
     "Septuagint (Rahlfs 1935) with lexemes - check repository licence"),
    ("synodal-ru", "scrollmapper/bible_databases", ["formats/json/RusSynodal.json"],
     "Russian Synodal Bible (public domain)"),
]

def run(*cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL)

def fetch(name, repo, sparse):
    dest = OUT / name
    if (dest / ".git").exists():
        run("git", "pull", "-q", "--ff-only", cwd=dest)
        return dest
    if dest.exists():
        shutil.rmtree(dest)
    url = f"https://github.com/{repo}.git"
    if sparse:
        run("git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(dest))
        run("git", "sparse-checkout", "set", "--no-cone", *sparse, cwd=dest)
        run("git", "checkout", "-q", cwd=dest)
    else:
        run("git", "clone", "-q", "--depth", "1", url, str(dest))
    return dest

def size_mb(p):
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file() and ".git" not in f.parts) / 1e6

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, failed = [], []
    for name, repo, sparse, note in SOURCES:
        if name == "lxx-rahlfs" and not WITH_LXX:
            print("SKIP  lxx-rahlfs (use --with-lxx, ~700 MB)")
            continue
        try:
            d = fetch(name, repo, sparse)
            rows.append((name, size_mb(d), repo, note))
            print(f"OK    {name:22s} {size_mb(d):7.1f} MB")
        except Exception as e:
            failed.append(name)
            print(f"FAIL  {name}: {e}")
    with open(OUT / "SOURCES.md", "w", encoding="utf-8") as f:
        f.write("# Open sources (auto-generated)\n\n")
        for name, mb, repo, note in rows:
            f.write(f"- **{name}** ({mb:.1f} MB) - https://github.com/{repo} - {note}\n")
    print(f"\nDone: {len(rows)} ok, {len(failed)} failed -> {OUT}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
