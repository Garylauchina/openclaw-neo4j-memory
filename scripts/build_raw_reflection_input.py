#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path

def chunk_text(text: str, chunk_chars: int):
    text = text.strip()
    return [text[i:i+chunk_chars] for i in range(0, len(text), chunk_chars) if text[i:i+chunk_chars].strip()]

STOP = {"Can", "There", "Here", "Remember", "Good", "That", "You", "It", "And", "As", "An", "Will", "Sun", "Session", "Conversation History", "Congratulations", "Don", "Goal", "Setting", "Habit", "Focus", "Chrome"}
WHITELIST_PHRASES = [
    "Task Management Apps", "Productivity Tools", "Goal-Setting and Habit-Tracking Apps",
    "Todoist", "Trello", "Asana", "Wunderlist", "RescueTime", "StayFocusd", "Pomodoro Timer",
    "Pomofocus", "Tomato Timer", "Habitica", "Strides", "Coach.me", "Evernote", "Google Calendar",
    "prioritizing tasks", "breaking them down into smaller chunks", "review and adjust", "Experiment"
]

def extract_graph_hints(text: str):
    seen = []
    for phrase in WHITELIST_PHRASES:
        if phrase in text and phrase not in seen:
            seen.append(phrase)
    candidates = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", text)
    for c in candidates:
        c = c.strip()
        if c in STOP:
            continue
        if len(c) < 3:
            continue
        if c not in seen:
            seen.append(c)
    nodes = seen[:12]
    edges = []
    for i in range(min(len(nodes)-1, 6)):
        edges.append({"source": nodes[i], "target": nodes[i+1], "type": "co_occurs", "weight": 1})
    return {"nodes": nodes, "edges": edges}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('input_path')
    p.add_argument('--chunk-chars', type=int, default=1200)
    p.add_argument('--slice-count', type=int, default=3)
    p.add_argument('--output', default='tmp/raw-reflection-input.json')
    args = p.parse_args()

    text = Path(args.input_path).read_text(encoding='utf-8')
    chunks = chunk_text(text, args.chunk_chars)[:args.slice_count]
    payload = []
    for idx, chunk in enumerate(chunks, start=1):
        hints = extract_graph_hints(chunk)
        payload.append({
            "slice_id": f"slice-{idx}",
            "raw_text": chunk,
            "graph_hints": hints,
        })
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
