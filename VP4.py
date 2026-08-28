#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 Verschlüsselungs Programm 4.0  (VP4)
=====================================================================
Starten mit:      python VP4.py

Was das Programm kann:

  1) Texte ver- und entschlüsseln - mit 13 Verfahren, von Caesar zum
     Ausprobieren bis AES-256 und ChaCha20 für echten Schutz
  2) Ganze Dateien und Ordner verschlüsseln - auch sehr grosse, sie
     wandern blockweise durch und passen nie ganz in den Speicher
  3) Eigene Schlüssel speichern und verwalten, geschützt durch ein
     Master-Passwort
  4) Texte signieren (beweist, dass etwas von dir kommt) und
     Prüfsummen berechnen
  5) Schlüssel als Notiz in einen Obsidian-Vault schreiben und von
     dort wieder einlesen
  6) Im eigenen WLAN chatten und Bilder/Videos schicken - direkt
     zwischen den Rechnern, ohne Server und ohne Internet
  7) Wahlweise über einen Discord-Kanal chatten, wenn der Freund nicht
     im selben WLAN sitzt. Verschlüsselt wird genauso; Discord bekommt
     nur den Geheimtext zu sehen. Dafür braucht es zusätzlich
     "pip install discord.py" - ohne das Paket läuft alles andere
     weiter, nur dieser eine Weg nicht.
  8) Gruppen: eine aufmachen, den Code weitergeben, und alle, die ihn
     haben, schreiben miteinander - ohne dass sich jemand vorher
     kennen muss.

Ver- und Entschlüsseln passiert vollständig auf deinem Rechner, und
zur Laufzeit wird keine KI gebraucht. Ins Internet geht nur, was du
selbst über den Chat verschickst - und auch das nur verschlüsselt.


DIE DATEIEN
------------
  VP4.py        diese Datei - startet nur das Programm
  gui.py        die Oberfläche (CustomTkinter, mit Dark Mode)
  krypto.py     alle Ver- und Entschlüsselungsverfahren
  dateien.py    Dateien und Ordner als .vp4-Container
  speicher.py   Schlüsselspeicher, Einstellungen, Obsidian
  chat.py       der LAN-Chat
  transport.py  wählt den Weg: WLAN, Discord oder beides
  discord_transport.py   der Chat über einen Discord-Kanal
  discord_konfig.py      Platzhalter für den eingebauten Bot-Zugang
  test_vp4.py   Selbsttest - nach Änderungen ausführen!

Die Aufteilung gibt es, weil alles zusammen in einer Datei bei über
3000 Zeilen unübersichtlich wird. Für die .exe macht das keinen
Unterschied, PyInstaller packt weiterhin alles in eine Datei.


VORAUSSETZUNGEN
----------------
  - Python 3.9 oder neuer
  - Einmalig installieren:   pip install cryptography argon2-cffi customtkinter
  - Für den Chat über Discord zusätzlich:   pip install discord.py


EINE .EXE DARAUS MACHEN (damit Freunde kein Python brauchen)
-------------------------------------------------------------
  1) pip install pyinstaller
  2) pyinstaller --onefile --noconsole --name "VP4" VP4.py
  3) Die fertige Datei liegt danach in "dist" und kann verschickt und
     doppelgeklickt werden.


WICHTIG - EHRLICHE HINWEISE
----------------------------
 - Das ist ein privates Programm, kein geprüftes Sicherheitsprodukt.
   Für wirklich Wichtiges (Bankdaten, Passwörter für echte Konten)
   nicht als einzige Absicherung verwenden.
 - Das Master-Passwort wird nirgends gespeichert. Wer es vergisst,
   kommt an die gespeicherten Schlüssel nicht mehr heran - es gibt
   keine Wiederherstellung und keine Hintertür. Das ist Absicht:
   jeder Weg zurück wäre auch ein Weg für jemand anderen.
 - Die klassischen Verfahren (Caesar, Vigenère, Playfair, ROT13,
   Atbash, Morse, XOR, Base64, Rail-Fence) sind NICHT sicher. Sie
   sind zum Ausprobieren da. In der App steht das an jedem Verfahren.
 - Beim Export nach Obsidian stehen die Schlüssel im Klartext in der
   Notiz. Wird der Vault synchronisiert, werden sie mitsynchronisiert.
 - Der Chat benutzt, wenn nichts anderes eingetragen ist, den in die
   .exe eingebauten Schlüssel. Der schützt gegen Discord und gegen
   Fremde, aber nicht untereinander: Wer dieselbe .exe hat, kann alles
   im Kanal mitlesen. Für ein Gespräch unter vier Augen trägt man für
   den Freund einen eigenen Schlüssel ein.
 - Dasselbe gilt für Gruppen: Wer den Einladungscode hat, liest mit -
   auch Älteres, das noch im Kanal steht.
 - Beim Verbindungsaufbau wird nur behauptet, wer man ist - nachgeprüft
   wird es nicht. Wer im selben WLAN oder im selben Discord-Kanal ist,
   könnte sich als ein Freund ausgeben.
=====================================================================
"""

import sys


def _abhaengigkeit_fehlt(paket: str, fehler: str):
    """Zeigt eine verständliche Meldung, wenn ein Paket fehlt.

    Möglichst als Fenster - in der .exe gibt es keine Konsole, dort würde
    eine Textausgabe niemand sehen.
    """
    text = (f"Das Python-Paket '{paket}' wird gebraucht, ist aber nicht "
            f"installiert.\n\n"
            f"Bitte einmalig in einem Terminal ausführen:\n\n"
            f"    pip install cryptography argon2-cffi customtkinter\n\n"
            f"(Technischer Fehler: {fehler})")
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror("Ein Paket fehlt", text)
    except Exception:
        print(text)
    sys.exit(1)


def main():
    if sys.version_info < (3, 9):
        print("VP4 braucht Python 3.9 oder neuer. "
              f"Gefunden: {sys.version.split()[0]}")
        sys.exit(1)

    try:
        import cryptography            # noqa: F401
    except ImportError as e:
        _abhaengigkeit_fehlt("cryptography", e)

    try:
        import argon2                  # noqa: F401
    except ImportError as e:
        _abhaengigkeit_fehlt("argon2-cffi", e)

    try:
        import customtkinter           # noqa: F401
    except ImportError as e:
        _abhaengigkeit_fehlt("customtkinter", e)

    import gui
    gui.starten()


if __name__ == "__main__":
    main()
