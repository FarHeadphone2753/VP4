# Auftrag: Verschlüsselungs Programm 4.0

Diese Datei wird von Claude Code automatisch als Projekt-Kontext gelesen,
sobald du in diesem Ordner `claude` startest. Du musst Claude Code also nicht
den ganzen Hintergrund erklären – lies diese Datei einfach zuerst.

## Wer das hier ist

Leon (16, Schüler) möchte ein eigenständiges Windows-Desktop-Programm bauen
und als Datei an Freunde verschicken, die es dann auf ihrem eigenen PC
benutzen. Ein anderer Claude-Agent (Cowork, Cloud-Sandbox) hat auf Basis von
Leons Anforderungen bereits eine vollständige, getestete erste Version
entworfen und implementiert. Diese Datei ist der Übergabe-Auftrag an dich
(Claude Code, lokal auf Leons Windows-PC "rasenschach") für die nächsten
Schritte: verifizieren, auf echtem Windows testen, zu einer .exe bauen und
iterativ verbessern.

## Ursprünglicher Auftrag von Leon (wörtlich sinngemäß)

Er möchte ein Programm mit folgenden Funktionen:

1. Verschiedene Verschlüsselungen ver- und entschlüsseln können, inkl.
   eigener Keys, die man speichern kann.
2. Verknüpfung mit Obsidian, um dort seine Keys zu speichern und zu
   verwalten.
3. Es soll **kein Claude / keine KI zur Laufzeit brauchen** – rein lokal.
4. Ver- **und** Entschlüsseln muss beides funktionieren.
5. Nebenfunktion: ein Chat, bei dem jede Installation beim ersten Start
   automatisch eine ID bekommt. Über diese ID kann man Freunde hinzufügen,
   mit ihnen chatten und Bilder/Videos schicken – alles direkt übers WLAN
   (lokales Netzwerk), ohne Server/Internet.

Die Wahl der Programmiersprache/Technik wurde bewusst Claude überlassen.

## Bereits umgesetzt (Version 1, siehe `VP4.py` in diesem Ordner)

Falls `VP4.py` bereits in diesem Ordner liegt: das ist die aktuelle Version,
nicht neu schreiben, sondern darauf aufbauen. Falls die Datei fehlen sollte,
frag Leon danach bzw. bitte ihn, sie erneut aus dem Cowork-Chat hierher zu
kopieren, bevor du weitermachst – nicht einfach von Grund auf neu
implementieren, die bestehende Version wurde bereits sorgfältig getestet.

**Technik:** Ein einzelnes Python-3-Skript, Tkinter-GUI (Standardbibliothek,
kein extra GUI-Framework nötig), einzige externe Abhängigkeit ist das Paket
`cryptography` (Industriestandard für AES/RSA, keine selbstgebastelte
Kryptografie).

**Funktionsumfang:**
- **Ver-/Entschlüsseln:** Caesar, Vigenère, XOR, Base64 sowie AES-256-GCM
  und RSA-2048.
- **Schlüsselverwaltung:** lokaler, mit Master-Passwort verschlüsselter
  Schlüsselspeicher (PBKDF2 + Fernet), Datei `vp4_daten/schluessel.enc`.
- **Obsidian-Sync:** Vault-Ordner ist frei wählbar (funktioniert also auch
  bei Freunden mit eigenem Vault); Export/Import der Schlüssel als
  Markdown-Tabelle in einer Notiz `VP4 Schluessel.md`, bestehender
  Notizinhalt bleibt beim Re-Export erhalten.
- **LAN-Chat:** persistente, beim ersten Start erzeugte ID pro Installation
  (`vp4_daten/konfig.json`); Discovery per UDP-Broadcast (Port 51230);
  Chat/Dateiübertragung per TCP (Port 51231); Freundesliste in
  `vp4_daten/freunde.json`; eingehende Verbindungen werden nur von bereits
  hinzugefügten Freund-IDs akzeptiert; optionale Ende-zu-Ende-Verschlüsselung
  pro Freund über einen manuell geteilten AES-Schlüssel; Bilder/Videos/Dateien
  werden nach `vp4_daten/empfangen/` gestreamt (Dateiname wird sanitisiert,
  kein Path-Traversal möglich); Limit 300 MB pro Datei, Verschlüsselung nur
  bis 50 MB (sonst unverschlüsselter Versand mit Warnhinweis).

**Getestet wurde (in der Cloud-Sandbox, Linux mit Xvfb, nicht auf echtem
Windows):**
- Alle Chiffren inkl. Roundtrip und Fehlerfälle (falscher Schlüssel etc.)
- Schlüsselspeicher: anlegen, entsperren, falsches Passwort, doppelte Namen
- Obsidian-Export/-Import inkl. Erhalt von handgeschriebenem Notizinhalt
- Chat-Protokoll Ende-zu-Ende zwischen zwei simulierten Instanzen: Text
  (verschlüsselt und unverschlüsselt), Dateiübertragung, Ablehnung fremder
  (nicht befreundeter) IDs
- GUI baut headless fehlerfrei auf, Verschlüsseln/Entschlüsseln über die
  echte GUI funktioniert

**Nicht getestet** (weil die Cloud-Sandbox kein echtes Windows / WLAN hat):
- Tatsächliches Funktionieren von UDP-Broadcast/TCP im echten Heim-WLAN
  zwischen zwei echten PCs
- Verhalten unter Windows Firewall (ggf. muss der Nutzer beim ersten Start
  eine Firewall-Freigabe für Python/die .exe erteilen – das ist normal bei
  Port-Listenern, aber gut, Leon das kurz zu erklären)
- PyInstaller-Build zu einer .exe (Anleitung steht im Kopfkommentar von
  `VP4.py`, aber nie tatsächlich ausgeführt)

## Deine Aufgaben jetzt (Claude Code, lokal auf Windows)

1. Prüfe, ob Python 3.9+ vorhanden ist (`python --version`), installiere bei
   Bedarf `pip install cryptography`.
2. Starte `python VP4.py` und prüfe, dass sich das Fenster öffnet und alle
   Tabs (Ver-/Entschlüsseln, Schlüsselverwaltung, Obsidian, Chat, Info)
   fehlerfrei funktionieren.
3. Wenn möglich: teste den Chat wirklich zwischen zwei Geräten im selben
   WLAN (z. B. mit einem Freund, oder zwei Instanzen auf demselben PC unter
   unterschiedlichen Freund-IDs, falls das für einen ersten Rauchtest
   ausreicht). Prüfe insbesondere, ob die Windows-Firewall beim ersten Start
   nachfragt und was danach passiert.
4. Baue eine `.exe`, damit Leons Freunde kein Python brauchen:
   ```
   pip install pyinstaller
   pyinstaller --onefile --noconsole --name "VP4" VP4.py
   ```
   Die fertige Datei liegt danach unter `dist/VP4.exe`. Teste sie auf einem
   Rechner ohne Python, falls möglich.
5. Geh die "Offene Punkte" unten mit Leon durch, bevor du größere
   Design-Entscheidungen (z. B. UI-Neugestaltung) triffst – nicht raten,
   nachfragen.
6. Behalte die Architektur bei (eine Python-Datei, `cryptography` als
   einzige externe Abhängigkeit, Daten unter `vp4_daten/`), außer Leon sagt
   explizit, dass er etwas anderes will.

## Offene Punkte – bitte mit Leon klären, nicht raten

- Reicht ihm die aktuelle Verfahrensauswahl (Caesar/Vigenère/XOR/Base64/
  AES-256/RSA-2048), oder fehlt ihm etwas Bestimmtes?
- Will er standardmäßig eine fertige `.exe` statt der `.py`-Datei bekommen
  (siehe Schritt 4 oben) – und soll die automatisch an Freunde mitgeschickt
  werden?
- Soll der Chat verpflichtend Ende-zu-Ende-verschlüsselt sein (aktuell
  optional pro Freund), auch wenn das den Ersteinrichtungs-Aufwand für seine
  Freunde erhöht (Schlüsselaustausch)?
- Soll es ein eigenes Programm-Icon/Design geben?
- Soll beim Empfang eines Bildes/Videos im Chat automatisch ein
  "Öffnen"-Button erscheinen (aktuell wird nur der Speicherort in der
  Chat-Historie angezeigt)?

## Wichtiger Hinweis zu Sicherheit/Ehrlichkeit

Das ist ein privates Hobby-Projekt, kein geprüftes Sicherheitsprodukt – das
steht auch im Kopfkommentar von `VP4.py` und sollte bei allen Änderungen so
bleiben (keine übertriebenen Sicherheitsversprechen machen). Der
Obsidian-Export schreibt Schlüssel im Klartext in eine Markdown-Datei – das
ist Absicht (Leon wollte das ausdrücklich so), aber der Warnhinweis dazu in
der App sollte erhalten bleiben.
