# Auftrag: Verschlüsselungs Programm 4.0

Diese Datei wird von Claude Code automatisch als Projekt-Kontext gelesen.
Lies sie zuerst.

## Wer das hier ist

Leon (16, Schüler) baut ein eigenständiges Windows-Desktop-Programm, das er
als Datei an Freunde verschickt, die es auf ihrem eigenen PC benutzen.

## Was Leon wollte

1. Verschiedene Verschlüsselungen ver- und entschlüsseln, inkl. eigener
   Schlüssel, die man speichern kann.
2. Verknüpfung mit Obsidian, um die Schlüssel dort zu verwalten.
3. **Kein Claude / keine KI zur Laufzeit** – rein lokal.
4. Ver- **und** Entschlüsseln muss beides funktionieren.
5. Ein Chat, bei dem jede Installation beim ersten Start eine ID bekommt.
   Über diese ID Freunde hinzufügen, chatten, Bilder/Videos schicken –
   alles direkt übers WLAN, ohne Server und ohne Internet.
6. **Eine moderne Oberfläche.** Leon hat die ursprüngliche Tkinter-Fassung
   ausdrücklich abgelehnt ("viel zu simpel", "sieht aus wie 1730"). Optik ist
   für ihn ein eigenes Qualitätsmerkmal, kein Beiwerk.
7. **Master-Passwort beim ersten Start**, ohne Wiederherstellung. Vergessen
   heißt: Programm neu einrichten, gespeicherte Schlüssel sind weg. Das war
   ausdrücklich Leons Wunsch.

## Aufbau

    VP4.py        Einstiegspunkt – prüft die Pakete und startet die Oberfläche
    gui.py        Oberfläche (CustomTkinter, Seitenleiste, Dark Mode)
    krypto.py     alle 13 Verfahren, Signaturen, Prüfsummen
    speicher.py   Schlüsselspeicher, Einstellungen, Freundesliste, Obsidian
    chat.py       LAN-Chat (UDP-Discovery, TCP-Übertragung)
    test_vp4.py   Selbsttest – 89 Prüfungen

Abhängigkeiten: `cryptography` und `customtkinter`. Die zweite kam mit dem
Oberflächen-Neubau dazu; Leon hat der Abwägung zugestimmt (Qt hätte besser
ausgesehen, aber die `.exe` auf 80–150 MB aufgebläht – zum Verschicken an
Freunde zu viel).

## Regeln für die Arbeit hier

1. **Nach jeder Änderung `python test_vp4.py` laufen lassen.** Wenn du etwas
   reparierst, ergänze vorher eine Prüfung, die den Fehler zeigt – dann ist
   belegt, dass der Fix wirklich greift.
2. **Bei Oberflächenarbeit wirklich hinsehen.** Starte das Fenster und mach
   einen Screenshot. Zwei überlappende Beschriftungen sind genau so
   aufgefallen und wären in keinem Test hochgekommen.
3. **Keine übertriebenen Sicherheitsversprechen.** Das ist ein privates
   Hobby-Projekt, kein geprüftes Sicherheitsprodukt. Die klassischen Verfahren
   sind ausdrücklich als "nur zum Spielen" gekennzeichnet – das muss so
   bleiben.
4. **Größere Design-Entscheidungen mit Leon klären, nicht raten.**

## Stand (August 2026)

Auf echtem Windows verifiziert: Python 3.13, `cryptography` 46,
`customtkinter` 5.2.2. Alle 89 Prüfungen bestehen, alle sieben Seiten bauen
fehlerfrei auf, Hell/Dunkel lässt sich umschalten.

### Fünf ernste Fehler wurden gefunden und behoben

Alle stammen daher, dass in der ursprünglichen Linux-Sandbox niemand mit
deutschen Texten, langen Schlüsseln, echten Verbindungsabbrüchen oder auf
echtem Windows getestet hat. Details stehen in den Commit-Nachrichten.

1. **Vigenère zerstörte Umlaute.** Aus `äöüß` wurde `btzw`, der Klartext war
   weg. `ch.isalpha()` ist in Python auch für `ä` wahr, die Rechnung darunter
   ist aber reines ASCII.
2. **Der Obsidian-Export zerstörte lange Schlüssel.** Abgeschnitten bei 120
   Zeichen; ein RSA-Schlüssel ist rund 1700 Zeichen lang und kam unbrauchbar
   zurück.
3. **Ein abgestürzter Empfangs-Thread machte einen Freund unerreichbar.** Eine
   verschlüsselte Nachricht ohne hinterlegten Schlüssel ließ den Thread
   sterben; die tote Verbindung blockierte danach alles bis zum Neustart.
4. **Die Chat-Ports lagen im dynamischen Windows-Bereich.** Windows vergibt
   alles ab 49152 selbst an ausgehende Verbindungen – der Chat-Server startete
   deshalb manchmal gar nicht. Jetzt 41230/41231. **Diese Grenze nicht wieder
   überschreiten**, ein Test prüft das.
5. **Netzwerkfehler waren unsichtbar.** Sie gingen über `print()` ins Leere –
   eine Fensteranwendung hat keine Konsole, und in der `.exe` mit
   `--noconsole` erst recht nicht. Jetzt Statusleiste plus Dialog bei schweren
   Startfehlern.

### Noch offen

- Die `.exe` wurde weiterhin nicht gebaut.
- Der Chat lief noch nicht zwischen zwei **echten** PCs im WLAN, nur über
  localhost. Das Verhalten der Windows-Firewall ist damit ungeklärt.
- **Bekannte Design-Schwäche:** Chat-IDs werden offen per Broadcast verteilt,
  und beim Verbindungsaufbau wird nur behauptet, wer man ist – nachgeprüft
  wird es nicht. Wer im selben WLAN ist, könnte sich als Freund ausgeben. Mit
  den Ed25519-Signaturen aus `krypto.py` ließe sich das lösen; mit Leon
  besprechen, bevor jemand das umbaut.
