<div align="center">

<img src="vp4.png" width="120" alt="VP4">

# Verschlüsselungs Programm 4.0

**Texte verschlüsseln, Schlüssel verwalten und im WLAN chatten – alles auf deinem eigenen Rechner.**

Kein Konto, kein Server, keine Internetverbindung nötig. Nichts wird irgendwohin geschickt.

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
Herumprobieren taugt.

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

### Chat im WLAN

Jede Installation bekommt beim ersten Start eine eigene ID wie `7AC5-EHTN`.
Tauscht die IDs, und ihr könnt chatten und Bilder oder Videos schicken – direkt
zwischen euren Rechnern, ohne Server und ohne Internet.

Für verschlüsselte Nachrichten tragt ihr **beide denselben gemeinsamen
Schlüssel** ein (🔑 in der Freundesliste). Ohne das gehen die Nachrichten
unverschlüsselt durchs WLAN.

**Der Chat funktioniert nur im selben WLAN.** Über das Internet geht es nicht –
dafür bräuchte es einen Server, den es (noch) nicht gibt.

---

## Das Master-Passwort – bitte einmal lesen

Beim ersten Start legst du ein Master-Passwort fest. Damit wird dein
Schlüsselspeicher verschlüsselt.

**Das Passwort wird nirgends gespeichert.** Nicht im Klartext, nicht
verschlüsselt, nirgends. Aus ihm wird nur der Schlüssel berechnet, mit dem die
Datei ver- und entschlüsselt wird.

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
| Freund taucht nicht auf | Seid ihr im **selben** WLAN? Ein Gäste-WLAN trennt Geräte voneinander ab. |
| Unten steht „Chat: Fehler" | Der Port war belegt. VP4 einmal beenden und neu starten. |
| Niemand erreicht dich | Hat die Windows-Firewall beim ersten Start gefragt? VP4 muss erlaubt sein. |
| „Nachricht konnte nicht entschlüsselt werden" | Ihr habt unterschiedliche gemeinsame Schlüssel eingetragen. Einer erzeugt einen neuen, schickt ihn dem anderen, beide tragen genau denselben ein. |

---

## Selbst bauen

Du brauchst Python 3.9 oder neuer.

```bash
pip install cryptography customtkinter pillow pyinstaller

python VP4.py        # direkt starten
python test_vp4.py   # Selbsttest (90 Prüfungen)
python bauen.py      # eigene VP4.exe erzeugen -> dist/VP4.exe
```

### Aufbau

| Datei | Inhalt |
|---|---|
| `VP4.py` | Einstiegspunkt |
| `gui.py` | Oberfläche (CustomTkinter, Dark Mode) |
| `krypto.py` | Alle Verfahren, Signaturen, Prüfsummen |
| `speicher.py` | Schlüsselspeicher, Einstellungen, Obsidian |
| `chat.py` | LAN-Chat |
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

Und eine bekannte Schwäche, die du kennen solltest: Beim Chat wird beim
Verbindungsaufbau nur **behauptet**, wer man ist – nachgeprüft wird es nicht.
Wer im selben WLAN sitzt, könnte sich als einer deiner Freunde ausgeben. Unter
Freunden im Heimnetz ist das in Ordnung, für Vertrauliches nicht.
