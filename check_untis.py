#!/usr/bin/env python3
"""
WebUntis -> Telegram Vertretungsplan-Bot

Prüft den WebUntis-Vertretungsplan für heute + morgen und schickt eine
Telegram-Nachricht, wenn sich etwas geändert hat (neue/geänderte/entfallene Stunden).

Konfiguration über Umgebungsvariablen (siehe .env.example bzw. GitHub Secrets):
  UNTIS_SCHOOL     - Schulname wie in WebUntis hinterlegt (z.B. "Meine Schule")
  UNTIS_USERNAME   - dein WebUntis Login
  UNTIS_PASSWORD   - dein WebUntis Passwort
  UNTIS_SERVER     - Server-Adresse, z.B. "borys.webuntis.com" (ohne https://)
  UNTIS_CLASS      - Klassenname, z.B. "10a"  (ODER UNTIS_ELEMENT wenn du direkt
                      als Schüler/Lehrer eingeloggt bist - dann leer lassen)
  TELEGRAM_TOKEN   - Bot-Token von @BotFather
  TELEGRAM_CHAT_ID - deine Chat-ID (siehe Anleitung)
"""

import os
import sys
import json
import hashlib
import datetime
import requests
import webuntis

STATE_FILE = "last_state.json"


def get_env(name, required=True, default=None):
    val = os.environ.get(name, default)
    if required and not val:
        print(f"FEHLER: Umgebungsvariable {name} fehlt.", file=sys.stderr)
        sys.exit(1)
    return val


def fetch_substitutions():
    school = get_env("UNTIS_SCHOOL")
    username = get_env("UNTIS_USERNAME")
    password = get_env("UNTIS_PASSWORD")
    server = get_env("UNTIS_SERVER")
    klass = get_env("UNTIS_CLASS", required=False)

    session = webuntis.Session(
        school=school,
        username=username,
        password=password,
        server=server,
        useragent="UntisTelegramBot/1.0",
    ).login()

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=7)

    if klass:
        klasse_obj = session.klassen().filter(name=klass)[0]
        timetable = session.timetable(klasse=klasse_obj, start=today, end=tomorrow)
    else:
        # my_timetable() ist bei manchen Schulen fehlerhaft (falscher personType).
        # Deshalb explizit als Schüler (type=5) mit der eigenen personId abfragen.
        person_id = session.login_result["personId"]
        try:
            timetable = session.timetable(student=person_id, start=today, end=tomorrow)
        except Exception:
            # Fallback: manche Konten sind kein "student"-Element, sondern brauchen
            # den generischen my_timetable()-Weg.
            timetable = session.my_timetable(start=today, end=tomorrow)

    entries = []
    for period in timetable:
        code = getattr(period, "code", None)  # None, "cancelled", "irregular"
        subjects = ",".join(s.name for s in period.subjects) if period.subjects else "?"
        teachers = ",".join(t.name for t in period.teachers) if period.teachers else "?"
        rooms = ",".join(r.name for r in period.rooms) if period.rooms else "?"

        entries.append({
            "date": str(period.start.date()),
            "start": period.start.strftime("%H:%M"),
            "end": period.end.strftime("%H:%M"),
            "subject": subjects,
            "teacher": teachers,
            "room": rooms,
            "code": code or "regular",
            "info": getattr(period, "substText", "") or "",
        })

    session.logout()
    entries.sort(key=lambda e: (e["date"], e["start"]))
    return entries


def load_last_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_last_state(entries):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def entry_key(e):
    return f'{e["date"]}|{e["start"]}|{e["subject"]}'


def diff_entries(old, new):
    old_map = {entry_key(e): e for e in old}
    new_map = {entry_key(e): e for e in new}

    added, changed, removed = [], [], []

    for key, e in new_map.items():
        if key not in old_map:
            if e["code"] != "regular":
                added.append(e)
        else:
            if old_map[key] != e:
                changed.append(e)

    for key, e in old_map.items():
        if key not in new_map and e["code"] != "regular":
            removed.append(e)

    return added, changed, removed


def format_entry(e):
    label = {"cancelled": "❌ Entfällt", "irregular": "🔄 Vertretung"}.get(e["code"], "ℹ️ Änderung")
    line = f"{label}: {e['date']} {e['start']}-{e['end']} {e['subject']} ({e['teacher']}, {e['room']})"
    if e["info"]:
        line += f"\n   📝 {e['info']}"
    return line


def send_telegram(text):
    token = get_env("TELEGRAM_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram-Nachrichtenlimit ist 4096 Zeichen - notfalls kürzen
    for chunk_start in range(0, len(text), 4000):
        chunk = text[chunk_start:chunk_start + 4000]
        resp = requests.post(url, data={"chat_id": chat_id, "text": chunk})
        if resp.status_code != 200:
            print(f"Telegram-Fehler: {resp.text}", file=sys.stderr)


def main():
    try:
        new_entries = fetch_substitutions()
    except Exception as e:
        print(f"FEHLER beim Abruf von WebUntis: {e}", file=sys.stderr)
        sys.exit(1)

    old_entries = load_last_state()
    added, changed, removed = diff_entries(old_entries, new_entries)

    if added or changed or removed:
        parts = ["📢 *Vertretungsplan-Update*\n"]
        for e in added:
            parts.append(format_entry(e))
        for e in changed:
            parts.append(format_entry(e))
        for e in removed:
            parts.append(f"✅ Wieder normal: {e['date']} {e['start']}-{e['end']} {e['subject']}")
        message = "\n".join(parts)
        print(message)
        send_telegram(message)
    else:
        print("Keine Änderungen.")

    save_last_state(new_entries)


if __name__ == "__main__":
    main()
