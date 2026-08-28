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

    VP4.py               Einstiegspunkt – prüft die Pakete und startet die Oberfläche
    gui.py               Oberfläche (CustomTkinter, Seitenleiste, Dark Mode)
    krypto.py            alle 13 Verfahren, Signaturen, Prüfsummen
    dateien.py           Dateien und Ordner als .vp4-Container (gestreamt)
    speicher.py          Schlüsselspeicher, Einstellungen, Freundesliste, Obsidian
    chat.py              LAN-Chat (UDP-Discovery, TCP-Übertragung)
    transport.py         wählt den Weg: WLAN, Discord oder beides
    discord_transport.py Chat über einen Discord-Kanal
    discord_konfig.py    Platzhalter für den eingebauten Bot-Zugang
    test_vp4.py          Selbsttest – 241 Prüfungen

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
25.1, `customtkinter` 5.2.2, `discord.py` 2.7.1. Alle 241 Prüfungen bestehen,
alle acht Seiten bauen fehlerfrei auf, Hell/Dunkel lässt sich umschalten. Die
`VP4.exe` ist gebaut (34 MB, `python bauen.py`) und wird über einen
GitHub-Workflow veröffentlicht. Das Repository liegt unter
<https://github.com/FarHeadphone2753/VP4> (öffentlich; Standardzweig
`master`).

**Weil es öffentlich ist, dürfen die drei Secrets `DISCORD_BOT_TOKEN`,
`DISCORD_KANAL_ID` und `VP4_GRUPPEN_SCHLUESSEL` dort nicht hinterlegt
werden.** Sonst hinge an jedem Release eine `.exe`, aus der sich Token und
Gruppenschlüssel herausholen lassen – und zwar von jedem, nicht nur von
Leons Freunden. `discord_konfig.py` sagt es selbst: „Diese .exe sollte man
nicht öffentlich zum Download anbieten." Ohne die Secrets läuft der Workflow
unverändert durch, nur ohne eingebauten Discord-Zugang (der `else`-Zweig in
`release.yml` schreibt das auch so ins Protokoll). Die `.exe` für Freunde
entsteht dann lokal mit `python bauen.py` und wird direkt verschickt. Der Chat über Discord ist mit einem echten
Bot in einem echten Kanal durchgespielt worden – Text, mehrteilige
Nachrichten und eine 200-KB-Datei.

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

**Nachtrag:** `_spaeter()` trug die Kennungen zwar ein, aber nie wieder aus –
ein gelaufener Auftrag blieb als toter Eintrag stehen, bei 300 ms Takt rund
12.000 pro Stunde. Aufgefallen ist es daran, dass genau die Zählung oben mal
durchlief und mal nicht, je nachdem ob zufällig gerade ein Zeitgeber gefeuert
hatte. Ein gelaufener Auftrag trägt sich jetzt selbst aus; ein eigener Test
prüft das direkt, statt sich auf das Timing zu verlassen.

Und deshalb wird beim Farbwechsel auch nur der **Inhalt** neu gebaut
(`_oberflaeche_neu_bauen()`), nicht das Fenster: der Rahmen bleibt stehen,
Grösse, Position, Netzwerk und Schlüsselspeicher bleiben unangetastet.

### Knöpfe nur noch über knopf()

Das Rezept für einen Knopf stand rund dreissig Mal wortgleich im Code. Neue
Knöpfe bitte über `gui.knopf(eltern, text, befehl, art=...)` bauen. Wichtig:
**gefüllte Elemente brauchen eine ausdrückliche Textfarbe.** Solange der
Akzent Blau war, fiel das nicht auf; bei einem hellen Akzent stand plötzlich
grauer Text auf hellem Grund.

### Der Chat über Discord

Der LAN-Chat reicht nur bis zur Wohnungstür. Damit Leons Freunde von zu Hause
aus schreiben können, geht dieselbe verschlüsselte Nachricht wahlweise durch
einen Discord-Textkanal. `transport.ChatVermittler` hält beide Wege und sieht
nach aussen aus wie `ChatNetwork`; die Oberfläche merkt nichts davon. Drei
Betriebsarten: `lan` (Voreinstellung), `discord`, `beide` – bei `beide` hat
das WLAN Vorrang, weil dort nichts das Haus verlässt.

Jede Zeile im Kanal trägt einen offenen Kopf und verschlüsselte Nutzlast:

    VP4D1|<von>|<an>|<nachrichten-id>|<teil>|<gesamt>|<typ>|<base64>

Verschlüsselt wird mit denselben Funktionen wie im WLAN
(`chat.payload_verschluesseln`) – bewusst auf Modulebene, damit es nicht
zwei Kopien gibt, die irgendwann auseinanderlaufen. **Über Discord geht
ausschliesslich Verschlüsseltes:** im Kanal liest jedes Server-Mitglied mit
und Discord speichert alles dauerhaft. Fehlt der gemeinsame Schlüssel, wird
das Senden abgelehnt statt still im Klartext gemacht.

Drei Punkte, die beim Ändern nicht verlorengehen dürfen:

1. **Nachrichten werden auf 1900 Zeichen pro Zeile zerlegt** (Discord lässt
   2000 zu) und beim Empfänger wieder zusammengesetzt – auch in verkehrter
   Reihenfolge, denn Discord garantiert keine.
2. **`payload_entschluesseln` macht aus `InvalidTag` einen `ValueError`.**
   AES-GCM meldet einen falschen Schlüssel mit einem Fehler ganz ohne Text;
   der Discord-Empfang unterscheidet aber genau danach, ob er "war für dich,
   ging aber nicht auf" meldet oder still verwirft. Ohne die Übersetzung
   verschwanden solche Nachrichten wortlos.
3. **`DiscordTransport.start()` tut im `VP4_TESTMODUS` nichts.** Sonst hängt
   sich jeder Selbsttestlauf mit dem echten Bot in den echten Kanal, sobald
   in `vp4_daten/discord.json` Zugangsdaten stehen.

**Damit Freunde nichts einrichten müssen**, setzt der GitHub-Workflow beim
Bauen der `.exe` Token, Kanal-ID **und Gruppenschlüssel** aus den
Repository-Secrets (`DISCORD_BOT_TOKEN`, `DISCORD_KANAL_ID`,
`VP4_GRUPPEN_SCHLUESSEL`) in `discord_konfig.py` ein. Im Quelltext bleibt die
Datei leer – ein Test wacht darüber, dass dort nie ein echter Token committet
wird. Was der Benutzer unter Einstellungen → Discord einträgt, geht dem
eingebauten Zugang immer vor. Ebenso ist `transport_modus` seit diesem Ausbau
auf `beide` voreingestellt: der Chat soll laufen, sobald jemand das Programm
offen hat.

### Der Gruppenschlüssel – und was er nicht kann

Leon wollte ausdrücklich, dass Freunde **sofort** schreiben können, ohne
vorher Schlüssel auszutauschen. Deshalb steckt in der `.exe` ein gemeinsamer
AES-256-Schlüssel (`chat.gruppen_schluessel_b64()`), der greift, wenn für
einen Freund kein eigener hinterlegt ist.

**Das ist bewusst eine Bequemlichkeitsentscheidung, keine
Sicherheitsverbesserung.** Gegen Discord und gegen Fremde im Server schützt
er vollständig; untereinander gar nicht – wer dieselbe `.exe` hat, kann jede
Nachricht im Kanal mitlesen, auch die zwischen zwei anderen. Leon kennt diese
Abwägung und hat sie so gewollt.

Was daraus folgt und nicht wegfallen darf:

1. **Ein eigener Schlüssel für einen Freund geht immer vor** – nur der
   schützt auch vor den anderen aus der Gruppe. Ein Test hält das fest.
2. **Die Oberfläche sagt den Unterschied.** In der Freundesliste steht 🔒
   für einen eigenen Schlüssel und 👥 für den Gruppenschlüssel, und über dem
   Chat steht ausgeschrieben „Gruppenschlüssel (alle mit VP4 können
   mitlesen)". „🔒 verschlüsselt" allein würde hier mehr versprechen, als es
   hält – siehe Regel 3 oben.
3. Der Schlüssel selbst gehört wie der Token in die GitHub-Secrets, nie in
   den Quelltext.

Auf echtem Discord verifiziert (August 2026, Bot `Encrypt-Relay#4140`): Text
mit Umlauten, eine über mehrere Zeilen zerlegte Antwort, eine 200-KB-Datei
Byte für Byte – und im Kanal steht nur Kopf plus Geheimtext.

### Gruppen

Leon wollte Gruppen: ein Knopf zum Erstellen, einer zum Beitreten, und die
Gruppe hat einen eigenen Code. Genau so ist es gebaut.

Eine Gruppe ist eine Kennung (`G-XXXXXXXX`, `speicher.ist_gruppen_id()`)
plus ein AES-256-Schlüssel. Der Einladungscode `VP4G1-…` trägt beides als
rohe Bytes – 5 für die Kennung, 32 für den Schlüssel, zusammen 56 Zeichen,
damit er in eine Zeile passt und beim Kopieren nicht zerreißt. Gespeichert
wird in `vp4_daten/gruppen.json` (`speicher.GruppenStore`).

**Eine Mitgliederliste gibt es bewusst nicht.** Wer den Code hat, ist dabei.
Das macht das Beitreten einfach und hat einen Preis, der im Programm auch so
dasteht: Ein Code lässt sich nicht zurückholen, und wer beitritt, kann auch
Älteres lesen, das noch im Kanal steht. Wer jemanden loswerden will, macht
eine neue Gruppe auf.

Vier Dinge, die beim Ändern nicht verlorengehen dürfen:

1. **In einer Gruppe zählt der Code, nicht die Freundesliste.** `zeile_lesen()`
   lässt Absender durch, die man gar nicht kennt – sonst wäre eine Gruppe
   sinnlos. Für Einzelnachrichten gilt weiterhin: unbekannter Absender,
   verworfen.
2. **Gruppen gehen nur über Discord** (`ChatVermittler._wege()`). Im WLAN gibt
   es keine Adresse für eine Gruppe: Wer dazugehört, weiß niemand.
3. **Der Absendername steckt in der verschlüsselten Nutzlast**
   (`TYP_GRUPPENTEXT`), nicht im offenen Kopf. Er ist eine Selbstauskunft –
   deshalb steht die ID in Klammern dahinter, und ein selbst vergebener Name
   aus der Freundesliste geht immer vor.
4. **Die Gruppenkennung geht in `an`**, und `schluessel_fuer()` entscheidet
   daran, welcher Schlüssel gilt. Deshalb muss beim Entschlüsseln einer
   Gruppennachricht `an` hineingehen und nicht `von`.

### Noch offen

- Der Chat lief noch nicht zwischen zwei **echten** PCs im WLAN, nur über
  localhost. Das Verhalten der Windows-Firewall ist damit ungeklärt.
- Vom Ausbauplan fehlen noch: Obsidian auf verschlüsselte Notizen im
  age-Format (Phase 2), Chat mit echtem Handschlag (Phase 3) und das
  restliche Aufräumen in `gui.py` (Phase 4) - vor allem die 1900 Zeilen in
  einer einzigen Klasse und der Chatverlauf, der bei jeder Nachricht
  komplett neu gezeichnet wird.
- **Der gemeinsame Schlüssel wird noch von Hand ausgetauscht** - und das
  steht Leons ausdrücklichem Wunsch entgegen, dass Freunde einfach
  losschreiben können, ohne etwas einzurichten. Der Bot-Token steckt seit
  dem Discord-Ausbau in der `.exe`, der Schlüssel nicht. Nächster Schritt
  wäre ein automatischer Handschlag über X25519 (die Bibliothek liegt schon
  wegen Ed25519 bei), mit einer vergleichbaren Sicherheitsnummer pro Freund
  gegen einen Mitleser im Kanal. Das ist mit Leon besprochen, aber noch
  nicht gebaut.
- Drag & Drop auf die Dateiseite fehlt; das bräuchte `tkinterdnd2` oder
  `windnd` und verträgt sich mit CustomTkinter erfahrungsgemäss schlecht.
- **Bekannte Design-Schwäche:** Chat-IDs werden offen per Broadcast verteilt,
  und beim Verbindungsaufbau wird nur behauptet, wer man ist – nachgeprüft
  wird es nicht. Wer im selben WLAN ist, könnte sich als Freund ausgeben. Mit
  den Ed25519-Signaturen aus `krypto.py` ließe sich das lösen; mit Leon
  besprechen, bevor jemand das umbaut.
