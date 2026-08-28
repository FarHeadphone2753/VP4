<div align="center">

<img src="vp4.png" width="120" alt="VP4">

# Verschlüsselungs Programm 4.0

**Texte, Dateien und Ordner verschlüsseln, Schlüssel verwalten und mit Freunden chatten.**

Kein Konto, keine Anmeldung, kein eigener Server. Sitzt ihr im selben WLAN, läuft
der Chat direkt zwischen euren Rechnern. Wenn nicht, nimmt er den Umweg über einen
Discord-Kanal – verschlüsselt, Discord bekommt nur Geheimtext zu sehen.

</div>

---

## Herunterladen

1. Auf **[Releases](../../releases)** gehen und `VP4.exe` herunterladen.
2. Doppelklicken. Fertig – **du brauchst kein Python und musst nichts installieren.**

> **Windows warnt beim ersten Start.** Es erscheint „Der Computer wurde durch
> Windows geschützt". Das liegt daran, dass das Programm nicht signiert ist –
> eine Signatur kostet mehrere hundert Euro im Jahr, und das ist ein privates
> Hobby-Projekt. Klick auf **Weitere Informationen** → **Trotzdem ausführen**.
>
> Wenn du dem nicht traust: Der komplette Quelltext liegt hier offen, und du
> kannst die `.exe` mit `python bauen.py` jederzeit selbst erzeugen.

Beim allerersten Start legst du ein **Master-Passwort** fest. Lies dazu unbedingt
den Abschnitt weiter unten – es gibt keine Wiederherstellung.

---

## Was das Programm kann

### Verschlüsseln und Entschlüsseln

13 Verfahren, und bei jedem steht dabei, ob es wirklich sicher ist oder nur zum
Herumprobieren taugt. Für Dateien und Ordner gibt es eine eigene Seite,
siehe unten.

**Sicher – dafür geeignet, etwas zu schützen:**

| Verfahren | Wofür |
|---|---|
| **AES-256-GCM** | Der Standard. Wenn du dich nicht entscheiden willst: nimm das. |
| **ChaCha20-Poly1305** | Gleichwertig zu AES, auf älteren Geräten schneller. |
| **Passwort (AES-256)** | Du gibst einfach ein Passwort ein statt einen langen Schlüssel. Am praktischsten, wenn du jemandem etwas schicken willst. |
| **RSA-2048** | Zwei Schlüssel: Der öffentliche darf jeder haben, mit dem privaten entschlüsselst du. Nur für kurze Texte. |

**Nur zum Spielen – in Sekunden zu knacken:**

Caesar · Vigenère · Playfair · Rail-Fence · ROT13 · Atbash · Morse · XOR · Base64

Diese Verfahren sind Jahrhunderte alt und interessant zum Ausprobieren – aber
schütze damit nichts, was wirklich geheim bleiben soll.

### Dateien und ganze Ordner

Nicht nur Text: VP4 verschlüsselt auch **Dateien und komplette Ordner** zu
einer `.vp4`-Datei. Das läuft im Hintergrund mit Fortschrittsbalken und
Abbrechen-Knopf, und die Grösse spielt keine Rolle – die Daten wandern
blockweise durch und müssen nie ganz in den Arbeitsspeicher passen.

Der **Dateiname steckt mit im verschlüsselten Teil**. Von aussen ist an
`Zeugnis.pdf.vp4` also nicht abzulesen, was drin war – man sieht nur eine
Datei namens `Zeugnis.pdf.vp4`, deshalb den Namen ruhig noch ändern.

Wird an einer verschlüsselten Datei auch nur ein Bit verändert, ein Stück
abgeschnitten oder etwas umsortiert, merkt VP4 das beim Entschlüsseln und
gibt lieber einen Fehler aus, als halb richtige Daten.

⚠️ Das Original bleibt liegen. **VP4 löscht von sich aus nichts** – wenn du
es weghaben willst, musst du es selbst löschen. (Und ehrlich gesagt: auf
einer SSD bekommt man Daten mit normalem Löschen ohnehin nicht sicher weg,
egal was Programme mit „Schreddern" im Namen versprechen.)

### Schlüsselspeicher

Deine Schlüssel liegen verschlüsselt auf der Festplatte, geschützt durch dein
Master-Passwort. Du kannst sie benennen, mit Notizen versehen und direkt beim
Verschlüsseln einsetzen.

### Signieren und Prüfsummen

Mit einer **Ed25519-Signatur** beweist du, dass ein Text wirklich von dir stammt
und unterwegs nicht verändert wurde. Der Text bleibt dabei lesbar – das ist
etwas anderes als Verschlüsseln. Dazu Prüfsummen (SHA-256 und andere), um zu
prüfen, ob zwei Dateien exakt gleich sind.

### Obsidian-Verknüpfung

Schlüssel lassen sich als Notiz in einen Obsidian-Vault schreiben und von dort
wieder einlesen. Praktisch, wenn du deine Notizen ohnehin dort hast.

⚠️ In der Notiz stehen die Schlüssel **im Klartext**. Wird dein Vault über
Obsidian Sync, iCloud oder Dropbox synchronisiert, wandern sie mit.

### Chat – im WLAN und von überall

Jede Installation bekommt beim ersten Start eine eigene ID wie `7AC5-EHTN`.
Tauscht die IDs, und ihr könnt chatten und Bilder oder Videos schicken.

VP4 sucht sich den Weg selbst:

| Weg | Wann | Was passiert |
|---|---|---|
| **Direkt im WLAN** | Ihr seid im selben Netz | Die Nachricht geht unmittelbar von Rechner zu Rechner. Nichts verlässt die Wohnung. |
| **Über Discord** 🌐 | Ihr seid es nicht | Die fertig verschlüsselte Nachricht nimmt den Umweg über einen Discord-Kanal. |

Das WLAN hat dabei immer Vorrang – dort bleibt alles im Haus. Eine Chatzeile
zeigt mit 🌐, wenn sie den Umweg genommen hat. Umstellen kannst du das unter
**Einstellungen → Chat-Weg**.

### Gruppen

Neben einzelnen Freunden gibt es Gruppen. **＋ Gruppe** macht eine neue auf,
**Beitreten** bringt dich in eine fremde, **Code** zeigt den Einladungscode.

Der Code ist die ganze Mitgliedschaft: Wer ihn hat, ist dabei – eine Liste, wer
dazugehört, gibt es nicht. Das macht das Beitreten einfach und hat einen Preis:
Zurückholen lässt sich ein Code nicht, und wer beitritt, kann auch Älteres
lesen, das noch im Kanal steht. Soll jemand nicht mehr mitlesen, macht ihr eine
neue Gruppe auf.

Gruppen laufen immer über Discord – auch wenn ihr im selben WLAN sitzt. Im WLAN
müsste VP4 wissen, an wen es die Nachricht schicken soll, und das weiß bei einer
Gruppe niemand.

### Wie gut sind die Nachrichten geschützt?

Das steht im Programm über jedem Chat und neben jedem Freund:

- **🔒 Ein eigener Schlüssel**, den nur ihr zwei habt (🔑 in der Freundesliste).
  Niemand sonst kann mitlesen, auch kein anderer VP4-Benutzer.
- **👥 Der eingebaute Gruppenschlüssel.** Er steckt in der Programmdatei, damit
  ihr sofort loslegen könnt, ohne vorher etwas auszutauschen. Gegen Discord und
  gegen Fremde schützt er vollständig – aber **jeder, der dasselbe VP4 hat, kann
  alles im Kanal mitlesen**, auch Nachrichten zwischen zwei anderen. Das ist eher
  ein Gruppenchat als ein privates Gespräch.
- **🔓 Gar kein Schlüssel.** Geht nur im WLAN. Über Discord verschickt VP4
  grundsätzlich nichts Unverschlüsseltes – dort liest sonst jedes Server-Mitglied
  mit, und Discord speichert alles dauerhaft.

Willst du mit einem bestimmten Freund wirklich unter vier Augen schreiben, trag
für ihn einen eigenen Schlüssel ein. Der geht dem Gruppenschlüssel immer vor.

Über den Chat gehen zurzeit höchstens 50 MB verschlüsselt. Ist eine Datei
grösser, **schickt VP4 sie nicht heimlich im Klartext**, sondern sagt es dir:
verschlüssele sie dann auf der Seite *Dateien* und schicke die `.vp4`.

---

## Das Master-Passwort – bitte einmal lesen

Beim ersten Start legst du ein Master-Passwort fest. Damit wird dein
Schlüsselspeicher verschlüsselt.

**Das Passwort wird nirgends gespeichert.** Nicht im Klartext, nicht
verschlüsselt, nirgends. Aus ihm wird nur der Schlüssel berechnet, mit dem die
Datei ver- und entschlüsselt wird – mit **Argon2id**, einem Verfahren, das
absichtlich Zeit *und* 64 MB Arbeitsspeicher verbraucht. Der Speicherbedarf ist
der eigentliche Trick: Daran scheitern Grafikkarten, die sonst Tausende
Passwörter gleichzeitig durchprobieren könnten.

Das bedeutet: **Wenn du es vergisst, kommst du nie wieder an deine gespeicherten
Schlüssel.** Niemand kann das rückgängig machen – auch dieses Programm nicht.
Dann bleibt nur, den Ordner `vp4_daten` zu löschen und neu anzufangen.

Das ist unbequem, aber genau der Grund, warum der Speicher etwas taugt: Jede
Wiederherstellungsmöglichkeit wäre auch ein Weg für jemand anderen.

👉 **Schreib dir das Passwort auf, bevor du es eingibst.**

---

## Wenn der Chat nicht funktioniert

| Problem | Was hilft |
|---|---|
| Freund taucht nicht auf | Im selben WLAN: Ein Gäste-WLAN trennt Geräte voneinander ab. Sonst muss unter **Einstellungen → Chat-Weg** „WLAN und Discord" oder „nur Discord" stehen. |
| Nichts geht über Discord | Ist ein Discord-Zugang hinterlegt? In der fertigen `VP4.exe` steckt er drin; startest du aus dem Quelltext, trägst du ihn unter **Einstellungen → Discord** selbst ein. |
| Unten steht „Chat: Fehler" | Der Port war belegt. VP4 einmal beenden und neu starten. |
| Niemand erreicht dich | Hat die Windows-Firewall beim ersten Start gefragt? VP4 muss erlaubt sein. |
| „Nachricht konnte nicht entschlüsselt werden" | Ihr habt unterschiedliche gemeinsame Schlüssel eingetragen. Einer erzeugt einen neuen, schickt ihn dem anderen, beide tragen genau denselben ein. |

---

## Selbst bauen

Der Quelltext liegt unter **[github.com/FarHeadphone2753/VP4](https://github.com/FarHeadphone2753/VP4)**.
Du brauchst Python 3.9 oder neuer.

```bash
git clone https://github.com/FarHeadphone2753/VP4.git
cd VP4

pip install cryptography argon2-cffi customtkinter pillow pyinstaller discord.py

python VP4.py        # direkt starten
python test_vp4.py   # Selbsttest (241 Prüfungen)
python bauen.py      # eigene VP4.exe erzeugen -> dist/VP4.exe
```

### Aufbau

| Datei | Inhalt |
|---|---|
| `VP4.py` | Einstiegspunkt |
| `gui.py` | Oberfläche (CustomTkinter, Dark Mode) |
| `krypto.py` | Alle Verfahren, Signaturen, Prüfsummen |
| `dateien.py` | Dateien und Ordner als `.vp4`-Container |
| `speicher.py` | Schlüsselspeicher, Einstellungen, Obsidian |
| `chat.py` | Chat im WLAN |
| `transport.py` | Wählt den Weg: WLAN, Discord oder beides |
| `discord_transport.py` | Chat über einen Discord-Kanal |
| `test_vp4.py` | Selbsttest |

Deine Daten liegen in `vp4_daten` neben dem Programm. Dieser Ordner gehört dir
allein – er wird nie mit hochgeladen.

---

## Ehrlich gesagt

Das hier ist ein privates Hobby-Projekt, **kein geprüftes Sicherheitsprodukt**.
Die verwendete Kryptografie ist Standard und selbst nicht gebastelt (die
Bibliothek `cryptography`), aber das Programm drumherum hat niemand fachlich
geprüft.

Für wirklich Wichtiges – Bankdaten, Passwörter für echte Konten – sollte das
nicht deine einzige Absicherung sein.

Und zwei bekannte Schwächen, die du kennen solltest:

Beim Chat wird beim Verbindungsaufbau nur **behauptet**, wer man ist –
nachgeprüft wird es nicht. Wer im selben WLAN sitzt oder im selben Discord-Kanal
ist, könnte sich als einer deiner Freunde ausgeben.

Und der eingebaute Gruppenschlüssel ist eine **Bequemlichkeit, keine
Sicherheitsverbesserung**: Er sorgt dafür, dass ihr sofort losschreiben könnt,
schützt euch aber nicht voreinander. Wer dasselbe VP4 hat, liest im Kanal alles
mit. Für ein Programm unter Freunden ist beides in Ordnung, für Vertrauliches
nicht – dafür gibt es die eigenen Schlüssel.
