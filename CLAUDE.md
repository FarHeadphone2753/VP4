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
    dateien.py    Dateien und Ordner als .vp4-Container (gestreamt)
    speicher.py   Schlüsselspeicher, Einstellungen, Freundesliste, Obsidian
    chat.py       LAN-Chat (UDP-Discovery, TCP-Übertragung)
    test_vp4.py   Selbsttest – 151 Prüfungen

Abhängigkeiten: `cryptography`, `argon2-cffi` und `customtkinter`. Die letzte
kam mit dem Oberflächen-Neubau dazu; Leon hat der Abwägung zugestimmt (Qt hätte besser
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

Auf echtem Windows verifiziert: Python 3.13, `cryptography` 46, `argon2-cffi`
25.1, `customtkinter` 5.2.2. Alle 151 Prüfungen bestehen, alle acht Seiten
bauen fehlerfrei auf, Hell/Dunkel lässt sich umschalten. Die `VP4.exe` ist
gebaut (34 MB, `python bauen.py`) und wird über einen GitHub-Workflow
veröffentlicht.

### Dateiformate: Einstellungen stehen IN der Datei

Seit Phase 0 des Ausbauplans tragen alle passwortgeschützten Formate einen
selbstbeschreibenden Kopf:

    Marke (5) | KDF-Kennung (1) | KDF-Einstellungen | Salt (16) | Nonce (12) | Daten

Der Kopf geht als AAD in AES-GCM ein, ist also mitversiegelt. **Der Grund:**
Vorher stand die Rundenzahl nur im Programm. Wer sie erhöht hätte – und
irgendwann erhöht man sie –, hätte damit jeden bestehenden Schlüsselspeicher
unlesbar gemacht, ohne dass irgendetwas gewarnt hätte.

Marken: `VP4K3` (Schlüsselspeicher), `VP4P2` (Passwort-Verschlüsselung).
Die Vorgänger `VP4K2` und `VP4P1` werden weiterhin **gelesen**; ein alter
Speicher wird beim Entsperren still auf Argon2id gehoben. Zwei fest im
Testcode einkodierte Alt-Dateien sichern das ab – **diese Blobs niemals
anfassen.**

Abgeleitet wird mit **Argon2id** (64 MiB, 3 Durchgänge, Parallelität 1;
gemessen rund 0,08 s). Die Parameter sind durch einen Test festgenagelt: Sie
zu ändern ist erlaubt, aber nur bewusst.

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

### Der .vp4-Container (Phase 1)

`dateien.py` verschlüsselt Dateien und ganze Ordner gestreamt:

    "VP4F1" | Schlüsselart (1) | KDF-Kopf | Nonce-Basis (8)
            | Länge + verschlüsselter Kopfsatz | dann Blöcke à 1 MiB

Drei Punkte, die beim Ändern nicht verlorengehen dürfen:

1. **Nonce pro Block** = Nonce-Basis (8 Byte) + Blocknummer. Ein Nonce
   zweimal mit demselben Schlüssel wäre bei GCM der Totalschaden.
2. **In die AAD jedes Blocks gehen Blocknummer und ein Letzter-Block-
   Kennzeichen.** Ohne das liessen sich Blöcke vertauschen oder die Datei
   hinten abschneiden, ohne dass es auffällt - jeder Block für sich wäre ja
   in Ordnung. Vier Tests greifen genau diese Fälle an.
3. **Der Dateiname liegt im verschlüsselten Kopfsatz**, nicht im Klartext.

Ein Ordner wird als ZIP direkt in die Verschlüsselung geschrieben; eine
unverschlüsselte Zwischendatei entsteht nie. Beim Entschlüsseln muss das ZIP
kurz auf die Platte, weil `zipfile` beim Lesen springen können muss - es
landet im Zielordner (dort liegt der Klartext ohnehin) und wird im `finally`
wieder gelöscht.

Kommt der Schlüssel aus dem Schlüsselspeicher statt aus einem Passwort, wird
er mit **HKDF** und dem Salt der Datei gemischt (`KDF_HKDF`). Ihn langsam
durchzurechnen brächte nichts - er ist schon zufällig -, aber so bekommt
jede Datei trotzdem ihren eigenen Schlüssel.

### Lange Arbeiten laufen im Hintergrund

Die Oberfläche hatte dafür bisher gar nichts. `VP4App._auftrag_starten()`
schickt die Arbeit in einen Thread und meldet sich über **dieselbe
Warteschlange wie der Chat** zurück (`fortschritt`, `auftrag_fertig`,
`auftrag_abgebrochen`, `auftrag_fehler`). Nur der Hauptthread fasst Widgets
an. `_ereignisse_pruefen()` ist in Abarbeiten und Wiederanmelden getrennt,
damit der Selbsttest die Warteschlange sofort leeren kann.

### Zeitgeber immer über _spaeter()

`VP4App` hat zwei Daueraufträge: die Ereignis-Warteschlange alle 300 ms und
die Freundesliste alle 3 s. Sie laufen über `self._spaeter(ms, funktion)`,
das die Kennung mitschreibt, und werden von `_zeitgeber_stoppen()`
abbestellt. **Neue wiederkehrende Aufträge bitte auch so anmelden**, nie
direkt mit `self.after(...)` – sonst feuern sie nach dem Schliessen auf ein
Fenster, das es nicht mehr gibt.

Aufgefallen ist das erst, als der Farbwechsel die Oberfläche mehrfach neu
baute: bei jedem Wechsel blieb ein weiterer Auftrag zurück. Ein Test zählt
deshalb nach, dass nach mehreren Farbwechseln immer noch genau zwei offen
sind.

Und deshalb wird beim Farbwechsel auch nur der **Inhalt** neu gebaut
(`_oberflaeche_neu_bauen()`), nicht das Fenster: der Rahmen bleibt stehen,
Grösse, Position, Netzwerk und Schlüsselspeicher bleiben unangetastet.

### Knöpfe nur noch über knopf()

Das Rezept für einen Knopf stand rund dreissig Mal wortgleich im Code. Neue
Knöpfe bitte über `gui.knopf(eltern, text, befehl, art=...)` bauen. Wichtig:
**gefüllte Elemente brauchen eine ausdrückliche Textfarbe.** Solange der
Akzent Blau war, fiel das nicht auf; bei einem hellen Akzent stand plötzlich
grauer Text auf hellem Grund.

### Noch offen

- Der Chat lief noch nicht zwischen zwei **echten** PCs im WLAN, nur über
  localhost. Das Verhalten der Windows-Firewall ist damit ungeklärt.
- Vom Ausbauplan fehlen noch: Obsidian auf verschlüsselte Notizen im
  age-Format (Phase 2), Chat mit echtem Handschlag (Phase 3) und das
  restliche Aufräumen in `gui.py` (Phase 4) - vor allem die 1900 Zeilen in
  einer einzigen Klasse und der Chatverlauf, der bei jeder Nachricht
  komplett neu gezeichnet wird.
- Drag & Drop auf die Dateiseite fehlt; das bräuchte `tkinterdnd2` oder
  `windnd` und verträgt sich mit CustomTkinter erfahrungsgemäss schlecht.
- **Bekannte Design-Schwäche:** Chat-IDs werden offen per Broadcast verteilt,
  und beim Verbindungsaufbau wird nur behauptet, wer man ist – nachgeprüft
  wird es nicht. Wer im selben WLAN ist, könnte sich als Freund ausgeben. Mit
  den Ed25519-Signaturen aus `krypto.py` ließe sich das lösen; mit Leon
  besprechen, bevor jemand das umbaut.
