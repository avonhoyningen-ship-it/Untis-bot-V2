# WebUntis → Telegram Bot – Setup-Anleitung

## Was das macht
Ein GitHub Actions Workflow läuft automatisch alle 20 Minuten (Mo–Fr, 7–19 Uhr) im
Hintergrund, ruft deinen WebUntis-Vertretungsplan ab und schickt dir per Telegram
eine Nachricht, wenn sich etwas geändert hat (Ausfall, Vertretung, Raumänderung etc.).
Kein eigener Server nötig, komplett kostenlos.

---

## Schritt 1: Telegram Bot erstellen
1. In Telegram nach **@BotFather** suchen und `/start` schreiben.
2. `/newbot` senden, Namen vergeben (z.B. `Vertretungsplan Bot`).
3. Du bekommst einen **Token** wie `123456789:ABCdefGhIJKlmNoPQRsTUVwxyz` → merken.
4. Deinen Bot in Telegram öffnen und `/start` schicken (damit er dir schreiben darf).
5. Deine **Chat-ID** herausfinden: öffne im Browser
   `https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates`
   nachdem du dem Bot geschrieben hast. Dort steht `"chat":{"id": 123456789, ...}`
   → das ist deine Chat-ID.

## Schritt 2: WebUntis-Zugangsdaten sammeln
Du brauchst:
- **Schulname** – genau wie er beim WebUntis-Login in der Schulliste steht
- **Server** – z.B. `borys.webuntis.com` (steht in der URL, wenn du dich im
  Browser einloggst: `https://SERVER/WebUntis/...`)
- **Benutzername + Passwort** – dein normaler WebUntis-Login
- **Klasse** (optional) – nur nötig, wenn dein Login mehrere Klassen sieht
  (z.B. als Elternteil/Lehrer). Als Schüler kannst du das Feld leer lassen.

## Schritt 3: GitHub Repository anlegen
1. Auf [github.com](https://github.com) ein neues **privates** Repository erstellen,
   z.B. `untis-bot`.
2. Die Dateien aus diesem Projekt hochladen (`check_untis.py`, der Ordner
   `.github/workflows/check.yml`, diese Anleitung).
   Am einfachsten per Drag & Drop im Browser oder mit `git push`.

## Schritt 4: Secrets hinterlegen
Im Repo: **Settings → Secrets and variables → Actions → New repository secret**
Folgende Secrets anlegen:

| Name | Wert |
|---|---|
| `UNTIS_SCHOOL` | dein Schulname |
| `UNTIS_USERNAME` | dein WebUntis-Login |
| `UNTIS_PASSWORD` | dein WebUntis-Passwort |
| `UNTIS_SERVER` | z.B. `borys.webuntis.com` |
| `UNTIS_CLASS` | deine Klasse, oder leer lassen/weglassen |
| `TELEGRAM_TOKEN` | Bot-Token von BotFather |
| `TELEGRAM_CHAT_ID` | deine Chat-ID |

## Schritt 5: Testen
Im Repo unter **Actions → Vertretungsplan Check → Run workflow** manuell starten.
Wenn alles korrekt ist, bekommst du bei Änderungen eine Telegram-Nachricht
(beim allerersten Lauf meist keine, da noch kein Vergleichsstand existiert).

Danach läuft es automatisch alle 20 Minuten von selbst.

---

## Wichtige Hinweise
- **Privates Repo verwenden**, da deine Zugangsdaten sonst sichtbar wären (auch
  wenn sie als Secrets nicht im Klartext im Code stehen).
- Falls dein Schul-WebUntis eine **2-Faktor-Anmeldung** oder ein Anmeldeportal
  über die Schule selbst nutzt (z.B. Login über Schulverwaltungssoftware statt
  direkt bei WebUntis), funktioniert der direkte Login evtl. nicht – dann bräuchte
  man einen anderen Ansatz (Screen-Scraping des mobilen Vertretungsplans).
- Die Zeiten im Cron (`6-18 UTC`) kannst du in `.github/workflows/check.yml`
  anpassen – aktuell deckt das ca. 7–19 Uhr deutscher Zeit ab.
- Wenn du das Skript stattdessen lieber lokal auf einem eigenen Raspberry Pi /
  Server laufen lassen willst, geht das genauso – dann statt Secrets einfach
  eine `.env`-Datei mit den gleichen Variablennamen nutzen und per `cron` alle
  20 Min aufrufen.
