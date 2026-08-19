#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 Selbsttest für Verschlüsselungs Programm 4.0
=====================================================================
Prüft, ob nach einer Änderung noch alles funktioniert:

    python test_vp4.py

Am Ende steht, wie viele Prüfungen bestanden wurden.

Der Test fasst deine echten Daten NICHT an - Schlüsselspeicher und
empfangene Dateien landen in einem Wegwerf-Ordner, der danach wieder
gelöscht wird. Nur der Oberflächen-Test startet kurz das echte
Fenster und schließt es sofort wieder.

Ohne Fenster testen (z.B. auf einem Server):
    set VP4_TEST_OHNE_GUI=1  &&  python test_vp4.py

Diese Datei gehört nicht ins fertige Programm - die .exe wird nur aus
VP4.py gebaut.
=====================================================================
"""

import os
import queue
import sys
import tempfile
import time
import traceback
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# MUSS vor dem Import von speicher/gui stehen: verhindert, dass ein Testlauf
# die echten Einstellungen überschreibt. Ohne das hat ein Testlauf schon
# einmal den eingestellten Obsidian-Ordner gelöscht, weil der Test das
# Hauptfenster mit erfundenen Standardwerten aufbaut und die dann gespeichert
# wurden.
os.environ["VP4_TESTMODUS"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent))

import speicher
from chat import ChatNetwork
from krypto import (VERFAHREN, SCHLUESSEL_ARTEN, ClassicCiphers, ModernCrypto,
                    Pruefsummen, Signaturen)
from speicher import (FalschesPasswortError, KeyStore, ObsidianSync,
                      passwort_staerke)


# ---------------------------------------------------------------------------
#  Testhilfe
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

# Enthält absichtlich alles, was erfahrungsgemäß Probleme macht:
# Umlaute, ß, Ziffern, Leer- und Sonderzeichen.
TESTTEXT = "Hallo Leon! Grüße aus Straße 5 - äöüß ÄÖÜ 123 & % Ende"


# ---------------------------------------------------------------------------
#  1) Klassische Verfahren
# ---------------------------------------------------------------------------

def test_klassische_verfahren():
    print("\n=== Klassische Verfahren ===")
    C = ClassicCiphers

    # Verfahren, bei denen exakt derselbe Text zurückkommen muss
    verlustfrei = [
        ("Caesar", C.caesar_encrypt, C.caesar_decrypt, "5"),
        ("Vigenere", C.vigenere_encrypt, C.vigenere_decrypt, "SCHLUESSEL"),
        ("XOR", C.xor_encrypt, C.xor_decrypt, "geheim"),
        ("Base64", C.base64_encode, C.base64_decode, ""),
        ("ROT13", C.rot13, C.rot13, ""),
        ("Atbash", C.atbash, C.atbash, ""),
        ("Rail-Fence", C.railfence_encrypt, C.railfence_decrypt, "3"),
    ]
    for name, enc, dec, key in verlustfrei:
        try:
            zurueck = dec(enc(TESTTEXT, key), key)
            R.pruefe(f"{name}: Text kommt unverändert zurück",
                     zurueck == TESTTEXT,
                     f"erwartet: {TESTTEXT!r}\n         bekam:    {zurueck!r}")
        except Exception as e:
            R.fehlschlag(f"{name}: Roundtrip", e)

    # Gegen bekannte Referenzwerte prüfen. Damit ist belegt, dass die
    # Verfahren wirklich richtig rechnen und nicht nur in sich umkehrbar sind.
    referenzen = [
        ("Vigenere", lambda: C.vigenere_encrypt("ATTACKATDAWN", "LEMON"), "LXFOPVEFRNHR"),
        ("ROT13", lambda: C.rot13("Hallo"), "Unyyb"),
        ("Atbash", lambda: C.atbash("ABC"), "ZYX"),
        ("Caesar", lambda: C.caesar_encrypt("abc", "3"), "def"),
        ("Rail-Fence", lambda: C.railfence_encrypt("WEAREDISCOVEREDFLEEATONCE", "3"),
         "WECRLTEERDSOEEFEAOCAIVDEN"),
        ("Morse", lambda: C.morse_encode("SOS"), "... --- ..."),
        # Das kanonische Playfair-Beispiel aus der Wikipedia.
        ("Playfair", lambda: C.playfair_encrypt("hide the gold in the tree stump",
                                                "playfair example"),
         "BMODZBXDNABEKUDMUIXMMOUVIF"),
    ]
    for name, fn, erwartet in referenzen:
        try:
            wert = fn()
            R.pruefe(f"{name} stimmt mit der bekannten Referenz überein",
                     wert == erwartet, f"bekam {wert!r}, erwartet {erwartet!r}")
        except Exception as e:
            R.fehlschlag(f"{name} Referenz", e)

    # Morse und Playfair sind nicht buchstabengetreu umkehrbar (Morse kennt
    # keine Satzzeichenvielfalt, Playfair schiebt X ein) - deshalb hier auf
    # passendem Text prüfen.
    try:
        R.pruefe("Morse: Roundtrip auf Buchstaben und Ziffern",
                 C.morse_decode(C.morse_encode("HALLO LEON 123")) == "HALLO LEON 123")
    except Exception as e:
        R.fehlschlag("Morse Roundtrip", e)
    try:
        zurueck = C.playfair_decrypt(C.playfair_encrypt("TREFFENUMDREI", "GEHEIM"), "GEHEIM")
        R.pruefe("Playfair: Roundtrip liefert den Text wieder",
                 zurueck.replace("X", "") == "TREFFENUMDREI".replace("X", ""),
                 f"bekam {zurueck!r}")
    except Exception as e:
        R.fehlschlag("Playfair Roundtrip", e)

    # Ungültige Schlüssel müssen eine verständliche Meldung geben, nicht abstürzen
    ungueltig = [
        ("Caesar ohne Schlüssel", C.caesar_encrypt, ""),
        ("Caesar mit Buchstaben statt Zahl", C.caesar_encrypt, "abc"),
        ("Vigenere ohne Schlüssel", C.vigenere_encrypt, ""),
        ("Vigenere nur mit Umlauten", C.vigenere_encrypt, "äöü"),
        ("XOR ohne Schlüssel", C.xor_encrypt, ""),
        ("Rail-Fence ohne Schlüssel", C.railfence_encrypt, ""),
        ("Rail-Fence mit 0 Zeilen", C.railfence_encrypt, "0"),
        ("Playfair ohne Schlüsselwort", C.playfair_encrypt, ""),
    ]
    for name, fn, key in ungueltig:
        try:
            fn("Testtext", key)
            R.pruefe(name + " wird abgelehnt", False, "kein Fehler ausgelöst!")
        except ValueError:
            R.pruefe(name + " wird abgelehnt", True)
        except Exception as e:
            R.pruefe(name + " wird abgelehnt", False,
                     f"falsche Fehlerart: {type(e).__name__}: {e}")

    # Kaputte Geheimtexte dürfen nicht mit einem Absturz enden
    for name, fn, key in [("XOR", C.xor_decrypt, "geheim"),
                          ("Base64", C.base64_decode, ""),
                          ("Morse", C.morse_decode, "")]:
        try:
            fn("das ist kein gültiger Geheimtext !!!", key)
            R.pruefe(f"{name}: kaputte Eingabe wird abgefangen", False,
                     "kein Fehler ausgelöst")
        except ValueError:
            R.pruefe(f"{name}: kaputte Eingabe wird abgefangen", True)
        except Exception as e:
            R.pruefe(f"{name}: kaputte Eingabe wird abgefangen", False,
                     f"falsche Fehlerart: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
#  2) Moderne Verfahren
# ---------------------------------------------------------------------------

def test_moderne_verfahren():
    print("\n=== Moderne Verfahren (AES / ChaCha20 / Passwort / RSA) ===")
    M = ModernCrypto

    for name, erzeuge, enc, dec in [
        ("AES-256-GCM", M.generate_aes_key, M.aes_encrypt, M.aes_decrypt),
        ("ChaCha20-Poly1305", M.generate_chacha_key, M.chacha_encrypt, M.chacha_decrypt),
    ]:
        try:
            k = erzeuge()
            geheim = enc(TESTTEXT, k)
            R.pruefe(f"{name}: Text kommt unverändert zurück", dec(geheim, k) == TESTTEXT)
            try:
                dec(geheim, erzeuge())
                R.pruefe(f"{name} lehnt einen falschen Schlüssel ab", False,
                         "hat trotzdem entschlüsselt!")
            except ValueError:
                R.pruefe(f"{name} lehnt einen falschen Schlüssel ab", True)
            # Zweimal derselbe Text muss zwei verschiedene Geheimtexte ergeben,
            # sonst wäre erkennbar, wenn zweimal dasselbe gesendet wurde.
            R.pruefe(f"{name}: gleicher Text ergibt verschiedene Geheimtexte",
                     enc("gleich", k) != enc("gleich", k))
        except Exception as e:
            R.fehlschlag(name, e)

    # Passwort-Verschlüsselung
    try:
        geheim = M.password_encrypt(TESTTEXT, "mein geheimes Passwort")
        R.pruefe("Passwort-Verschlüsselung: Text kommt unverändert zurück",
                 M.password_decrypt(geheim, "mein geheimes Passwort") == TESTTEXT)
        try:
            M.password_decrypt(geheim, "falsches Passwort")
            R.pruefe("Falsches Passwort wird abgelehnt", False, "hat entschlüsselt!")
        except ValueError:
            R.pruefe("Falsches Passwort wird abgelehnt", True)
        R.pruefe("Gleiches Passwort ergibt verschiedene Geheimtexte",
                 M.password_encrypt("x", "pw") != M.password_encrypt("x", "pw"))
        try:
            M.password_decrypt("QUJD", "pw")     # Base64, aber ohne Kennzeichnung
            R.pruefe("Fremder Text wird als solcher erkannt", False, "kein Fehler")
        except ValueError:
            R.pruefe("Fremder Text wird als solcher erkannt", True)
    except Exception as e:
        R.fehlschlag("Passwort-Verschlüsselung", e)

    # RSA
    try:
        privat, oeffentlich = M.generate_rsa_keypair()
        kurz = "Kurzer Text für RSA"
        R.pruefe("RSA-2048: Text kommt unverändert zurück",
                 M.rsa_decrypt(M.rsa_encrypt(kurz, oeffentlich), privat) == kurz)
        try:
            M.rsa_encrypt("x" * 500, oeffentlich)
            R.pruefe("RSA sagt bei zu langem Text verständlich Bescheid", False,
                     "kein Fehler")
        except ValueError as e:
            R.pruefe("RSA sagt bei zu langem Text verständlich Bescheid",
                     "190" in str(e), str(e))
    except Exception as e:
        R.fehlschlag("RSA", e)


# ---------------------------------------------------------------------------
#  3) Signaturen und Prüfsummen
# ---------------------------------------------------------------------------

def test_signaturen():
    print("\n=== Signaturen & Prüfsummen ===")
    try:
        privat, oeffentlich = Signaturen.generate_keypair()
        signatur = Signaturen.sign(TESTTEXT, privat)
        R.pruefe("Ed25519: die eigene Signatur wird anerkannt",
                 Signaturen.verify(TESTTEXT, signatur, oeffentlich) is True)
        R.pruefe("Ed25519: ein verändertes Zeichen fällt auf",
                 Signaturen.verify(TESTTEXT + "!", signatur, oeffentlich) is False)
        _, fremd = Signaturen.generate_keypair()
        R.pruefe("Ed25519: fremder Schlüssel passt nicht",
                 Signaturen.verify(TESTTEXT, signatur, fremd) is False)
    except Exception as e:
        R.fehlschlag("Signaturen", e)

    try:
        R.pruefe("SHA-256 stimmt mit der bekannten Referenz überein",
                 Pruefsummen.berechne("") ==
                 "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        R.pruefe("Ein geändertes Zeichen ergibt eine andere Prüfsumme",
                 Pruefsummen.berechne("Hallo") != Pruefsummen.berechne("Hallo!"))
        R.pruefe("Alle Prüfsummen-Verfahren rechnen",
                 all(Pruefsummen.berechne("x", v) for v in Pruefsummen.VERFAHREN))
    except Exception as e:
        R.fehlschlag("Prüfsummen", e)


# ---------------------------------------------------------------------------
#  4) Schlüsselspeicher
# ---------------------------------------------------------------------------

def test_schluesselspeicher():
    print("\n=== Schlüsselspeicher ===")
    with tempfile.TemporaryDirectory() as ordner:
        pfad = Path(ordner) / "test_schluessel.enc"
        passwort = "MeinMasterPasswort123"
        try:
            sp = KeyStore(pfad)
            sp.create(passwort)
            geheimer_wert = ModernCrypto.generate_aes_key()
            sp.add_key("Testschluessel", "AES", geheimer_wert, "eine Notiz")
            R.pruefe("Schlüssel anlegen", len(sp.list_keys()) == 1)

            try:
                sp.add_key("Testschluessel", "AES", "x")
                R.pruefe("Doppelter Name wird abgelehnt", False, "kein Fehler")
            except ValueError:
                R.pruefe("Doppelter Name wird abgelehnt", True)

            sp.lock()
            R.pruefe("Nach dem Sperren ist der Speicher zu", not sp.is_unlocked())

            try:
                KeyStore(pfad).unlock("FALSCHESPASSWORT")
                R.pruefe("Falsches Master-Passwort wird abgelehnt", False,
                         "wurde trotzdem geöffnet!")
            except FalschesPasswortError:
                R.pruefe("Falsches Master-Passwort wird abgelehnt", True)

            wieder = KeyStore(pfad)
            wieder.unlock(passwort)
            R.pruefe("Richtiges Master-Passwort öffnet wieder",
                     len(wieder.list_keys()) == 1)

            R.pruefe("Die Datei enthält den Schlüssel nicht im Klartext",
                     geheimer_wert.encode("utf-8") not in pfad.read_bytes())

            # Eine veränderte Datei muss auffallen - AES-GCM merkt das selbst.
            roh = bytearray(pfad.read_bytes())
            roh[-1] ^= 0xFF
            manipuliert = Path(ordner) / "manipuliert.enc"
            manipuliert.write_bytes(bytes(roh))
            try:
                KeyStore(manipuliert).unlock(passwort)
                R.pruefe("Eine veränderte Speicherdatei fällt auf", False,
                         "wurde klaglos geöffnet!")
            except Exception:
                R.pruefe("Eine veränderte Speicherdatei fällt auf", True)

            # Passwort ändern - der Inhalt muss erhalten bleiben
            wieder.change_password(passwort, "NeuesPasswort456")
            noch_mal = KeyStore(pfad)
            noch_mal.unlock("NeuesPasswort456")
            R.pruefe("Nach Passwortwechsel ist der Inhalt noch da",
                     len(noch_mal.list_keys()) == 1)
            try:
                KeyStore(pfad).unlock(passwort)
                R.pruefe("Das alte Passwort gilt nicht mehr", False, "ging noch!")
            except FalschesPasswortError:
                R.pruefe("Das alte Passwort gilt nicht mehr", True)

            noch_mal.delete_key("Testschluessel")
            R.pruefe("Schlüssel löschen", len(noch_mal.list_keys()) == 0)
        except Exception as e:
            R.fehlschlag("Schlüsselspeicher", e)
            traceback.print_exc()

    # Gesperrter Speicher darf nichts herausgeben
    with tempfile.TemporaryDirectory() as ordner:
        try:
            sp = KeyStore(Path(ordner) / "x.enc")
            sp.list_keys()
            R.pruefe("Gesperrter Speicher gibt nichts heraus", False, "kein Fehler")
        except Exception:
            R.pruefe("Gesperrter Speicher gibt nichts heraus", True)

    stufen = [passwort_staerke(p)[0] for p in ["a", "abcdefgh", "Abcdefgh1!ngLang"]]
    R.pruefe("Passwortstärke steigt mit Länge und Vielfalt",
             stufen[0] < stufen[-1], f"Stufen: {stufen}")

    # Ein Testlauf darf die echten Einstellungen niemals verändern. Das ist
    # schon einmal schiefgegangen: der Test baut das Hauptfenster mit
    # erfundenen Standardwerten auf, die wurden gespeichert, und der
    # tatsächlich eingestellte Obsidian-Ordner war weg.
    vorher = speicher.CONFIG_FILE.read_bytes() if speicher.CONFIG_FILE.exists() else None
    speicher.save_config({"my_id": "KAPUTT", "obsidian_vault": "weg"})
    nachher = speicher.CONFIG_FILE.read_bytes() if speicher.CONFIG_FILE.exists() else None
    R.pruefe("Ein Testlauf fasst die echten Einstellungen nicht an",
             vorher == nachher,
             "save_config hat trotz VP4_TESTMODUS geschrieben!")


# ---------------------------------------------------------------------------
#  5) Obsidian
# ---------------------------------------------------------------------------

def test_obsidian():
    print("\n=== Obsidian-Verknüpfung ===")
    with tempfile.TemporaryDirectory() as vault:
        try:
            sync = ObsidianSync(vault)
            privat, oeffentlich = ModernCrypto.generate_rsa_keypair()

            schluessel = [
                {"label": "Mein AES", "typ": "AES",
                 "wert": ModernCrypto.generate_aes_key(), "meta": "kurzer Schlüssel"},
                # Der harte Fall: rund 1700 Zeichen mit vielen Zeilenumbrüchen.
                # Genau daran ist der Export früher gescheitert - er hat bei
                # 120 Zeichen abgeschnitten und den Schlüssel unbrauchbar gemacht.
                {"label": "RSA privat", "typ": "RSA-priv",
                 "wert": privat, "meta": "langer Schlüssel"},
                # Ein "|" würde die Markdown-Tabelle zerreißen.
                {"label": "Mit Sonderzeichen", "typ": "Text",
                 "wert": "a|b\\c\nzweite Zeile", "meta": "Notiz mit | Strich"},
            ]

            notiz = Path(sync.export_keys(schluessel))
            R.pruefe("Export legt die Notiz an", notiz.exists())

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
                R.pruefe(f"Roundtrip: {original['label']} kommt vollständig zurück",
                         gelesen.get("wert") == original["wert"],
                         f"{len(original['wert'])} Zeichen rein, "
                         f"{len(gelesen.get('wert', ''))} zurück")
                R.pruefe(f"Roundtrip: Notiz von {original['label']} bleibt erhalten",
                         gelesen.get("meta") == original["meta"])

            # Der wichtigste Test: lässt sich mit dem Schlüssel, der aus
            # Obsidian zurückkam, wirklich noch entschlüsseln?
            geheim = ModernCrypto.rsa_encrypt("Geheime Nachricht", oeffentlich)
            R.pruefe("Der zurückgelesene RSA-Schlüssel funktioniert noch",
                     ModernCrypto.rsa_decrypt(
                         geheim, zurueck["RSA privat"]["wert"]) == "Geheime Nachricht")
        except Exception as e:
            R.fehlschlag("Obsidian", e)
            traceback.print_exc()

    # Notiz aus einer alten Programmversion: abgeschnittene Schlüssel müssen
    # gemeldet werden, statt still kaputt zurückzukommen.
    with tempfile.TemporaryDirectory() as vault:
        try:
            (Path(vault) / ObsidianSync.NOTE_NAME).write_text(
                "| Name | Typ | Wert | Notiz | Erstellt |\n"
                "|---|---|---|---|---|\n"
                "| Alter RSA | RSA-priv | `-----BEGIN PRIVATE KEY----- MIIEvAIBAD...` "
                "| x | 2026-01-01 |\n", encoding="utf-8")
            ObsidianSync(vault).import_keys()
            R.pruefe("Abgeschnittener Schlüssel aus alter Version wird gemeldet",
                     False, "wurde stillschweigend übernommen!")
        except ValueError:
            R.pruefe("Abgeschnittener Schlüssel aus alter Version wird gemeldet", True)
        except Exception as e:
            R.fehlschlag("Warnung bei alter Notiz", e)


# ---------------------------------------------------------------------------
#  6) Chat
# ---------------------------------------------------------------------------

def test_chat():
    print("\n=== Chat zwischen zwei Instanzen ===")

    PORT = 41951          # eigener Port, damit ein laufendes VP4 nicht stört

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
    empfang_vorher = speicher.RECEIVED_DIR
    speicher.RECEIVED_DIR = Path(ordner)      # echte Dateien nicht anfassen

    a = b = None
    try:
        gemeinsam = ModernCrypto.generate_aes_key()
        ereignisse_a, ereignisse_b = queue.Queue(), queue.Queue()

        # A kennt B, hat aber (noch) KEINEN gemeinsamen Schlüssel hinterlegt.
        a = ChatNetwork("AAAA-1111",
                        TestFreunde({"BBBB-2222": {"nickname": "B", "shared_key_b64": None}}),
                        ereignisse_a, chat_port=PORT, broadcast_port=PORT + 1,
                        bind_host="127.0.0.1")
        # B hat den Schlüssel gesetzt und sendet deshalb verschlüsselt.
        b = ChatNetwork("BBBB-2222",
                        TestFreunde({"AAAA-1111": {"nickname": "A", "shared_key_b64": gemeinsam}}),
                        ereignisse_b, chat_port=PORT, broadcast_port=PORT + 1,
                        bind_host="127.0.0.1")

        a.start()
        R.pruefe("Chat-Server startet und meldet sich bereit",
                 warte_auf(ereignisse_a, "server_bereit", 3) is not None)

        b._running = True             # B nur als Gegenstelle, kein zweiter Server
        with b._peers_lock:
            b.peers["AAAA-1111"] = ("127.0.0.1", time.time(), PORT)

        # --- Der Fall, an dem die Verbindung früher gestorben ist ----------
        # B schickt verschlüsselt, A kann es nicht lesen. Früher ist dabei der
        # Empfangs-Thread von A abgestürzt und die tote Verbindung blieb in
        # der Liste stehen - danach ging bis zum Neustart gar nichts mehr.
        b.send_text("AAAA-1111", "Das kann A noch nicht lesen")
        R.pruefe("Nicht entschlüsselbare Nachricht gibt eine Meldung",
                 warte_auf(ereignisse_a, "error") is not None)

        a.friends.get("BBBB-2222")["shared_key_b64"] = gemeinsam
        b.send_text("AAAA-1111", "Und das hier schon - mit Umlauten: äöüß")
        nachricht = warte_auf(ereignisse_a, "message")
        R.pruefe("Die Verbindung überlebt eine unlesbare Nachricht",
                 nachricht is not None, "A empfängt nichts mehr - Verbindung war tot")
        if nachricht:
            R.pruefe("Nachricht kommt unverändert an (auch mit Umlauten)",
                     nachricht["text"] == "Und das hier schon - mit Umlauten: äöüß",
                     f"bekam: {nachricht['text']!r}")
            R.pruefe("Nachricht wurde verschlüsselt übertragen",
                     nachricht["encrypted"] is True)

        # --- Verschlüsselte Datei ------------------------------------------
        quelle = Path(ordner) / "testbild.png"
        quelle.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 400)
        b.send_file("AAAA-1111", str(quelle), "bild")
        datei = warte_auf(ereignisse_a, "file")
        R.pruefe("Verschlüsselte Datei kommt an", datei is not None)
        if datei:
            R.pruefe("Die empfangene Datei ist Byte für Byte identisch",
                     Path(datei["path"]).read_bytes() == quelle.read_bytes())

        b.send_text("AAAA-1111", "Noch eine Nachricht nach der Datei")
        R.pruefe("Nach einer Dateiübertragung geht das Chatten weiter",
                 warte_auf(ereignisse_a, "message") is not None)
    except Exception as e:
        R.fehlschlag("Chat", e)
        traceback.print_exc()
    finally:
        speicher.RECEIVED_DIR = empfang_vorher
        for netz in (a, b):
            if netz is not None:
                try:
                    netz.stop()
                except Exception:
                    pass

    # Die Ports müssen unterhalb des dynamischen Windows-Bereichs liegen.
    # Ab 49152 vergibt Windows Ports selbst an ausgehende Verbindungen -
    # ein fester Server-Port dort oben kann beim Start schon belegt sein.
    import chat as chat_modul
    R.pruefe("Die Chat-Ports liegen unter 49152",
             chat_modul.CHAT_PORT < 49152 and chat_modul.BROADCAST_PORT < 49152,
             f"Ports: {chat_modul.BROADCAST_PORT}, {chat_modul.CHAT_PORT}")


# ---------------------------------------------------------------------------
#  7) Verfahrensliste
# ---------------------------------------------------------------------------

def test_verfahrensliste():
    print("\n=== Verfahrensliste (davon lebt die Auswahl in der Oberfläche) ===")
    R.pruefe(f"Es sind {len(VERFAHREN)} Verfahren eingetragen", len(VERFAHREN) >= 13)

    unvollstaendig = [n for n, i in VERFAHREN.items()
                      if not all(f in i for f in ("enc", "dec", "art", "key", "hinweis"))]
    R.pruefe("Jedes Verfahren hat alle nötigen Angaben",
             not unvollstaendig, f"unvollständig: {unvollstaendig}")

    unbekannt = [n for n, i in VERFAHREN.items() if i["key"] not in SCHLUESSEL_ARTEN]
    R.pruefe("Jedes Verfahren verweist auf eine bekannte Schlüsselart",
             not unbekannt, f"unbekannt: {unbekannt}")

    falsche_art = [n for n, i in VERFAHREN.items() if i["art"] not in ("sicher", "spiel")]
    R.pruefe("Jedes Verfahren ist als 'sicher' oder 'spiel' eingestuft",
             not falsche_art, f"falsch: {falsche_art}")

    # Jedes Verfahren muss über die Liste tatsächlich aufrufbar sein - genau
    # so ruft die Oberfläche es später auf.
    passende_schluessel = {
        "aes": ModernCrypto.generate_aes_key(),
        "chacha": ModernCrypto.generate_chacha_key(),
        "passwort": "Testpasswort",
        "zahl": "3", "wort": "SCHLUESSEL", "keiner": "",
    }
    fehler = []
    for name, info in VERFAHREN.items():
        if info["key"] == "rsa":
            continue                       # braucht zwei verschiedene Schlüssel
        try:
            info["enc"]("Testtext ABC", passende_schluessel[info["key"]])
        except Exception as e:
            fehler.append(f"{name}: {type(e).__name__}: {e}")
    R.pruefe("Jedes Verfahren lässt sich über die Liste aufrufen",
             not fehler, "\n         ".join(fehler))


# ---------------------------------------------------------------------------
#  8) Oberfläche
# ---------------------------------------------------------------------------

def test_oberflaeche():
    print("\n=== Oberfläche ===")
    if os.environ.get("VP4_TEST_OHNE_GUI"):
        print("  (übersprungen, weil VP4_TEST_OHNE_GUI gesetzt ist)")
        return

    fenster = None
    try:
        import customtkinter as ctk
        import gui

        with tempfile.TemporaryDirectory() as ordner:
            # Auf einen Wegwerf-Speicher umbiegen, damit der echte
            # Schlüsselspeicher unangetastet bleibt.
            ks = KeyStore(Path(ordner) / "test.enc")
            ks.create("TestPasswort123")
            ks.add_key("Beispiel", "AES", ModernCrypto.generate_aes_key(), "Notiz")

            config = dict(speicher.STANDARD_EINSTELLUNGEN)
            config["my_id"] = "TEST-0001"
            config["chat_aktiv"] = False        # im Test kein Netzwerk starten

            fenster = gui.VP4App(ks, config)
            R.pruefe("Das Hauptfenster wird erzeugt", fenster is not None)

            # Jede Seite einmal wirklich anzeigen lassen
            namen = []
            for name, _, beschriftung in gui.VP4App.SEITEN:
                fenster._seite_zeigen(name)
                fenster.update()
                namen.append(beschriftung)
            R.pruefe(f"Alle {len(namen)} Seiten bauen fehlerfrei auf "
                     f"({', '.join(namen)})",
                     len(namen) == len(gui.VP4App.SEITEN))

            # Jedes Verfahren einmal in der Auswahl durchschalten - dabei wird
            # der Hinweistext und die Schlüsselzeile neu gesetzt.
            for verfahren in VERFAHREN:
                fenster._verfahren_gewechselt(verfahren)
                fenster.update()
            R.pruefe("Alle Verfahren lassen sich in der Auswahl durchschalten", True)

            # Wirklich einmal verschlüsseln, so wie ein Klick es täte
            fenster.verfahren_wahl.set("AES-256-GCM")
            fenster._verfahren_gewechselt("AES-256-GCM")
            fenster.schluessel_feld.delete("1.0", "end")
            fenster.schluessel_feld.insert("1.0", ModernCrypto.generate_aes_key())
            fenster.eingabe_feld.insert("1.0", TESTTEXT)
            fenster._rechnen(True)
            fenster.update()
            geheim = fenster.ausgabe_feld.get("1.0", "end-1c")
            R.pruefe("Verschlüsseln über die Oberfläche liefert ein Ergebnis",
                     len(geheim) > 0)

            fenster._tauschen()
            fenster._rechnen(False)
            fenster.update()
            R.pruefe("Entschlüsseln über die Oberfläche gibt den Text zurück",
                     fenster.ausgabe_feld.get("1.0", "end-1c") == TESTTEXT)

            # Beide Designs durchschalten
            for modus in ("light", "dark"):
                ctk.set_appearance_mode(modus)
                fenster._treeview_stil()
                fenster.update()
            R.pruefe("Hell und Dunkel lassen sich umschalten", True)

            R.pruefe("Die Schlüsselliste zeigt den vorhandenen Eintrag",
                     len(fenster.schluessel_tabelle.get_children()) == 1)
    except Exception as e:
        R.fehlschlag("Oberfläche", e)
        traceback.print_exc()
    finally:
        if fenster is not None:
            try:
                fenster.network.stop()
                fenster.destroy()
            except Exception:
                pass


# ---------------------------------------------------------------------------
#  Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    print("=" * 64)
    print(" Selbsttest für Verschlüsselungs Programm 4.0")
    print("=" * 64)

    test_klassische_verfahren()
    test_moderne_verfahren()
    test_signaturen()
    test_schluesselspeicher()
    test_obsidian()
    test_chat()
    test_verfahrensliste()
    test_oberflaeche()

    print("\n" + "=" * 64)
    if R.fehler:
        print(f" ERGEBNIS: {R.ok} bestanden, {len(R.fehler)} FEHLGESCHLAGEN")
        print("\n Fehlgeschlagen sind:")
        for name in R.fehler:
            print(f"   - {name}")
        print("=" * 64)
        return 1

    print(f" ERGEBNIS: alle {R.ok} Prüfungen bestanden.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
