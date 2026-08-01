#!/usr/bin/env python3
"""One-command setup for a fresh clone of this repository.

A `git clone` alone does NOT give you a working library. Two artefacts are
deliberately not committed and must be built locally:

  * `vector_index/chunks.jsonl`   (~126 MB) — the retrieval corpus
  * `vector_index/lexical.sqlite` (~166 MB) — the FTS5 index search reads

Without them `scripts/search_knowledge.py` answers `Coverage: NONE` for every
query *and still exits 0*, which looks like an empty library rather than a
missing index. `.claude/commands/` is likewise not committed (it is a
byte-for-byte copy of the tracked `commands/`), so Claude Code offers zero
slash commands on a fresh clone.

This script fixes both, then proves it worked:

    python3 scripts/bootstrap.py

Measured at 9 s on a fresh clone, cold (Apple silicon macOS 26.5, Python 3.14.4;
Python 3.12 measured the same). A re-run is 7-8 s because the lexical index
short-circuits on an unchanged chunk hash. See `docs/installing.md`.

What it deliberately does NOT do
--------------------------------
* No package installation. If a dependency is missing it tells you the command
  and exits 2; it never installs anything on your behalf.
* No writes to git — no staging, no commits, no branch or index mutation.
* No network access.
* No writes to any tracked file. It builds in-process via
  `pipelines.sync_engine.build_state` and writes ONLY the two gitignored
  retrieval artefacts above (plus `vector_index/embeddings.jsonl` under
  `--with-embeddings`). It never calls `pipelines.sync_engine.write_state`,
  which is what makes `scripts/build_index.py` leave 1,029 modified tracked
  files on a clean clone (it nulls `vector_embedding` across all registry
  records whenever the embedding backend is unavailable).
  Net effect: `git status` is still clean when this finishes.

Exit codes: 0 success, 1 verification failed, 2 refused to start (bad Python,
missing dependency, or --with-embeddings against a config that disables them).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIN_PYTHON = (3, 10)
HEARTBEAT_SECONDS = 3.0
PHASE_COUNT = 6

# The verification query. Chosen because the corpus has one unambiguous best
# answer for it and the README uses the same query as its demo.
SMOKE_QUERY = "trigger recursion"
SMOKE_EXPECT_SKILL = "apex/recursive-trigger-prevention"

CHUNKS_PATH = ROOT / "vector_index" / "chunks.jsonl"
LEXICAL_PATH = ROOT / "vector_index" / "lexical.sqlite"
EMBEDDINGS_PATH = ROOT / "vector_index" / "embeddings.jsonl"

_T0 = time.monotonic()
_PRINT_LOCK = threading.Lock()
_QUIET = False


# --------------------------------------------------------------------------
# progress reporting
# --------------------------------------------------------------------------

def _elapsed() -> float:
    return time.monotonic() - _T0


def step(message: str, *, force: bool = False) -> None:
    """Emit one timestamped progress line.

    Every line carries monotonic elapsed seconds so a long phase is never
    mistakable for a hang.
    """
    if _QUIET and not force:
        return
    with _PRINT_LOCK:
        print(f"[{_elapsed():6.1f}s] {message}", flush=True)


def detail(message: str, *, force: bool = False) -> None:
    step(" " * 10 + message, force=force)


def fail(message: str) -> None:
    with _PRINT_LOCK:
        print(f"\nBOOTSTRAP FAILED: {message}", file=sys.stderr, flush=True)


def _size_note(paths: "list[Path]") -> str:
    parts = []
    for path in paths:
        try:
            parts.append(f"{path.name} {path.stat().st_size / 1e6:.0f} MB")
        except OSError:
            parts.append(f"{path.name} not yet written")
    return "  [" + ", ".join(parts) + "]" if parts else ""


class Heartbeat:
    """Daemon thread that keeps a blocking phase visibly alive.

    `build_state` and the sqlite build are single opaque calls that can run for
    tens of seconds. Without this the process is silent and indistinguishable
    from a hang — the original complaint that motivated this script.
    """

    def __init__(self, label: str, watch: "list[Path]") -> None:
        self.label = label
        self.watch = watch
        self._stop = threading.Event()
        self._thread = None

    def __enter__(self) -> "Heartbeat":
        if not _QUIET:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def _run(self) -> None:
        while True:
            if self._stop.wait(HEARTBEAT_SECONDS):
                return
            detail(f"... {self.label}{_size_note(self.watch)}")

    def __exit__(self, *exc_info: object) -> bool:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        return False


# --------------------------------------------------------------------------
# phase 1 — preflight
# --------------------------------------------------------------------------

def preflight() -> int:
    step(f"phase 1/{PHASE_COUNT}  preflight")

    if sys.version_info < MIN_PYTHON:
        detail(
            f"FAIL  Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required; "
            f"this interpreter is {sys.version.split()[0]}",
            force=True,
        )
        fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required.")
        return 2

    detail(f"repo root       {ROOT}")
    detail(f"interpreter     {sys.executable}")
    detail(f"python          {sys.version.split()[0]}")

    missing = []
    for module in ("yaml", "jsonschema"):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    try:
        __import__("fastembed")
        detail("fastembed       installed (semantic embeddings available)")
    except ImportError:
        detail("fastembed       not installed (lexical-only retrieval — this is the default)")

    if missing:
        detail(f"FAIL  missing required package(s): {', '.join(missing)}", force=True)
        fail("required dependencies are not installed. Run this, then re-run bootstrap:")
        # The one remediation string a new user needs. Printed, never executed —
        # this script installs nothing.
        print("\n  python3 -m pip install -r requirements.txt\n", file=sys.stderr, flush=True)
        return 2

    detail("OK  required dependencies present (PyYAML, jsonschema)")
    return 0


# --------------------------------------------------------------------------
# phases 2-4 — build + write the gitignored retrieval artefacts
# --------------------------------------------------------------------------

def _config_embeddings_enabled() -> "bool | None":
    """Read `embeddings.enabled` from config/retrieval-config.yaml.

    Read-only; nothing is ever written back. This matters because
    `--with-embeddings` reaches the encoder only via
    `build_state(skip_embeddings=False)` -> `build_embeddings`, and
    `build_embeddings` returns `[]` when `config.enabled` is False
    (pipelines/embedding_backends.py:103-104). The flag can therefore suppress
    the encode but never enable it. Without this check, `--with-embeddings`
    against a disabled config runs the whole scan, writes zero vectors, and
    reports success.

    Returns None when the file is absent or unparseable — in that case we let
    the build proceed rather than block on a config we could not read.
    """
    config_path = ROOT / "config" / "retrieval-config.yaml"
    try:
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 — a config read must never break bootstrap
        return None
    section = data.get("embeddings")
    if not isinstance(section, dict):
        return None
    return bool(section.get("enabled", False))


def build_retrieval_artefacts(with_embeddings: bool) -> "tuple[int, object]":
    # Deliberately NOT named build_index: this shares no code path with
    # scripts/build_index.py and must never be mistaken for a wrapper round it.
    from pipelines.sync_engine import build_chunks_jsonl, build_state

    if with_embeddings:
        if _config_embeddings_enabled() is False:
            # Hard stop, not a warning: continuing would scan everything, encode
            # nothing, and exit 0 — the silent no-op this script exists to avoid.
            detail(
                "FAIL  --with-embeddings requested but config/retrieval-config.yaml "
                "has embeddings.enabled: false",
                force=True,
            )
            fail(
                "embeddings are disabled repository-wide, so --with-embeddings would "
                "encode nothing.\nSet embeddings.enabled: true in "
                "config/retrieval-config.yaml, or drop the flag."
            )
            return 2, None
        step(
            f"phase 2/{PHASE_COUNT}  scanning skill packages -> chunks + EMBEDDINGS "
            "(HOURS — the encode dominates; see docs/installing.md section 4)",
            force=True,
        )
        # Measured 2026-08-01 on this corpus: 9.4 chunks/sec over a 521-chunk
        # strided sample (BAAI/bge-small-en-v1.5, Apple silicon, load avg 3.5/8,
        # model load and cold start excluded) => ~3h50m for all 130,151 chunks.
        # Consistent with the repo's own notes: ~2:20 in
        # config/retrieval-config.yaml, ~2-3h in requirements.txt.
        detail("measured ~9.4 chunks/sec => roughly 3-4 HOURS for ~130k chunks on this")
        detail("machine. Adds ~535 MB. Benefit: 0.0pp on the 400-query curated fixtures,")
        detail("+1.3pp Hit@1 / +4.6pp Hit@3 on the held-out realistic set.")
        detail("Omit the flag for the ~5-35 s lexical-only build. Ctrl-C now if unintended.")
    else:
        # ETA is deliberately a conservative bracket: measured 6 s on Apple
        # silicon / Python 3.14, but this walks ~1,027 packages off disk and a
        # slow or cold filesystem dominates. Over-quoting beats a surprise.
        step(f"phase 2/{PHASE_COUNT}  scanning skill packages -> retrieval chunks (~5-35 s)")

    with Heartbeat("still scanning skills/ and knowledge/", [CHUNKS_PATH, LEXICAL_PATH]):
        state = build_state(ROOT, skip_embeddings=not with_embeddings)
    detail(f"{len(state.chunks)} chunks built from {state.manifest['skill_count']} skill packages")

    # -- phase 3: integrity ------------------------------------------------
    step(f"phase 3/{PHASE_COUNT}  verifying chunk hash against the committed manifest")
    built_hash = state.manifest["chunks_hash"]
    committed_hash = None
    manifest_path = ROOT / "vector_index" / "manifest.json"
    if manifest_path.exists():
        try:
            committed_hash = json.loads(manifest_path.read_text(encoding="utf-8")).get("chunks_hash")
        except (ValueError, OSError):
            committed_hash = None

    if committed_hash is None:
        detail(f"WARNING  no committed chunks_hash to compare against; built={built_hash[:12]}...")
    elif committed_hash == built_hash:
        detail(f"OK  chunks_hash={built_hash[:12]}... matches the committed manifest")
    else:
        # Expected whenever the working tree has local skill edits. Never fatal:
        # the index we are about to write describes THIS tree, which is correct.
        detail(
            f"WARNING  chunk drift — committed={committed_hash[:12]}... "
            f"built={built_hash[:12]}..."
        )
        detail("         expected if you have local skill edits; the index will match your tree.")

    # -- phase 4: write ----------------------------------------------------
    targets = "chunks.jsonl + lexical.sqlite"
    if with_embeddings:
        targets += " + embeddings.jsonl"
    step(f"phase 4/{PHASE_COUNT}  writing vector_index/ ({targets}) — all gitignored")

    (ROOT / "vector_index").mkdir(parents=True, exist_ok=True)
    with Heartbeat("still writing the index", [CHUNKS_PATH, LEXICAL_PATH]):
        payload = build_chunks_jsonl(state.chunks)
        CHUNKS_PATH.write_text(payload, encoding="utf-8")
        del payload

        from pipelines.lexical_index import build_lexical_index

        build_lexical_index(LEXICAL_PATH, state.chunks, built_hash)

        if with_embeddings:
            from pipelines.embedding_backends import write_embeddings

            # delete_if_empty=False: if the encode produced nothing (backend
            # unavailable) an existing file on disk is still valid — never
            # destroy it as a side effect of bootstrap.
            write_embeddings(EMBEDDINGS_PATH, state.embeddings, delete_if_empty=False)

    detail(f"chunks.jsonl   {CHUNKS_PATH.stat().st_size / 1e6:.0f} MB")
    detail(f"lexical.sqlite {LEXICAL_PATH.stat().st_size / 1e6:.0f} MB")
    if with_embeddings:
        if state.embeddings:
            detail(f"embeddings.jsonl {EMBEDDINGS_PATH.stat().st_size / 1e6:.0f} MB "
                   f"({len(state.embeddings)} vectors)")
        else:
            # The config-disabled case is caught before phase 2, so the realistic
            # remaining cause is a missing/failed backend. Name the fix, don't guess.
            detail("WARNING  --with-embeddings was requested but the encoder produced no "
                   "vectors; retrieval stays lexical-only. Check the phase-1 fastembed "
                   "line above; install with: python3 -m pip install 'fastembed>=0.4,<1.0'")

    return 0, state


# --------------------------------------------------------------------------
# phase 5 — slash commands
# --------------------------------------------------------------------------

def install_commands() -> int:
    step(f"phase 5/{PHASE_COUNT}  installing slash commands -> .claude/commands/")
    installer = ROOT / "scripts" / "install_local_commands.py"
    if not installer.exists():
        detail(f"WARNING  {installer.relative_to(ROOT)} not found; skipping")
        return 0

    completed = subprocess.run(
        [sys.executable, str(installer)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    for line in (completed.stdout + completed.stderr).splitlines():
        if line.strip():
            detail(line.strip())
    if completed.returncode != 0:
        detail(f"WARNING  installer exited {completed.returncode}")
    return completed.returncode


# --------------------------------------------------------------------------
# phase 6 — verification (the gate)
# --------------------------------------------------------------------------

def verify(check_commands: bool) -> int:
    step(f"phase 6/{PHASE_COUNT}  verifying retrieval")

    for required in (LEXICAL_PATH, CHUNKS_PATH):
        if not required.exists():
            detail(f"FAIL  vector_index/{required.name} is missing", force=True)
            fail("index not built — run: python3 scripts/bootstrap.py")
            return 1

    from scripts.search_knowledge import build_search_context, run_search

    try:
        context = build_search_context(ROOT)
        result = run_search(SMOKE_QUERY, context)
    except Exception as exc:  # noqa: BLE001 — any read failure means "rebuild"
        # Most commonly sqlite3.DatabaseError from a truncated or corrupted
        # lexical.sqlite (an interrupted build). A raw traceback here reads as
        # a bug in the library; it is almost always a half-written index.
        detail(f"FAIL  could not query the index: {type(exc).__name__}: {exc}", force=True)
        fail(
            "the retrieval index is unreadable — most likely a corrupted or "
            "half-written build.\nDelete it and rebuild:\n"
            "  rm -f vector_index/lexical.sqlite vector_index/chunks.jsonl\n"
            "  python3 scripts/bootstrap.py"
        )
        return 1

    if not result.get("has_coverage"):
        detail(f"FAIL  query {SMOKE_QUERY!r} returned Coverage: NONE", force=True)
        fail(
            "the retrieval index answered 'no coverage' for a query the corpus "
            "definitely covers.\nRebuild it with: python3 scripts/bootstrap.py"
        )
        return 1

    skills = result.get("skills") or []
    if not skills:
        detail(f"FAIL  query {SMOKE_QUERY!r} returned has_coverage but no skills", force=True)
        fail("retrieval returned an empty skill list. Rebuild: python3 scripts/bootstrap.py")
        return 1

    top_id = skills[0].get("id")
    if top_id != SMOKE_EXPECT_SKILL:
        detail(f"FAIL  expected top skill {SMOKE_EXPECT_SKILL}, got {top_id}", force=True)
        fail(
            f"retrieval works but routed {SMOKE_QUERY!r} to {top_id!r} instead of "
            f"{SMOKE_EXPECT_SKILL!r}.\nThe index built cleanly, so this is a ranking "
            "regression, not a setup problem — see config/retrieval-config.yaml."
        )
        return 1

    # Assert the skill ID only. The score is a tuning output (measured 2.350
    # lexical-only vs 2.505 with embeddings) and moves whenever the ranker is
    # retuned; asserting it would make this gate spuriously red.
    detail(f"OK  {SMOKE_QUERY!r} -> {top_id}", force=True)

    if check_commands:
        source = sorted((ROOT / "commands").glob("*.md"))
        installed = sorted((ROOT / ".claude" / "commands").glob("*.md"))
        if len(installed) != len(source):
            detail(
                f"FAIL  {len(installed)} slash commands installed, {len(source)} in commands/",
                force=True,
            )
            fail(
                "slash commands are out of sync. Run: "
                "python3 scripts/install_local_commands.py"
            )
            return 1
        detail(f"OK  {len(installed)} slash commands installed in .claude/commands/", force=True)

    return 0


# --------------------------------------------------------------------------

def next_steps(check_commands: bool) -> None:
    command_count = len(list((ROOT / ".claude" / "commands").glob("*.md")))
    print(f"\nBootstrap complete in {_elapsed():.0f}s.\n", flush=True)
    print("Next steps:", flush=True)
    print('  1. Search the library:  python3 scripts/search_knowledge.py "<your question>"', flush=True)
    if check_commands and command_count:
        print(f"  2. Restart Claude Code so the {command_count} slash commands in "
              ".claude/commands/ register", flush=True)
    else:
        print("  2. Install slash commands: python3 scripts/install_local_commands.py", flush=True)
    print("  3. Wire up the MCP server:  mcp/sfskills-mcp/docs/CONNECT.md", flush=True)
    print("  4. Full setup reference:    docs/installing.md", flush=True)


def parse_args(argv: "list[str] | None" = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="Build the local retrieval index and install slash commands.",
    )
    parser.add_argument(
        "--with-embeddings",
        action="store_true",
        help="also encode semantic embeddings (+535 MB, HOURS of encode time, "
             "0.0pp benefit on the curated fixtures; requires embeddings.enabled: true "
             "in config/retrieval-config.yaml)",
    )
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="do not install commands/*.md into .claude/commands/",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="run the verification phase only; build nothing",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress progress lines; print failures and the final result only",
    )
    return parser.parse_args(argv)


def main(argv: "list[str] | None" = None) -> int:
    global _QUIET
    args = parse_args(argv)
    _QUIET = args.quiet

    code = preflight()
    if code:
        return code

    if args.verify_only:
        step("phases 2-5 skipped (--verify-only)")
        return verify(check_commands=not args.skip_commands)

    code, _state = build_retrieval_artefacts(with_embeddings=args.with_embeddings)
    if code:
        return code

    if args.skip_commands:
        step(f"phase 5/{PHASE_COUNT}  slash-command install skipped (--skip-commands)")
    else:
        install_commands()

    code = verify(check_commands=not args.skip_commands)
    if code:
        return code

    next_steps(check_commands=not args.skip_commands)
    return 0


if __name__ == "__main__":
    sys.exit(main())
