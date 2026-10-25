#!/usr/bin/env python3
"""lucid-audit: session feedback against the Lucid coding rules.

Reads Claude Code transcripts (~/.claude/projects/**/*.jsonl), measures each
session and reports which Lucid rules it bent, with one concrete suggestion per
finding. Standard library only. Nothing leaves your machine, and prompt text
is never printed (secret-like strings are counted, not shown).

    python3 lucid_audit.py                      # last 30 days, worst 10 sessions
    python3 lucid_audit.py --days 0 --top 25    # whole history
    python3 lucid_audit.py --project myapp --lang es
    python3 lucid_audit.py --session <id>       # one session, full detail
    python3 lucid_audit.py --json > audit.json
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import statistics
import sys

PROCEED_BARE = re.compile(
    r"^\s*(proceda|procede|proceed|dale|sigue|sigamos|contin[uú]a|continue|go|go on|"
    r"ok|okay|si|sí|yes|hazlo|do it|adelante)\s*[.!,]*\s*$", re.I)
WHATS_LEFT = re.compile(
    r"qu[eé] (queda|falta|m[aá]s falta)|what'?s left|what remains|cerramos|anything else", re.I)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|"
    r"xox[abprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
TEST_CMD = re.compile(
    r"\b(pytest|unittest|npm (run )?test|pnpm (run )?test|yarn test|vitest|jest|playwright|"
    r"cypress|go test|cargo test|mvn test|gradle test|rspec|phpunit|e2e)\b")
COMMIT_CMD = re.compile(r"\bgit\b[^\n|;&]*\bcommit\b")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
AGENT_TOOLS = {"Agent", "Task"}
READ_ONLY_AGENTS = {"Explore", "Plan", "claude-code-guide", "statusline-setup"}

T = {
    "en": {
        "title": "Lucid audit",
        "scope": "{n} sessions · {p} prompts · {d1} → {d2}",
        "overall": "Overall",
        "worst": "Sessions to review (lowest score first)",
        "none": "No sessions found. Check --dir, --days or --project.",
        "R0": "Compacted {n}× (peak context {k}k). Wrap up and open a new session before the first compaction; split the change if it does not fit.",
        "R4": "{n} of {p} prompts were a bare «proceed». Say what to proceed with, or answer a numbered option.",
        "BL": "Asked «what's left?» {n}×. Keep a BACKLOG file and end each session with a wrap-up.",
        "R5": "{e} file edits and no git commit. Every prompt should end in a commit.",
        "R5b": "{r:.0f} prompts per commit. Aim for one change per prompt, one commit per change.",
        "QA": "{e} file edits and no test run. Inspect: run unit/e2e tests or check production before «done».",
        "R1": "{n} prompts over 300 words. Move permanent instructions to the context file or a template.",
        "R6": "{n} subagents, none in an isolated worktree, while files were edited. One branch and worktree per agent.",
        "R9": "Main thread ran on {m} for {pct:.0f}% of responses. Use the most capable model by default.",
        "SEC": "{n} secret-like strings pasted in prompts. Use env vars or a vault, and rotate those keys.",
        "R8": "{b} browser actions and {s} skill invocations across all sessions. Save repeated procedures as skills.",
        "R0g": "{pct:.0f}% of sessions compacted. Shorter sessions, one topic each.",
        "R4g": "{pct:.0f}% of prompts were a bare «proceed».",
        "ok": "Nothing to flag.",
        "metrics": "Metrics",
    },
    "es": {
        "title": "Auditoría Lucid",
        "scope": "{n} sesiones · {p} prompts · {d1} → {d2}",
        "overall": "General",
        "worst": "Sesiones a revisar (menor puntaje primero)",
        "none": "No hay sesiones. Revisa --dir, --days o --project.",
        "R0": "Compactó {n}× (contexto máximo {k}k). Haz Cierre y abre otra sesión antes de la primera compactación; si el cambio no cabe, pártelo.",
        "R4": "{n} de {p} prompts fueron un «proceda» sin objeto. Di con qué, o responde una opción numerada.",
        "BL": "Preguntó «¿qué queda?» {n}×. Lleva un archivo BACKLOG y cierra cada sesión con el evento de Cierre.",
        "R5": "{e} ediciones de archivos y ningún commit. Cada prompt termina en un commit.",
        "R5b": "{r:.0f} prompts por commit. Un cambio por prompt, un commit por cambio.",
        "QA": "{e} ediciones y ninguna prueba ejecutada. Inspecciona: corre unit/e2e o revisa producción antes del «listo».",
        "R1": "{n} prompts de más de 300 palabras. Lo permanente va al archivo de contexto o a una plantilla.",
        "R6": "{n} subagentes, ninguno en worktree aislado, con archivos editados. Una rama y un worktree por agente.",
        "R9": "El hilo principal usó {m} en el {pct:.0f} % de las respuestas. El modelo más capaz por defecto.",
        "SEC": "{n} cadenas con forma de secreto pegadas en prompts. Usa variables de entorno o un vault, y rota esas llaves.",
        "R8": "{b} acciones de navegador y {s} invocaciones de skills en total. Guarda los procedimientos repetidos como skills.",
        "R0g": "El {pct:.0f} % de las sesiones compactó. Sesiones más cortas, un tema cada una.",
        "R4g": "El {pct:.0f} % de los prompts fue un «proceda» sin objeto.",
        "ok": "Nada que señalar.",
        "metrics": "Métricas",
    },
}

# Penalty per finding; a session starts at 100.
WEIGHT = {"R0": 20, "R4": 10, "BL": 10, "R5": 20, "R5b": 10, "QA": 15, "R1": 5, "R6": 10, "R9": 10, "SEC": 25}


def prompt_text(rec):
    """Text the human typed, or None for tool results, meta and system-injected turns."""
    if rec.get("isMeta") or rec.get("isCompactSummary") or rec.get("isSidechain"):
        return None
    content = (rec.get("message") or {}).get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(b.get("type") == "tool_result" for b in content if isinstance(b, dict)):
            return None
        text = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    else:
        return None
    text = text.strip()
    if not text or text.startswith("<") or re.fullmatch(r"(\[Image[^\]]*\]\s*)+", text):
        return None
    return text


def parse_session(path):
    s = {
        "id": os.path.basename(path)[:-6], "project": "", "start": None, "end": None,
        "prompts": 0, "short": 0, "long": 0, "proceed_bare": 0, "whats_left": 0, "secrets": 0,
        "compactions": 0, "peak_ctx": 0, "edits": 0, "commits": 0, "tests": 0,
        "subagents": 0, "subagents_writers": 0, "subagents_isolated": 0, "skills": 0, "browser": 0,
        "models": collections.Counter(), "tools": collections.Counter(),
    }
    seen_msg = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            ts = rec.get("timestamp")
            if ts and not rec.get("isSidechain"):
                s["start"] = s["start"] or ts
                s["end"] = ts
            if rec.get("cwd") and not s["project"]:
                s["project"] = rec["cwd"]
            kind = rec.get("type")
            if kind == "system" and rec.get("subtype") == "compact_boundary":
                s["compactions"] += 1
                pre = (rec.get("compactMetadata") or {}).get("preTokens") or 0
                s["peak_ctx"] = max(s["peak_ctx"], pre)
            elif kind == "user":
                text = prompt_text(rec)
                if text is None:
                    continue
                words = len(text.split())
                s["prompts"] += 1
                s["short"] += words <= 3
                s["long"] += words > 300
                s["proceed_bare"] += bool(PROCEED_BARE.match(text))
                s["whats_left"] += bool(WHATS_LEFT.search(text))
                s["secrets"] += len(SECRET.findall(text))
            elif kind == "assistant" and not rec.get("isSidechain"):
                msg = rec.get("message") or {}
                mid = msg.get("id")
                if mid not in seen_msg:
                    seen_msg.add(mid)
                    if msg.get("model") and not msg["model"].startswith("<"):
                        s["models"][msg["model"]] += 1
                    u = msg.get("usage") or {}
                    ctx = sum(u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
                    s["peak_ctx"] = max(s["peak_ctx"], ctx)
                for b in msg.get("content") or []:
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    name, inp = b.get("name", ""), b.get("input") or {}
                    s["tools"][name] += 1
                    if name in EDIT_TOOLS:
                        s["edits"] += 1
                    elif name == "Bash":
                        cmd = inp.get("command", "")
                        s["commits"] += len(COMMIT_CMD.findall(cmd))
                        s["tests"] += bool(TEST_CMD.search(cmd))
                    elif name in AGENT_TOOLS:
                        s["subagents"] += 1
                        # Read-only agents need no worktree; only writers count against rule 6.
                        if inp.get("subagent_type") not in READ_ONLY_AGENTS:
                            s["subagents_writers"] += 1
                            s["subagents_isolated"] += inp.get("isolation") == "worktree"
                    elif name == "Skill":
                        s["skills"] += 1
                    if "chrome" in name or "browser" in name.lower():
                        s["browser"] += 1
    return s


def findings(s, top_model):
    f = []
    if s["compactions"]:
        f.append(("R0", dict(n=s["compactions"], k=round(s["peak_ctx"] / 1000))))
    if s["prompts"] >= 5 and s["proceed_bare"] / s["prompts"] > 0.3:
        f.append(("R4", dict(n=s["proceed_bare"], p=s["prompts"])))
    if s["whats_left"] >= 2:
        f.append(("BL", dict(n=s["whats_left"])))
    if s["edits"] >= 3 and not s["commits"]:
        f.append(("R5", dict(e=s["edits"])))
    elif s["commits"] and s["prompts"] / s["commits"] > 10:
        f.append(("R5b", dict(r=s["prompts"] / s["commits"])))
    if s["edits"] >= 5 and not s["tests"]:
        f.append(("QA", dict(e=s["edits"])))
    if s["long"] >= 2:
        f.append(("R1", dict(n=s["long"])))
    if s["subagents_writers"] >= 2 and not s["subagents_isolated"] and s["edits"]:
        f.append(("R6", dict(n=s["subagents_writers"])))
    total = sum(s["models"].values())
    if top_model and total >= 10:
        main, cnt = s["models"].most_common(1)[0]
        if main != top_model and cnt / total > 0.5:
            f.append(("R9", dict(m=main, pct=100 * cnt / total)))
    if s["secrets"]:
        f.append(("SEC", dict(n=s["secrets"])))
    return f


def score(fs):
    return max(0, 100 - sum(WEIGHT[k] for k, _ in fs))


def main():
    ap = argparse.ArgumentParser(description="Session feedback against the Lucid coding rules.")
    ap.add_argument("--dir", default=os.path.expanduser("~/.claude/projects"), help="transcripts folder")
    ap.add_argument("--days", type=int, default=30, help="look back N days (0 = everything)")
    ap.add_argument("--project", help="only sessions whose folder contains this text")
    ap.add_argument("--session", help="only this session id (prefix ok)")
    ap.add_argument("--min-prompts", type=int, default=3, help="skip sessions with fewer prompts")
    ap.add_argument("--top", type=int, default=10, help="how many sessions to list")
    ap.add_argument("--lang", choices=("en", "es"), default="en")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()
    t = T[a.lang]

    cutoff = None
    if a.days:
        cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.days)).isoformat()
    sessions = []
    for root, dirs, files in os.walk(a.dir):
        dirs[:] = [d for d in dirs if d != "subagents"]
        if a.project and a.project.lower() not in root.lower():
            continue
        for name in files:
            if not name.endswith(".jsonl") or (a.session and not name.startswith(a.session)):
                continue
            path = os.path.join(root, name)
            if cutoff and dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc).isoformat() < cutoff:
                continue
            s = parse_session(path)
            if s["prompts"] >= (1 if a.session else a.min_prompts):
                sessions.append(s)

    if not sessions:
        print(t["none"], file=sys.stderr)
        return 1

    models = collections.Counter()
    for s in sessions:
        models.update(s["models"])
    top_model = next((m for m, _ in models.most_common() if "opus" in m or "fable" in m), None) or (
        models.most_common(1)[0][0] if models else None)
    for s in sessions:
        s["findings"] = findings(s, top_model)
        s["score"] = score(s["findings"])

    n, prompts = len(sessions), sum(s["prompts"] for s in sessions)
    agg = {
        "sessions": n, "prompts": prompts,
        "score_median": statistics.median(s["score"] for s in sessions),
        "compacted_pct": 100 * sum(1 for s in sessions if s["compactions"]) / n,
        "compactions": sum(s["compactions"] for s in sessions),
        "short_pct": 100 * sum(s["short"] for s in sessions) / prompts,
        "proceed_bare_pct": 100 * sum(s["proceed_bare"] for s in sessions) / prompts,
        "whats_left": sum(s["whats_left"] for s in sessions),
        "commits": sum(s["commits"] for s in sessions),
        "prompts_per_commit": prompts / max(1, sum(s["commits"] for s in sessions)),
        "subagents": sum(s["subagents"] for s in sessions),
        "skills": sum(s["skills"] for s in sessions),
        "browser": sum(s["browser"] for s in sessions),
        "peak_ctx_median": statistics.median(s["peak_ctx"] for s in sessions),
        "models": dict(models.most_common(5)),
        "secrets": sum(s["secrets"] for s in sessions),
    }
    general = []
    if agg["compacted_pct"] > 25:
        general.append(t["R0g"].format(pct=agg["compacted_pct"]))
    if agg["proceed_bare_pct"] > 15:
        general.append(t["R4g"].format(pct=agg["proceed_bare_pct"]))
    if agg["browser"] > 200 and agg["skills"] < agg["browser"] / 100:
        general.append(t["R8"].format(b=agg["browser"], s=agg["skills"]))

    ranked = sorted(sessions, key=lambda s: (s["score"], -s["prompts"]))
    if a.json:
        out = {"summary": agg, "general": general, "sessions": [
            {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in s.items() if k != "tools"}
            | {"findings": [{"rule": k, "text": t[k].format(**v)} for k, v in s["findings"]]}
            for s in ranked]}
        json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
        return 0

    starts = sorted(s["start"] for s in sessions if s["start"])
    print(f"# {t['title']}\n")
    print(t["scope"].format(n=n, p=prompts, d1=starts[0][:10], d2=starts[-1][:10]))
    print(f"\n## {t['metrics']}\n")
    print(f"score p50 {agg['score_median']:.0f}/100 · compacted {agg['compacted_pct']:.0f}% ({agg['compactions']}) · "
          f"≤3 words {agg['short_pct']:.0f}% · bare proceed {agg['proceed_bare_pct']:.0f}% · "
          f"what's left {agg['whats_left']} · prompts/commit {agg['prompts_per_commit']:.1f} · "
          f"subagents {agg['subagents']} · skills {agg['skills']} · browser {agg['browser']} · "
          f"peak ctx p50 {agg['peak_ctx_median'] / 1000:.0f}k")
    print("models: " + ", ".join(f"{m} {c}" for m, c in agg["models"].items()))
    if general:
        print(f"\n## {t['overall']}\n")
        for g in general:
            print(f"- {g}")
    print(f"\n## {t['worst']}\n")
    for s in ranked[:a.top]:
        proj = os.path.basename(s["project"].rstrip("/")) or "?"
        print(f"### {s['score']:>3}/100 · {proj} · {s['id'][:8]} · {(s['start'] or '')[:10]} · "
              f"{s['prompts']} prompts, {s['commits']} commits, {s['compactions']} compactions")
        for k, v in s["findings"] or [("ok", {})]:
            print(f"- {t[k].format(**v)}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
