#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 Selbsttest für Verschlüsselungs Programm 4.0
=====================================================================
Prüft, ob nach einer Änderung noch alles funktioniert. Einfach
ausführen:

    python test_vp4.py

Am Ende steht, wie viele Prüfungen bestanden wurden. Wenn dort
"alle Prüfungen bestanden" steht, ist alles in Ordnung.

Der Test fasst deine echten Daten NICHT an - der Schlüsselspeicher
wird in einem Wegwerf-Ordner angelegt, der danach wieder gelöscht
wird. Nur der GUI-Test startet kurz das echte Programm (samt
Chat-Netzwerk) und schließt es sofort wieder.

Diese Datei gehört NICHT ins fertige Programm - beim Bauen der .exe
mit PyInstaller wird nur VP4.py verwendet.
=====================================================================
"""

import sys
import os
import tempfile
import traceback
from pathlib import Path

# Damit Umlaute in der Windows-Konsole nicht als "?" erscheinen
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import VP4


# ---------------------------------------------------------------------------
#  Kleine Testhilfe
# ---------------------------------------------------------------------------

class Ergebnis:
    def __init__(self):
        self.ok = 0
        self.fehler = []

    def pruefe(self, name, bedingung, detail=""):
        if bedingung:
            self.ok += 1
            print(f"  [OK]   {name}")
        else:
            self.fehler.append(name)
            print(f"  [FEHL] {name}")
            if detail:
                print(f"         {detail}")

    def fehlschlag(self, name, ausnahme):
        self.fehler.append(name)
        print(f"  [FEHL] {name}")
        print(f"         {type(ausnahme).__name__}: {ausnahme}")


R = Ergebnis()

# Ein Text, der absichtlich alles enthält, was erfahrungsgemäß Probleme macht:
# Umlaute, ß, Ziffern, Leerzeichen, Satz- und Sonderzeichen.
TESTTEXT = "Hallo Leon! Grüße aus Straße 5 - äöüß ÄÖÜ 123 & % Ende"


# ---------------------------------------------------------------------------
#  1) Klassische Chiffren
# ---------------------------------------------------------------------------

def test_klassische_chiffren():
    print("\n=== Klassische Chiffren ===")
    C = VP4.ClassicCiphers

    verfahren = [
        ("Caesar", C.caesar_encrypt, C.caesar_decrypt, "5"),
        ("Vigenere", C.vigenere_encrypt, C.vigenere_decrypt, "SCHLUESSEL"),
        ("XOR", C.xor_encrypt, C.xor_decrypt, "geheim"),
        ("Base64", C.base64_encode, C.base64_decode, ""),
    ]

    for name, enc, dec, key in verfahren:
        try:
            zurueck = dec(enc(TESTTEXT, key), key)
            R.pruefe(
                f"{name}: Text kommt unverändert zurück",
                zurueck == TESTTEXT,
                f"erwartet: {TESTTEXT!r}\n         bekam:    {zurueck!r}",
            )
        except Exception as e:
            R.fehlschlag(f"{name}: Roundtrip", e)

    # Vigenere gegen den bekannten Lehrbuch-Wert prüfen. Wenn das stimmt,
    # ist das Verfahren wirklich korrekt und nicht nur in sich umkehrbar.
    try:
        ergebnis = C.vigenere_encrypt("ATTACKATDAWN", "LEMON")
        R.pruefe(
            "Vigenere stimmt mit der Lehrbuch-Referenz überein",
            ergebnis == "LXFOPVEFRNHR",
            f"bekam: {ergebnis!r}, erwartet: LXFOPVEFRNHR",
        )
    except Exception as e:
        R.fehlschlag("Vigenere Lehrbuch-Referenz", e)

    # Leere oder unsinnige Schlüssel müssen eine verständliche Meldung geben,
    # nicht abstürzen.
    ungueltig = [
        ("Caesar ohne Schlüssel", C.caesar_encrypt, ""),
        ("Caesar mit Buchstaben statt Zahl", C.caesar_encrypt, "abc"),
        ("Vigenere ohne Schlüssel", C.vigenere_encrypt, ""),
        ("Vigenere nur mit Umlauten", C.vigenere_encrypt, "äöü"),
        ("XOR ohne Schlüssel", C.xor_encrypt, ""),
    ]
    for name, fn, key in ungueltig:
        try:
            fn("Test", key)
            R.pruefe(name + " wird abgelehnt", False, "kein Fehler ausgelöst!")
        except ValueError:
            R.pruefe(name + " wird abgelehnt", True)
        except Exception as e:
            R.pruefe(name + " wird abgelehnt", False,
                     f"falsche Fehlerart: {type(e).__name__}: {e}")

    # Kaputte Geheimtexte dürfen nicht mit einem Absturz enden.
    for name, fn in [("XOR", C.xor_decrypt), ("Base64", C.base64_decode)]:
        try:
            fn("das ist kein gültiger Geheimtext !!!", "geheim")
            R.pruefe(f"{name}: kaputter Geheimtext wird abgefangen", False,
                     "kein Fehler ausgelöst")
        except ValueError:
            R.pruefe(f"{name}: kaputter Geheimtext wird abgefangen", True)
        except Exception as e:
            R.pruefe(f"{name}: kaputter Geheimtext wird abgefangen", False,
                     f"falsche Fehlerart: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
#  2) Moderne Kryptografie
# ---------------------------------------------------------------------------

def test_moderne_krypto():
    print("\n=== Moderne Kryptografie (AES / RSA) ===")
    M = VP4.ModernCrypto

    try:
        schluessel = M.generate_aes_key()
        geheim = M.aes_encrypt(TESTTEXT, schluessel)
        R.pruefe("AES-256-GCM: Text kommt unverändert zurück",
                 M.aes_decrypt(geheim, schluessel) == TESTTEXT)

        try:
            M.aes_decrypt(geheim, M.generate_aes_key())
            R.pruefe("AES lehnt einen falschen Schlüssel ab", False,
                     "hat mit falschem Schlüssel entschlüsselt!")
        except Exception:
            R.pruefe("AES lehnt einen falschen Schlüssel ab", True)

        # Zweimal denselben Text zu verschlüsseln muss zwei verschiedene
        # Geheimtexte ergeben - sonst könnte ein Mitleser erkennen, wenn
        # zweimal dasselbe gesendet wurde.
        R.pruefe("AES erzeugt bei gleichem Text zwei verschiedene Geheimtexte",
                 M.aes_encrypt("gleich", schluessel) != M.aes_encrypt("gleich", schluessel))
    except Exception as e:
        R.fehlschlag("AES", e)

    try:
        privat, oeffentlich = M.generate_rsa_keypair()
        kurz = "Kurzer Text für RSA"
        R.pruefe("RSA-2048: Text kommt unverändert zurück",
                 M.rsa_decrypt(M.rsa_encrypt(kurz, oeffentlich), privat) == kurz)
    except Exception as e:
        R.fehlschlag("RSA", e)


# ---------------------------------------------------------------------------
#  3) Schlüsselspeicher
# ---------------------------------------------------------------------------

def test_schluesselspeicher():
    print("\n=== Schlüsselspeicher ===")
    with tempfile.TemporaryDirectory() as ordner:
        pfad = Path(ordner) / "test_schluessel.enc"
        passwort = "MeinMasterPasswort123"
        try:
            speicher = VP4.KeyStore(pfad)
            speicher.create(passwort)
            geheimer_wert = VP4.ModernCrypto.generate_aes_key()
            speicher.add_key("Testschluessel", "AES", geheimer_wert, "eine Notiz")
            R.pruefe("Schlüssel anlegen", len(speicher.list_keys()) == 1)

            speicher.lock()
            R.pruefe("Nach dem Sperren ist der Speicher zu", not speicher.is_unlocked())

            try:
                VP4.KeyStore(pfad).unlock("FALSCHESPASSWORT")
                R.pruefe("Falsches Masterpasswort wird abgelehnt", False,
                         "wurde trotzdem geöffnet!")
            except Exception:
                R.pruefe("Falsches Masterpasswort wird abgelehnt", True)

            wieder = VP4.KeyStore(pfad)
            wieder.unlock(passwort)
            R.pruefe("Richtiges Masterpasswort öffnet wieder",
                     len(wieder.list_keys()) == 1)

            # Der Schlüssel darf in der Datei nirgends im Klartext stehen.
            R.pruefe("Die Speicherdatei enthält keinen Klartext-Schlüssel",
                     geheimer_wert.encode("utf-8") not in pfad.read_bytes())
        except Exception as e:
            R.fehlschlag("Schlüsselspeicher", e)


# ---------------------------------------------------------------------------
#  4) Obsidian-Verknüpfung
# ---------------------------------------------------------------------------

def test_obsidian():
    print("\n=== Obsidian-Verknüpfung ===")
    with tempfile.TemporaryDirectory() as vault:
        try:
            sync = VP4.ObsidianSync(vault)
            aes = VP4.ModernCrypto.generate_aes_key()
            privat, oeffentlich = VP4.ModernCrypto.generate_rsa_keypair()

            schluessel = [
                {"label": "Mein AES", "typ": "AES",
                 "wert": aes, "meta": "kurzer Schlüssel"},
                # Der harte Fall: ein RSA-Schlüssel ist rund 1700 Zeichen lang
                # und voller Zeilenumbrüche. Genau daran ist der Export früher
                # gescheitert - er hat bei 120 Zeichen abgeschnitten.
                {"label": "RSA privat", "typ": "RSA-priv",
                 "wert": privat, "meta": "langer Schlüssel"},
                # Ein "|" würde die Markdown-Tabelle zerreißen.
                {"label": "Mit Sonderzeichen", "typ": "Text",
                 "wert": "a|b\\c\nzweite Zeile", "meta": "Notiz mit | Strich"},
            ]

            notiz = Path(sync.export_keys(schluessel))
            R.pruefe("Export legt die Notiz an", notiz.exists())

            # Handgeschriebenen Text anhängen und erneut exportieren -
            # der eigene Text muss erhalten bleiben.
            with open(notiz, "a", encoding="utf-8") as f:
                f.write("\n\nDas hier habe ich selbst geschrieben.\n")
            sync.export_keys(schluessel)
            R.pruefe("Eigener Notiztext überlebt einen erneuten Export",
                     "Das hier habe ich selbst geschrieben."
                     in notiz.read_text(encoding="utf-8"))

            zurueck = {k["label"]: k for k in sync.import_keys()}
            R.pruefe("Import liest alle Schlüssel wieder ein",
                     len(zurueck) == len(schluessel),
                     f"erwartet {len(schluessel)}, bekam {len(zurueck)}")

            for original in schluessel:
                gelesen = zurueck.get(original["label"], {})
                R.pruefe(
                    f"Obsidian-Roundtrip: {original['label']} kommt vollständig zurück",
                    gelesen.get("wert") == original["wert"],
                    f"{len(original['wert'])} Zeichen rein, "
                    f"{len(gelesen.get('wert', ''))} Zeichen zurück",
                )
                R.pruefe(
                    f"Obsidian-Roundtrip: Notiz von {original['label']} bleibt erhalten",
                    gelesen.get("meta") == original["meta"],
                    f"erwartet {original['meta']!r}, bekam {gelesen.get('meta')!r}",
                )

            # Der wichtigste Test überhaupt: lässt sich mit dem Schlüssel,
            # der aus Obsidian zurückkam, wirklich noch entschlüsseln?
            geheim = VP4.ModernCrypto.rsa_encrypt("Geheime Nachricht", oeffentlich)
            R.pruefe("Der aus Obsidian zurückgelesene RSA-Schlüssel funktioniert noch",
                     VP4.ModernCrypto.rsa_decrypt(
                         geheim, zurueck["RSA privat"]["wert"]) == "Geheime Nachricht")
        except Exception as e:
            R.fehlschlag("Obsidian", e)

    # Eine Notiz aus einer alten Programmversion enthält abgeschnittene
    # Schlüssel. Das muss deutlich gemeldet werden, statt still einen
    # kaputten Schlüssel zurückzugeben.
    with tempfile.TemporaryDirectory() as vault:
        try:
            alte_notiz = Path(vault) / VP4.ObsidianSync.NOTE_NAME
            alte_notiz.write_text(
                "| Name | Typ | Wert | Notiz | Erstellt |\n"
                "|---|---|---|---|---|\n"
                "| Alter RSA | RSA-priv | `-----BEGIN PRIVATE KEY----- MIIEvAIBAD...` "
                "| x | 2026-01-01 |\n",
                encoding="utf-8",
            )
            VP4.ObsidianSync(vault).import_keys()
            R.pruefe("Abgeschnittener Schlüssel aus alter Version wird gemeldet",
                     False, "wurde stillschweigend übernommen!")
        except ValueError:
            R.pruefe("Abgeschnittener Schlüssel aus alter Version wird gemeldet", True)
        except Exception as e:
            R.fehlschlag("Warnung bei alter Notiz", e)


# ---------------------------------------------------------------------------
#  5) Chat - zwei Instanzen reden wirklich miteinander
# ---------------------------------------------------------------------------

def test_chat():
    print("\n=== Chat zwischen zwei Instanzen ===")

    import queue
    import time

    PORT = 51951          # eigener Port, damit ein laufendes VP4 nicht stört

    class TestFreunde:
        """Ersetzt FriendsStore, damit der Test nichts auf die Platte schreibt."""
        def __init__(self, eintraege):
            self._d = dict(eintraege)

        def __contains__(self, fid):
            return fid in self._d

        def get(self, fid):
            return self._d.get(fid)

        def all(self):
            return dict(self._d)

    def warte_auf(q, art, sekunden=5.0):
        ende = time.time() + sekunden
        while time.time() < ende:
            try:
                typ, daten = q.get(timeout=0.2)
                if typ == art:
                    return daten
            except queue.Empty:
                pass
        return None

    ordner = tempfile.mkdtemp()
    empfangs_ordner_vorher = VP4.RECEIVED_DIR
    VP4.RECEIVED_DIR = Path(ordner)     # echte empfangene Dateien nicht anfassen

    a = b = None
    try:
        gemeinsam = VP4.ModernCrypto.generate_aes_key()
        ereignisse_a, ereignisse_b = queue.Queue(), queue.Queue()

        # A kennt B, hat aber (noch) KEINEN gemeinsamen Schlüssel hinterlegt.
        a = VP4.ChatNetwork(
            "AAAA-1111",
            TestFreunde({"BBBB-2222": {"nickname": "B", "shared_key_b64": None}}),
            ereignisse_a, chat_port=PORT, broadcast_port=PORT + 1,
            bind_host="127.0.0.1")
        # B hat den Schlüssel gesetzt und sendet deshalb verschlüsselt.
        b = VP4.ChatNetwork(
            "BBBB-2222",
            TestFreunde({"AAAA-1111": {"nickname": "A", "shared_key_b64": gemeinsam}}),
            ereignisse_b, chat_port=PORT, broadcast_port=PORT + 1,
            bind_host="127.0.0.1")

        a.start()                       # A ist der Server
        time.sleep(0.5)
        b._running = True               # B nur als Gegenstelle, kein zweiter Server
        with b._peers_lock:
            b.peers["AAAA-1111"] = ("127.0.0.1", time.time())

        # --- Der Fall, an dem die Verbindung früher gestorben ist ----------
        # B schickt verschlüsselt, A kann es nicht lesen. Früher ist dabei
        # der Empfangs-Thread von A abgestürzt, und danach ging gar nichts
        # mehr - bis zum Neustart des Programms.
        b.send_text("AAAA-1111", "Das kann A noch nicht lesen")
        R.pruefe("Nicht entschlüsselbare Nachricht gibt eine Meldung",
                 warte_auf(ereignisse_a, "error") is not None)

        # Jetzt hat A denselben Schlüssel - die Verbindung muss noch stehen.
        a.friends.get("BBBB-2222")["shared_key_b64"] = gemeinsam
        b.send_text("AAAA-1111", "Und das hier schon - mit Umlauten: äöüß")
        nachricht = warte_auf(ereignisse_a, "message")
        R.pruefe("Die Verbindung überlebt eine unlesbare Nachricht",
                 nachricht is not None,
                 "A empfängt nichts mehr - die Verbindung war tot")
        if nachricht:
            R.pruefe("Nachricht kommt unverändert an (auch mit Umlauten)",
                     nachricht["text"] == "Und das hier schon - mit Umlauten: äöüß",
                     f"bekam: {nachricht['text']!r}")
            R.pruefe("Nachricht wurde verschlüsselt übertragen",
                     nachricht["encrypted"] is True)

        # --- Verschlüsselte Datei übertragen -------------------------------
        quelle = Path(ordner) / "testbild.png"
        quelle.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 400)
        b.send_file("AAAA-1111", str(quelle), "bild")
        datei = warte_auf(ereignisse_a, "file")
        R.pruefe("Verschlüsselte Datei kommt an", datei is not None)
        if datei:
            R.pruefe("Die empfangene Datei ist Byte für Byte identisch",
                     Path(datei["path"]).read_bytes() == quelle.read_bytes())

        # --- Läuft die Verbindung nach der Datei weiter? -------------------
        b.send_text("AAAA-1111", "Noch eine Nachricht nach der Datei")
        R.pruefe("Nach einer Dateiübertragung geht das Chatten weiter",
                 warte_auf(ereignisse_a, "message") is not None)
    except Exception as e:
        R.fehlschlag("Chat", e)
        traceback.print_exc()
    finally:
        VP4.RECEIVED_DIR = empfangs_ordner_vorher
        for netz in (a, b):
            if netz is not None:
                try:
                    netz.stop()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
#  6) Programmfenster - baut die GUI fehlerfrei auf?
# ---------------------------------------------------------------------------

def test_gui():
    print("\n=== Programmfenster ===")
    if os.environ.get("VP4_TEST_OHNE_GUI"):
        print("  (übersprungen, weil VP4_TEST_OHNE_GUI gesetzt ist)")
        return

    fenster = None
    try:
        fenster = VP4.App()
        R.pruefe("Fenster wird erzeugt", fenster is not None)

        tableiste = None
        for kind in fenster.winfo_children():
            if kind.winfo_class() == "TNotebook":
                tableiste = kind
                break

        if tableiste is None:
            R.pruefe("Tab-Leiste gefunden", False, "kein TNotebook im Fenster")
        else:
            namen = []
            for tab in tableiste.tabs():
                namen.append(tableiste.tab(tab, "text"))
                tableiste.select(tab)
                fenster.update()      # wirklich zeichnen lassen
            R.pruefe(f"Alle Tabs bauen fehlerfrei auf ({', '.join(namen)})",
                     len(namen) == 5, f"gefunden: {namen}")

        R.pruefe("Eine eigene Chat-ID ist vorhanden",
                 bool(fenster.my_id) and len(fenster.my_id) >= 4,
                 f"ID: {fenster.my_id!r}")
    except Exception as e:
        R.fehlschlag("Programmfenster", e)
        traceback.print_exc()
    finally:
        if fenster is not None:
            try:
                fenster._on_close()     # stoppt auch das Chat-Netzwerk
            except Exception:
                pass


# ---------------------------------------------------------------------------
#  Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    print("=" * 62)
    print(" Selbsttest für Verschlüsselungs Programm 4.0")
    print("=" * 62)

    if not VP4._CRYPTO_OK:
        print("\nFEHLER: Das Paket 'cryptography' fehlt.")
        print("Bitte einmalig ausführen:  pip install cryptography")
        return 1

    test_klassische_chiffren()
    test_moderne_krypto()
    test_schluesselspeicher()
    test_obsidian()
    test_chat()
    test_gui()

    print("\n" + "=" * 62)
    if R.fehler:
        print(f" ERGEBNIS: {R.ok} bestanden, {len(R.fehler)} FEHLGESCHLAGEN")
        print("\n Fehlgeschlagen sind:")
        for name in R.fehler:
            print(f"   - {name}")
        print("=" * 62)
        return 1

    print(f" ERGEBNIS: alle {R.ok} Prüfungen bestanden.")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
