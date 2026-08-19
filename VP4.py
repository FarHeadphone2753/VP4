#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 Verschlüsselungs Programm 4.0  (VP4)
=====================================================================
Ein eigenständiges Desktop-Programm für Windows/macOS/Linux mit vier
Funktionen:

  1) Ver-/Entschlüsseln von Texten mit mehreren Verfahren
     (Caesar, Vigenère, XOR, Base64, AES-256, RSA-2048)
  2) Ein lokaler, passwortgeschützter Schlüsselspeicher, in dem eigene
     Schlüssel gespeichert und verwaltet werden können
  3) Eine Verknüpfung mit Obsidian: die gespeicherten Schlüssel können
     in eine Notiz im eigenen Obsidian-Vault exportiert (und von dort
     wieder importiert) werden
  4) Ein einfacher LAN-Chat: Beim ersten Start bekommt jede Installation
     eine eigene ID. Über diese ID können Freunde (im selben WLAN)
     hinzugefügt werden. Danach kann man chatten sowie Bilder/Videos
     schicken - alles läuft direkt über das lokale Netzwerk (WLAN),
     ganz ohne Internet, ohne Server und ohne Claude/KI.

WICHTIG - HINWEISE ZUR SICHERHEIT
----------------------------------
 - Dies ist ein privates Hobby-Tool, kein geprüftes Sicherheitsprodukt.
   Für hochsensible Daten (Bankdaten, echte Passwörter für wichtige
   Accounts o.ä.) nicht als einzige Absicherung verwenden.
 - Wenn du Schlüssel nach Obsidian exportierst, landen sie im Klartext
   in einer Markdown-Datei in deinem Vault. Wenn dieser Vault z.B. über
   Obsidian Sync, iCloud, Dropbox oder Git synchronisiert wird, werden
   die Schlüssel mit-synchronisiert. Nur exportieren, wenn du dem
   Speicherort vertraust.
 - Der Chat verschlüsselt nur dann, wenn für den jeweiligen Freund ein
   gemeinsamer Schlüssel hinterlegt wurde (siehe Tab "Chat" -> Schlüssel
   setzen). Ohne gemeinsamen Schlüssel werden Nachrichten/Dateien
   unverschlüsselt im lokalen WLAN übertragen (das steht auch in der App).
 - Eingehende Chat-Verbindungen werden nur von IDs akzeptiert, die man
   vorher selbst als Freund hinzugefügt hat.

VORAUSSETZUNGEN ZUM AUSFÜHREN
------------------------------
 - Python 3.9 oder neuer (mit Tkinter, ist bei den meisten
   Python-Installationen unter Windows automatisch dabei)
 - Einmalig installieren:      pip install cryptography
 - Starten:                    python VP4.py

DARAUS EINE .EXE MACHEN (damit Freunde kein Python brauchen)
--------------------------------------------------------------
 1) pip install pyinstaller
 2) pyinstaller --onefile --noconsole --name "VP4" VP4.py
 3) Die fertige .exe liegt danach im Ordner "dist" und kann einfach
    verschickt und doppelgeklickt werden - kein Python, kein pip,
    keine Installation nötig.

Alles in dieser Datei läuft rein lokal auf dem eigenen Rechner bzw. im
eigenen WLAN. Es werden keinerlei Daten an das Internet, an Anthropic
oder an Claude geschickt - das Programm braucht dafür keine
KI/Internetverbindung.
=====================================================================
"""

import sys
import os
import json
import base64
import struct
import socket
import threading
import time
import uuid
import queue
import string
import secrets
import random
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Abhängigkeit prüfen: das Paket "cryptography" wird für AES/RSA gebraucht.
# ---------------------------------------------------------------------------
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
    _CRYPTO_OK = True
    _CRYPTO_IMPORT_ERROR = None
except ImportError as _e:
    _CRYPTO_OK = False
    _CRYPTO_IMPORT_ERROR = str(_e)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext


# =============================================================================
#  Pfade / lokale Daten
# =============================================================================

def _base_dir() -> Path:
    """Ordner, in dem die App liegt (funktioniert auch als PyInstaller-.exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
DATA_DIR = BASE_DIR / "vp4_daten"
DATA_DIR.mkdir(exist_ok=True)

KEYSTORE_FILE = DATA_DIR / "schluessel.enc"
CONFIG_FILE = DATA_DIR / "konfig.json"
FRIENDS_FILE = DATA_DIR / "freunde.json"
RECEIVED_DIR = DATA_DIR / "empfangen"
RECEIVED_DIR.mkdir(exist_ok=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def load_config() -> dict:
    cfg = load_json(CONFIG_FILE, {})
    changed = False
    if "my_id" not in cfg:
        cfg["my_id"] = generate_id()
        changed = True
    if "nickname" not in cfg:
        cfg["nickname"] = ""
        changed = True
    if "obsidian_vault" not in cfg:
        cfg["obsidian_vault"] = ""
        changed = True
    if changed:
        save_json(CONFIG_FILE, cfg)
    return cfg


def generate_id() -> str:
    """Kurze, gut lesbare ID (ohne verwechselbare Zeichen wie 0/O, 1/I/l)."""
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "-".join("".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(2))


# =============================================================================
#  Klassische Chiffren (Caesar, Vigenère, XOR, Base64)
# =============================================================================

class ClassicCiphers:

    @staticmethod
    def caesar(text: str, shift: int) -> str:
        shift %= 26
        out = []
        for ch in text:
            if "a" <= ch <= "z":
                out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
            elif "A" <= ch <= "Z":
                out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
            else:
                out.append(ch)
        return "".join(out)

    @staticmethod
    def caesar_encrypt(text: str, key: str) -> str:
        return ClassicCiphers.caesar(text, ClassicCiphers._caesar_key_to_int(key))

    @staticmethod
    def caesar_decrypt(text: str, key: str) -> str:
        return ClassicCiphers.caesar(text, -ClassicCiphers._caesar_key_to_int(key))

    @staticmethod
    def _caesar_key_to_int(key: str) -> int:
        key = (key or "").strip()
        if not key:
            raise ValueError("Bitte eine Verschiebung (Zahl, z.B. 3) angeben.")
        try:
            return int(key)
        except ValueError:
            raise ValueError("Der Caesar-Schlüssel muss eine ganze Zahl sein (z.B. 3).")

    @staticmethod
    def vigenere(text: str, key: str, decrypt: bool) -> str:
        # Nur A-Z/a-z. Umlaute (ä/ö/ü/ß) und andere Sonderzeichen haben im
        # 26-Buchstaben-Alphabet keinen Platz und bleiben deshalb - genau wie
        # bei Caesar - unverändert stehen. Wichtig: ch.isalpha() wäre hier
        # falsch, denn Python zählt auch "ä" als Buchstabe. Die Rechnung
        # darunter ist aber reines ASCII, wodurch Umlaute unwiederbringlich
        # in den a-z-Bereich gequetscht würden (aus "äöüß" wurde "btzw").
        key = "".join(ch for ch in (key or "") if "a" <= ch <= "z" or "A" <= ch <= "Z")
        if not key:
            raise ValueError("Bitte ein Schlüsselwort angeben (nur die Buchstaben A-Z).")
        key_upper = key.upper()
        out = []
        ki = 0
        for ch in text:
            if "a" <= ch <= "z" or "A" <= ch <= "Z":
                shift = ord(key_upper[ki % len(key_upper)]) - 65
                if decrypt:
                    shift = -shift
                base = 97 if ch.islower() else 65
                out.append(chr((ord(ch) - base + shift) % 26 + base))
                ki += 1
            else:
                out.append(ch)
        return "".join(out)

    @staticmethod
    def vigenere_encrypt(text: str, key: str) -> str:
        return ClassicCiphers.vigenere(text, key, decrypt=False)

    @staticmethod
    def vigenere_decrypt(text: str, key: str) -> str:
        return ClassicCiphers.vigenere(text, key, decrypt=True)

    @staticmethod
    def xor_encrypt(text: str, key: str) -> str:
        if not key:
            raise ValueError("Bitte einen Schlüssel-Text angeben.")
        data = text.encode("utf-8")
        kb = key.encode("utf-8")
        result = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))
        return base64.b64encode(result).decode("ascii")

    @staticmethod
    def xor_decrypt(text: str, key: str) -> str:
        if not key:
            raise ValueError("Bitte einen Schlüssel-Text angeben.")
        try:
            data = base64.b64decode(text)
        except Exception:
            raise ValueError("Das ist kein gültiger XOR-Geheimtext (erwartet Base64).")
        kb = key.encode("utf-8")
        result = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))
        try:
            return result.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Falscher Schlüssel oder beschädigter Text.")

    @staticmethod
    def base64_encode(text: str, key: str = "") -> str:
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def base64_decode(text: str, key: str = "") -> str:
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            raise ValueError("Das ist kein gültiger Base64-Text.")


# =============================================================================
#  Moderne Kryptografie (AES-256-GCM, RSA-2048)
# =============================================================================

class ModernCrypto:

    @staticmethod
    def derive_fernet_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390_000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    # ---- AES-256-GCM ----
    @staticmethod
    def generate_aes_key() -> str:
        return base64.b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")

    @staticmethod
    def aes_encrypt(plaintext: str, key_b64: str) -> str:
        key = ModernCrypto._aes_key_bytes(key_b64)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("ascii")

    @staticmethod
    def aes_decrypt(ciphertext_b64: str, key_b64: str) -> str:
        key = ModernCrypto._aes_key_bytes(key_b64)
        try:
            raw = base64.b64decode(ciphertext_b64)
            nonce, ct = raw[:12], raw[12:]
            pt = AESGCM(key).decrypt(nonce, ct, None)
            return pt.decode("utf-8")
        except Exception:
            raise ValueError("Entschlüsseln fehlgeschlagen: falscher Schlüssel oder beschädigte Daten.")

    @staticmethod
    def _aes_key_bytes(key_b64: str) -> bytes:
        try:
            key = base64.b64decode((key_b64 or "").strip())
        except Exception:
            raise ValueError("Ungültiger AES-Schlüssel (erwartet Base64, z.B. per 'Schlüssel generieren').")
        if len(key) not in (16, 24, 32):
            raise ValueError("Ungültige AES-Schlüssellänge.")
        return key

    @staticmethod
    def aes_encrypt_bytes(data: bytes, key: bytes) -> bytes:
        nonce = os.urandom(12)
        ct = AESGCM(key).encrypt(nonce, data, None)
        return nonce + ct

    @staticmethod
    def aes_decrypt_bytes(data: bytes, key: bytes) -> bytes:
        nonce, ct = data[:12], data[12:]
        return AESGCM(key).decrypt(nonce, ct, None)

    # ---- RSA-2048 ----
    @staticmethod
    def generate_rsa_keypair():
        priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pub = priv.public_key()
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")
        pub_pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        return priv_pem, pub_pem

    @staticmethod
    def rsa_encrypt(plaintext: str, pub_pem: str) -> str:
        try:
            pub = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
        except Exception:
            raise ValueError("Ungültiger RSA Public Key.")
        try:
            ct = pub.encrypt(
                plaintext.encode("utf-8"),
                asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                                   algorithm=hashes.SHA256(), label=None),
            )
        except ValueError:
            raise ValueError("Text zu lang für RSA (max. ca. 190 Zeichen). Für längere Texte AES-256 nutzen.")
        return base64.b64encode(ct).decode("ascii")

    @staticmethod
    def rsa_decrypt(ciphertext_b64: str, priv_pem: str) -> str:
        try:
            priv = serialization.load_pem_private_key(priv_pem.encode("utf-8"), password=None)
        except Exception:
            raise ValueError("Ungültiger RSA Private Key.")
        try:
            raw = base64.b64decode(ciphertext_b64)
            pt = priv.decrypt(
                raw,
                asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                                   algorithm=hashes.SHA256(), label=None),
            )
            return pt.decode("utf-8")
        except Exception:
            raise ValueError("Entschlüsseln fehlgeschlagen: falscher Schlüssel oder beschädigte Daten.")


# =============================================================================
#  Lokaler, passwortgeschützter Schlüsselspeicher
# =============================================================================

class KeyStoreLockedError(Exception):
    pass


class KeyStore:
    """Speichert Schlüssel verschlüsselt (mit Master-Passwort) in einer Datei."""

    def __init__(self, path: Path):
        self.path = path
        self._fernet = None
        self._data = {"keys": []}  # Liste von Dicts: label, typ, wert, meta, erstellt

    def exists(self) -> bool:
        return self.path.exists()

    def is_unlocked(self) -> bool:
        return self._fernet is not None

    def create(self, master_password: str):
        salt = os.urandom(16)
        self._fernet = Fernet(ModernCrypto.derive_fernet_key(master_password, salt))
        self._data = {"keys": []}
        self._save(salt)

    def unlock(self, master_password: str):
        raw = self.path.read_bytes()
        salt, token = raw[:16], raw[16:]
        fernet = Fernet(ModernCrypto.derive_fernet_key(master_password, salt))
        try:
            plain = fernet.decrypt(token)
        except InvalidToken:
            raise ValueError("Falsches Master-Passwort.")
        self._fernet = fernet
        self._salt = salt
        self._data = json.loads(plain.decode("utf-8"))

    def lock(self):
        self._fernet = None
        self._data = {"keys": []}

    def _save(self, salt: bytes = None):
        if salt is None:
            salt = self._salt
        else:
            self._salt = salt
        token = self._fernet.encrypt(json.dumps(self._data, ensure_ascii=False).encode("utf-8"))
        tmp = self.path.with_suffix(".tmp")
        tmp.write_bytes(salt + token)
        tmp.replace(self.path)

    def _require_unlocked(self):
        if not self.is_unlocked():
            raise KeyStoreLockedError("Schlüsselspeicher ist gesperrt.")

    def list_keys(self):
        self._require_unlocked()
        return list(self._data["keys"])

    def get_key(self, label: str):
        self._require_unlocked()
        for k in self._data["keys"]:
            if k["label"] == label:
                return k
        return None

    def add_key(self, label: str, typ: str, value, meta: str = ""):
        self._require_unlocked()
        if any(k["label"] == label for k in self._data["keys"]):
            raise ValueError(f"Es gibt bereits einen Schlüssel mit dem Namen '{label}'.")
        self._data["keys"].append({
            "label": label,
            "typ": typ,
            "wert": value,
            "meta": meta,
            "erstellt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._save()

    def delete_key(self, label: str):
        self._require_unlocked()
        self._data["keys"] = [k for k in self._data["keys"] if k["label"] != label]
        self._save()

    def replace_all(self, keys: list):
        """Wird beim Import aus Obsidian genutzt (führt zusammen, überschreibt bei gleichem Label)."""
        self._require_unlocked()
        by_label = {k["label"]: k for k in self._data["keys"]}
        for k in keys:
            by_label[k["label"]] = k
        self._data["keys"] = list(by_label.values())
        self._save()


# =============================================================================
#  Obsidian-Verknüpfung
# =============================================================================

class ObsidianSync:
    """Exportiert/importiert die gespeicherten Schlüssel als Markdown-Notiz
    in einem beliebigen Obsidian-Vault-Ordner (frei wählbar, damit auch
    Freunde mit ihrem eigenen Vault das Programm nutzen können)."""

    NOTE_NAME = "VP4 Schluessel.md"
    START_MARK = "<!-- VP4:START (automatisch erzeugt - nicht von Hand bearbeiten) -->"
    END_MARK = "<!-- VP4:END -->"

    def __init__(self, vault_path: str):
        if not vault_path:
            raise ValueError("Es ist noch kein Obsidian-Vault-Ordner eingestellt.")
        self.vault_path = Path(vault_path)
        if not self.vault_path.is_dir():
            raise ValueError(f"Der Ordner '{vault_path}' existiert nicht.")

    @property
    def note_path(self) -> Path:
        return self.vault_path / self.NOTE_NAME

    @staticmethod
    def _wert_kodieren(wert) -> str:
        """Macht aus einem Schlüssel einen einzeiligen, tabellensicheren Text.

        Eine Zelle in einer Markdown-Tabelle darf weder einen Zeilenumbruch
        noch ein "|" enthalten - beides würde die Tabelle zerreißen. Deshalb
        wird beides umkehrbar ersetzt, und der Backslash selbst gleich mit,
        damit die Rückwandlung eindeutig bleibt.

        Gekürzt wird hier bewusst NICHT: ein RSA-Schlüssel ist im PEM-Format
        rund 1700 Zeichen lang und enthält knapp 30 Zeilenumbrüche. Früher
        wurde er auf 120 Zeichen abgeschnitten - der Export sah ordentlich
        aus, aber der Schlüssel war beim Zurücklesen unbrauchbar, und damit
        auch alles, was mit ihm verschlüsselt wurde.
        """
        return (str(wert)
                .replace("\\", "\\\\")
                .replace("\r\n", "\\n")
                .replace("\n", "\\n")
                .replace("\r", "\\n")
                .replace("|", "\\|"))

    @staticmethod
    def _zeile_aufteilen(zeile: str) -> list:
        """Teilt eine Zeile der Markdown-Tabelle an den echten Trennstrichen.

        Ein "|", das zum Inhalt gehört, steht als "\\|" in der Zeile und ist
        kein Spaltentrenner. Ein einfaches split("|") würde die Zeile an
        dieser Stelle fälschlich auseinanderreißen.
        """
        spalten = []
        aktuell = []
        i = 0
        while i < len(zeile):
            ch = zeile[i]
            if ch == "\\" and i + 1 < len(zeile):
                # Escape-Sequenz unangetastet übernehmen - das Dekodieren
                # passiert später in _wert_dekodieren().
                aktuell.append(ch)
                aktuell.append(zeile[i + 1])
                i += 2
                continue
            if ch == "|":
                spalten.append("".join(aktuell))
                aktuell = []
                i += 1
                continue
            aktuell.append(ch)
            i += 1
        spalten.append("".join(aktuell))
        return spalten

    @staticmethod
    def _wert_dekodieren(wert: str) -> str:
        """Macht _wert_kodieren() wieder rückgängig."""
        out = []
        i = 0
        while i < len(wert):
            ch = wert[i]
            if ch == "\\" and i + 1 < len(wert):
                folgt = wert[i + 1]
                if folgt == "n":
                    out.append("\n")
                    i += 2
                    continue
                if folgt in ("|", "\\"):
                    out.append(folgt)
                    i += 2
                    continue
            out.append(ch)
            i += 1
        return "".join(out)

    def export_keys(self, keys: list) -> Path:
        lines = [self.START_MARK, ""]
        lines.append(f"Zuletzt synchronisiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("> [!warning] Diese Notiz enthält deine Schlüssel im Klartext.")
        lines.append("> Teile diesen Vault nur mit Personen/Diensten, denen du vertraust.")
        lines.append("")
        lines.append("| Name | Typ | Wert | Notiz | Erstellt |")
        lines.append("|---|---|---|---|---|")
        for k in keys:
            wert = self._wert_kodieren(k["wert"])
            meta = self._wert_kodieren(k.get("meta", ""))
            lines.append(f"| {k['label']} | {k['typ']} | `{wert}` | {meta} | {k.get('erstellt', '')} |")
        lines.append("")
        lines.append(self.END_MARK)
        new_block = "\n".join(lines)

        if self.note_path.exists():
            existing = self.note_path.read_text(encoding="utf-8")
            if self.START_MARK in existing and self.END_MARK in existing:
                before = existing.split(self.START_MARK)[0]
                after = existing.split(self.END_MARK)[-1]
                content = before + new_block + after
            else:
                # Bestehende, von Hand geschriebene Notiz -> Block ergänzen, nichts löschen.
                content = existing.rstrip() + "\n\n" + new_block + "\n"
        else:
            content = f"# Verschlüsselungs-Schlüssel (VP4)\n\n{new_block}\n"

        self.note_path.write_text(content, encoding="utf-8")
        return self.note_path

    def import_keys(self) -> list:
        if not self.note_path.exists():
            raise ValueError(f"Keine Datei '{self.NOTE_NAME}' im Vault gefunden.")
        content = self.note_path.read_text(encoding="utf-8")
        imported = []
        beschaedigt = []
        for line in content.splitlines():
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---") or line.startswith("| Name |"):
                continue
            cols = self._zeile_aufteilen(line)
            # Vor dem ersten und hinter dem letzten "|" steht nichts - weg damit.
            # (Nicht mit line.strip("|") machen: das würde einem Wert, der auf
            # ein escaptes "\|" endet, den Strich wegschneiden.)
            if cols and not cols[0].strip():
                cols = cols[1:]
            if cols and not cols[-1].strip():
                cols = cols[:-1]
            cols = [c.strip() for c in cols]
            if len(cols) < 5:
                continue
            label, typ, wert, meta, erstellt = cols[0], cols[1], cols[2], cols[3], cols[4]
            # Der Wert steht beim Export in Backticks - genau ein Paar entfernen.
            if len(wert) >= 2 and wert.startswith("`") and wert.endswith("`"):
                wert = wert[1:-1]
            wert = self._wert_dekodieren(wert)
            meta = self._wert_dekodieren(meta)
            if not label:
                continue
            # Notizen, die noch mit einer älteren Programmversion geschrieben
            # wurden, können abgeschnittene Schlüssel enthalten - erkennbar am
            # angehängten "...". Die sind nicht mehr zu retten. Besser einmal
            # deutlich sagen als stillschweigend einen kaputten Schlüssel
            # zurückgeben, mit dem sich später nichts mehr entschlüsseln lässt.
            if wert.endswith("..."):
                beschaedigt.append(label)
            imported.append({"label": label, "typ": typ, "wert": wert, "meta": meta, "erstellt": erstellt})
        if beschaedigt:
            raise ValueError(
                "Diese Schlüssel wurden von einer älteren Programmversion beim "
                "Export abgeschnitten und sind unvollständig:\n\n  - "
                + "\n  - ".join(beschaedigt)
                + "\n\nSie lassen sich nicht mehr reparieren. Falls du sie noch "
                  "im Schlüsselspeicher des Programms hast, exportiere sie "
                  "bitte einmal neu - dann werden sie vollständig geschrieben."
            )
        return imported


# =============================================================================
#  Freundesliste (für den Chat)
# =============================================================================

class FriendsStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = load_json(path, {})  # { id: {"nickname": str, "shared_key_b64": str|None} }

    def save(self):
        save_json(self.path, self.data)

    def add(self, friend_id: str, nickname: str = ""):
        friend_id = friend_id.strip().upper()
        if friend_id not in self.data:
            self.data[friend_id] = {"nickname": nickname, "shared_key_b64": None}
        elif nickname:
            self.data[friend_id]["nickname"] = nickname
        self.save()

    def remove(self, friend_id: str):
        self.data.pop(friend_id, None)
        self.save()

    def set_shared_key(self, friend_id: str, key_b64: str):
        if friend_id in self.data:
            self.data[friend_id]["shared_key_b64"] = key_b64
            self.save()

    def __contains__(self, friend_id: str):
        return friend_id in self.data

    def get(self, friend_id: str):
        return self.data.get(friend_id)

    def all(self):
        return dict(self.data)


# =============================================================================
#  LAN-Chat-Netzwerk (Discovery per UDP-Broadcast, Chat/Dateien per TCP)
# =============================================================================

BROADCAST_PORT = 51230
CHAT_PORT = 51231
PEER_TIMEOUT_SEC = 15
MAX_ENCRYPTED_FILE_SIZE = 50 * 1024 * 1024   # 50 MB
MAX_FILE_SIZE = 300 * 1024 * 1024            # 300 MB

MSG_HELLO = 0
MSG_TEXT = 1
MSG_META = 2
MSG_DATA = 3


class ChatNetwork:
    """Kümmert sich um:
      - Bekanntgeben der eigenen ID im lokalen Netz (WLAN) per UDP-Broadcast
      - Eine Liste gerade sichtbarer Geräte (self.peers)
      - Aufbau von TCP-Verbindungen zu Freunden für Chat/Dateiübertragung
    Events (neue Nachricht, empfangene Datei, Fehler) werden in eine Queue
    gelegt, die die GUI im Hauptthread regelmäßig abfragt.
    """

    def __init__(self, my_id: str, friends: FriendsStore, event_queue: "queue.Queue",
                 chat_port: int = CHAT_PORT, broadcast_port: int = BROADCAST_PORT,
                 bind_host: str = ""):
        self.my_id = my_id
        self.friends = friends
        self.events = event_queue
        self.chat_port = chat_port
        self.broadcast_port = broadcast_port
        self.bind_host = bind_host  # normalerweise "" (alle Interfaces); nur für Tests auf einer einzelnen Maschine relevant
        self.peers = {}          # {friend_id: (ip, last_seen_ts)}
        self._peers_lock = threading.Lock()
        self._connections = {}   # {friend_id: socket}
        self._conn_lock = threading.Lock()
        self._running = False
        self._server_sock = None

    # ---------------- Start/Stop ----------------

    def start(self):
        self._running = True
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_broadcast_loop, daemon=True).start()
        threading.Thread(target=self._tcp_server_loop, daemon=True).start()

    def stop(self):
        self._running = False
        try:
            if self._server_sock:
                self._server_sock.close()
        except OSError:
            pass
        with self._conn_lock:
            for s in self._connections.values():
                try:
                    s.close()
                except OSError:
                    pass

    # ---------------- Discovery (UDP) ----------------

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = f"VP4|ANNOUNCE|{self.my_id}".encode("utf-8")
        while self._running:
            try:
                sock.sendto(msg, ("255.255.255.255", self.broadcast_port))
            except OSError:
                pass
            time.sleep(4)

    def _listen_broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.bind_host, self.broadcast_port))
        except OSError as e:
            self.events.put(("error", f"Konnte Netzwerk-Erkennung nicht starten (Port {self.broadcast_port} belegt?): {e}"))
            return
        sock.settimeout(1.0)
        while self._running:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                self._prune_peers()
                continue
            except OSError:
                break
            try:
                text = data.decode("utf-8")
                parts = text.split("|")
                if len(parts) == 3 and parts[0] == "VP4" and parts[1] == "ANNOUNCE":
                    peer_id = parts[2]
                    if peer_id != self.my_id:
                        with self._peers_lock:
                            was_new = peer_id not in self.peers
                            self.peers[peer_id] = (addr[0], time.time())
                        if was_new:
                            self.events.put(("peer_update", None))
            except (UnicodeDecodeError, IndexError):
                continue

    def _prune_peers(self):
        now = time.time()
        with self._peers_lock:
            stale = [pid for pid, (ip, ts) in self.peers.items() if now - ts > PEER_TIMEOUT_SEC]
            for pid in stale:
                del self.peers[pid]
        if stale:
            self.events.put(("peer_update", None))

    def is_online(self, friend_id: str) -> bool:
        with self._peers_lock:
            return friend_id in self.peers

    # ---------------- TCP: Server ----------------

    def _tcp_server_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.bind_host, self.chat_port))
            sock.listen(20)
        except OSError as e:
            self.events.put(("error", f"Konnte Chat-Server nicht starten (Port {self.chat_port} belegt?): {e}"))
            return
        self._server_sock = sock
        while self._running:
            try:
                conn, addr = sock.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()

    def _handle_connection(self, conn: socket.socket):
        try:
            flags, msgtype, payload = self._recv_frame(conn)
            if msgtype != MSG_HELLO:
                conn.close()
                return
            sender_id = payload.decode("utf-8")
            if sender_id not in self.friends:
                conn.close()
                return
            with self._conn_lock:
                old = self._connections.get(sender_id)
                if old and old is not conn:
                    try:
                        old.close()
                    except OSError:
                        pass
                self._connections[sender_id] = conn
            self._read_loop(sender_id, conn)
        except (ConnectionError, OSError, struct.error):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _read_loop(self, friend_id: str, conn: socket.socket):
        while self._running:
            try:
                flags, msgtype, payload = self._recv_frame(conn)
            except (ConnectionError, OSError, struct.error):
                break
            if msgtype == MSG_TEXT:
                text = self._maybe_decrypt(friend_id, flags, payload).decode("utf-8", errors="replace")
                self.events.put(("message", {"from": friend_id, "text": text,
                                              "encrypted": bool(flags & 1)}))
            elif msgtype == MSG_META:
                meta_raw = self._maybe_decrypt(friend_id, flags, payload)
                try:
                    meta = json.loads(meta_raw.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                self._receive_data_frame(friend_id, conn, meta)
        with self._conn_lock:
            if self._connections.get(friend_id) is conn:
                del self._connections[friend_id]

    def _receive_data_frame(self, friend_id: str, conn: socket.socket, meta: dict):
        try:
            header = self._recv_exact(conn, 6)
        except (ConnectionError, OSError):
            return
        flags, msgtype, length = struct.unpack("!BBI", header)
        if msgtype != MSG_DATA or length > MAX_FILE_SIZE:
            self._recv_exact(conn, min(length, MAX_FILE_SIZE))
            return

        safe_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{Path(meta.get('name') or 'datei').name}"
        out_path = RECEIVED_DIR / safe_name

        if flags & 1:
            # Verschlüsselt -> komplett im Speicher empfangen und entschlüsseln
            raw = self._recv_exact(conn, length)
            try:
                data = self._maybe_decrypt(friend_id, flags, raw)
            except Exception:
                self.events.put(("error", f"Konnte Datei von {friend_id} nicht entschlüsseln."))
                return
            out_path.write_bytes(data)
        else:
            # Unverschlüsselt -> direkt in Datei streamen (spart RAM bei Videos)
            remaining = length
            with open(out_path, "wb") as f:
                while remaining > 0:
                    chunk = self._recv_exact(conn, min(65536, remaining))
                    f.write(chunk)
                    remaining -= len(chunk)

        self.events.put(("file", {"from": friend_id, "path": str(out_path),
                                   "kind": meta.get("kind", "file"), "name": meta.get("name", safe_name)}))

    # ---------------- TCP: Client / Senden ----------------

    def _get_connection(self, friend_id: str):
        with self._conn_lock:
            sock = self._connections.get(friend_id)
        if sock is not None:
            return sock
        with self._peers_lock:
            peer = self.peers.get(friend_id)
        if peer is None:
            return None
        ip = peer[0]
        try:
            sock = socket.create_connection((ip, self.chat_port), timeout=4)
            self._send_frame(sock, MSG_HELLO, self.my_id.encode("utf-8"), encrypted=False)
        except OSError:
            return None
        with self._conn_lock:
            self._connections[friend_id] = sock
        threading.Thread(target=self._read_loop, args=(friend_id, sock), daemon=True).start()
        return sock

    def send_text(self, friend_id: str, text: str):
        sock = self._get_connection(friend_id)
        if sock is None:
            raise ConnectionError("Freund ist gerade offline / nicht im selben WLAN erreichbar.")
        encrypted, payload = self._maybe_encrypt(friend_id, text.encode("utf-8"))
        self._send_frame(sock, MSG_TEXT, payload, encrypted)

    def send_file(self, friend_id: str, filepath: str, kind: str):
        sock = self._get_connection(friend_id)
        if sock is None:
            raise ConnectionError("Freund ist gerade offline / nicht im selben WLAN erreichbar.")
        size = os.path.getsize(filepath)
        if size > MAX_FILE_SIZE:
            raise ValueError("Datei ist zu groß (Limit: 300 MB).")
        name = os.path.basename(filepath)
        friend = self.friends.get(friend_id) or {}
        want_encrypt = bool(friend.get("shared_key_b64"))
        can_encrypt = want_encrypt and size <= MAX_ENCRYPTED_FILE_SIZE

        meta = {"kind": kind, "name": name, "size": size}
        meta_encrypted, meta_payload = self._maybe_encrypt(friend_id, json.dumps(meta).encode("utf-8"))
        self._send_frame(sock, MSG_META, meta_payload, meta_encrypted)

        if can_encrypt:
            with open(filepath, "rb") as f:
                raw = f.read()
            key = base64.b64decode(friend["shared_key_b64"])
            body = ModernCrypto.aes_encrypt_bytes(raw, key)
            self._send_frame(sock, MSG_DATA, body, encrypted=True)
        else:
            if want_encrypt and size > MAX_ENCRYPTED_FILE_SIZE:
                self.events.put(("info", f"'{name}' ist größer als 50 MB und wurde unverschlüsselt gesendet."))
            header = struct.pack("!BBI", 0, MSG_DATA, size)
            sock.sendall(header)
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    sock.sendall(chunk)

    # ---------------- Ver-/Entschlüsseln der Chat-Nutzlast ----------------

    def _maybe_encrypt(self, friend_id: str, payload: bytes):
        friend = self.friends.get(friend_id)
        if friend and friend.get("shared_key_b64"):
            key = base64.b64decode(friend["shared_key_b64"])
            return True, ModernCrypto.aes_encrypt_bytes(payload, key)
        return False, payload

    def _maybe_decrypt(self, friend_id: str, flags: int, payload: bytes) -> bytes:
        if flags & 1:
            friend = self.friends.get(friend_id)
            if not friend or not friend.get("shared_key_b64"):
                raise ValueError("Nachricht ist verschlüsselt, aber es ist kein gemeinsamer Schlüssel hinterlegt.")
            key = base64.b64decode(friend["shared_key_b64"])
            return ModernCrypto.aes_decrypt_bytes(payload, key)
        return payload

    # ---------------- Low-Level Framing ----------------

    @staticmethod
    def _send_frame(sock: socket.socket, msgtype: int, payload: bytes, encrypted: bool):
        flags = 1 if encrypted else 0
        header = struct.pack("!BBI", flags, msgtype, len(payload))
        sock.sendall(header + payload)

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(min(65536, n - len(buf)))
            if not chunk:
                raise ConnectionError("Verbindung wurde getrennt.")
            buf.extend(chunk)
        return bytes(buf)

    @classmethod
    def _recv_frame(cls, sock: socket.socket):
        header = cls._recv_exact(sock, 6)
        flags, msgtype, length = struct.unpack("!BBI", header)
        payload = cls._recv_exact(sock, length)
        return flags, msgtype, payload


# =============================================================================
#  GUI
# =============================================================================

ALGORITHMS = {
    "Caesar (Verschiebung)": {"key_hint": "Zahl, z.B. 3", "key_type": "text",
                               "enc": ClassicCiphers.caesar_encrypt, "dec": ClassicCiphers.caesar_decrypt},
    "Vigenère": {"key_hint": "Schlüsselwort, z.B. Wolke", "key_type": "text",
                 "enc": ClassicCiphers.vigenere_encrypt, "dec": ClassicCiphers.vigenere_decrypt},
    "XOR": {"key_hint": "beliebiger Text als Schlüssel", "key_type": "text",
            "enc": ClassicCiphers.xor_encrypt, "dec": ClassicCiphers.xor_decrypt},
    "Base64 (Kodierung, kein echter Schutz)": {"key_hint": "kein Schlüssel nötig", "key_type": "none",
                                                "enc": ClassicCiphers.base64_encode, "dec": ClassicCiphers.base64_decode},
    "AES-256 (empfohlen für echten Schutz)": {"key_hint": "AES-Schlüssel (Base64)", "key_type": "aes",
                                               "enc": ModernCrypto.aes_encrypt, "dec": ModernCrypto.aes_decrypt},
    "RSA-2048 (Public/Private Key)": {"key_hint": "PEM Public/Private Key", "key_type": "rsa",
                                       "enc": ModernCrypto.rsa_encrypt, "dec": ModernCrypto.rsa_decrypt},
}


class MasterPasswordDialog(simpledialog.Dialog):
    def __init__(self, parent, title, create_mode: bool):
        self.create_mode = create_mode
        self.result_password = None
        super().__init__(parent, title)

    def body(self, master):
        msg = ("Lege ein Master-Passwort für deinen Schlüsselspeicher fest.\n"
               "Merk es dir gut - ohne dieses Passwort kommst du nicht mehr an\n"
               "deine gespeicherten Schlüssel!") if self.create_mode else \
              "Bitte gib dein Master-Passwort ein, um den Schlüsselspeicher zu entsperren."
        tk.Label(master, text=msg, justify="left").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")
        tk.Label(master, text="Passwort:").grid(row=1, column=0, sticky="e")
        self.entry = tk.Entry(master, show="*", width=30)
        self.entry.grid(row=1, column=1, pady=4)
        if self.create_mode:
            tk.Label(master, text="Wiederholen:").grid(row=2, column=0, sticky="e")
            self.entry2 = tk.Entry(master, show="*", width=30)
            self.entry2.grid(row=2, column=1, pady=4)
        else:
            self.entry2 = None
        return self.entry

    def validate(self):
        pw = self.entry.get()
        if not pw:
            messagebox.showwarning("Fehlt", "Bitte ein Passwort eingeben.", parent=self)
            return False
        if self.create_mode:
            if len(pw) < 4:
                messagebox.showwarning("Zu kurz", "Bitte mindestens 4 Zeichen verwenden.", parent=self)
                return False
            if pw != self.entry2.get():
                messagebox.showwarning("Stimmt nicht überein", "Die beiden Passwörter sind nicht gleich.", parent=self)
                return False
        return True

    def apply(self):
        self.result_password = self.entry.get()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Verschlüsselungs Programm 4.0")
        self.geometry("880x620")
        self.minsize(760, 540)

        self.config_data = load_config()
        self.my_id = self.config_data["my_id"]
        self.keystore = KeyStore(KEYSTORE_FILE)
        self.friends = FriendsStore(FRIENDS_FILE)
        self.event_queue = queue.Queue()
        self.network = ChatNetwork(self.my_id, self.friends, self.event_queue)
        self.network.start()

        self.active_chat_friend = None
        self.chat_histories = {}  # friend_id -> list[str] (für die Anzeige)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(300, self._poll_events)
        self.after(1000, self._refresh_friend_list)

    # ------------------------------------------------------------------
    # UI-Aufbau
    # ------------------------------------------------------------------

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.tab_crypto = ttk.Frame(nb)
        self.tab_keys = ttk.Frame(nb)
        self.tab_obsidian = ttk.Frame(nb)
        self.tab_chat = ttk.Frame(nb)
        self.tab_info = ttk.Frame(nb)

        nb.add(self.tab_crypto, text="Ver-/Entschlüsseln")
        nb.add(self.tab_keys, text="Schlüsselverwaltung")
        nb.add(self.tab_obsidian, text="Obsidian")
        nb.add(self.tab_chat, text="Chat")
        nb.add(self.tab_info, text="Info / Hilfe")

        self._build_tab_crypto()
        self._build_tab_keys()
        self._build_tab_obsidian()
        self._build_tab_chat()
        self._build_tab_info()

    # ---------------- Tab: Ver-/Entschlüsseln ----------------

    def _build_tab_crypto(self):
        f = self.tab_crypto
        top = ttk.Frame(f)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Methode:").grid(row=0, column=0, sticky="w")
        self.algo_var = tk.StringVar(value=list(ALGORITHMS.keys())[0])
        algo_box = ttk.Combobox(top, textvariable=self.algo_var, values=list(ALGORITHMS.keys()),
                                 state="readonly", width=42)
        algo_box.grid(row=0, column=1, sticky="w", padx=6)
        algo_box.bind("<<ComboboxSelected>>", lambda e: self._update_key_hint())

        self.key_hint_label = ttk.Label(top, text="", foreground="#555")
        self.key_hint_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        key_row = ttk.Frame(f)
        key_row.pack(fill="x", padx=10, pady=4)
        ttk.Label(key_row, text="Schlüssel:").pack(side="left")
        self.key_entry = tk.Text(key_row, height=2, width=60, wrap="word")
        self.key_entry.pack(side="left", padx=6, fill="x", expand=True)

        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", padx=10, pady=2)
        ttk.Button(btn_row, text="Neuen Schlüssel generieren", command=self._generate_key_for_selected).pack(side="left")
        ttk.Button(btn_row, text="Gespeicherten Schlüssel laden...", command=self._load_saved_key_into_field).pack(side="left", padx=6)

        ttk.Label(f, text="Eingabetext:").pack(anchor="w", padx=10, pady=(8, 0))
        self.input_text = scrolledtext.ScrolledText(f, height=8, wrap="word")
        self.input_text.pack(fill="both", expand=True, padx=10, pady=4)

        action_row = ttk.Frame(f)
        action_row.pack(fill="x", padx=10, pady=4)
        ttk.Button(action_row, text="Verschlüsseln →", command=lambda: self._do_crypto(True)).pack(side="left")
        ttk.Button(action_row, text="Entschlüsseln →", command=lambda: self._do_crypto(False)).pack(side="left", padx=6)
        ttk.Button(action_row, text="Ergebnis kopieren", command=self._copy_output).pack(side="left", padx=6)
        ttk.Button(action_row, text="Felder leeren", command=self._clear_crypto_fields).pack(side="left", padx=6)

        ttk.Label(f, text="Ergebnis:").pack(anchor="w", padx=10, pady=(8, 0))
        self.output_text = scrolledtext.ScrolledText(f, height=8, wrap="word")
        self.output_text.pack(fill="both", expand=True, padx=10, pady=4)

        self._update_key_hint()

    def _update_key_hint(self):
        info = ALGORITHMS[self.algo_var.get()]
        self.key_hint_label.config(text=f"Erwartetes Format: {info['key_hint']}")

    def _clear_crypto_fields(self):
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.key_entry.delete("1.0", "end")

    def _generate_key_for_selected(self):
        info = ALGORITHMS[self.algo_var.get()]
        if info["key_type"] == "aes":
            key = ModernCrypto.generate_aes_key()
            self.key_entry.delete("1.0", "end")
            self.key_entry.insert("1.0", key)
            self._offer_save_key("aes", key)
        elif info["key_type"] == "rsa":
            priv, pub = ModernCrypto.generate_rsa_keypair()
            self.key_entry.delete("1.0", "end")
            self.key_entry.insert("1.0", pub)
            messagebox.showinfo(
                "RSA-Schlüsselpaar erzeugt",
                "Ein neues RSA-Schlüsselpaar wurde erzeugt.\n\n"
                "Zum VERSCHLÜSSELN wird der Public Key genutzt (steht jetzt im Feld).\n"
                "Zum ENTSCHLÜSSELN brauchst du den Private Key - du kannst jetzt beide "
                "in der Schlüsselverwaltung speichern.")
            if messagebox.askyesno("Speichern?", "Beide Schlüssel (Public + Private) jetzt in der Schlüsselverwaltung speichern?"):
                label = simpledialog.askstring("Name", "Name für dieses Schlüsselpaar (z.B. 'Mein RSA Key'):", parent=self)
                if label:
                    try:
                        self._ensure_keystore_unlocked()
                        self.keystore.add_key(f"{label} (public)", "rsa-public", pub)
                        self.keystore.add_key(f"{label} (private)", "rsa-private", priv)
                        self._refresh_key_list()
                        messagebox.showinfo("Gespeichert", "RSA-Schlüsselpaar wurde gespeichert.")
                    except (ValueError, KeyStoreLockedError) as e:
                        messagebox.showerror("Fehler", str(e))
        elif info["key_type"] == "none":
            messagebox.showinfo("Kein Schlüssel nötig", "Diese Methode braucht keinen Schlüssel.")
        else:
            messagebox.showinfo("Manuell", "Bitte selbst einen Schlüssel/ein Schlüsselwort eintragen.")

    def _offer_save_key(self, typ: str, value: str):
        if messagebox.askyesno("Speichern?", "Diesen Schlüssel jetzt in der Schlüsselverwaltung speichern?"):
            label = simpledialog.askstring("Name", "Name für diesen Schlüssel:", parent=self)
            if label:
                try:
                    self._ensure_keystore_unlocked()
                    self.keystore.add_key(label, typ, value)
                    self._refresh_key_list()
                    messagebox.showinfo("Gespeichert", f"Schlüssel '{label}' wurde gespeichert.")
                except (ValueError, KeyStoreLockedError) as e:
                    messagebox.showerror("Fehler", str(e))

    def _load_saved_key_into_field(self):
        try:
            self._ensure_keystore_unlocked()
        except KeyStoreLockedError:
            return
        keys = self.keystore.list_keys()
        if not keys:
            messagebox.showinfo("Keine Schlüssel", "Es sind noch keine Schlüssel gespeichert.")
            return
        labels = [k["label"] for k in keys]
        choice = self._ask_choice("Schlüssel wählen", "Welchen gespeicherten Schlüssel laden?", labels)
        if choice:
            key = self.keystore.get_key(choice)
            self.key_entry.delete("1.0", "end")
            self.key_entry.insert("1.0", str(key["wert"]))

    def _ask_choice(self, title, prompt, options):
        top = tk.Toplevel(self)
        top.title(title)
        top.transient(self)
        top.grab_set()
        ttk.Label(top, text=prompt).pack(padx=12, pady=8)
        var = tk.StringVar(value=options[0])
        box = ttk.Combobox(top, textvariable=var, values=options, state="readonly", width=40)
        box.pack(padx=12, pady=4)
        result = {"value": None}

        def ok():
            result["value"] = var.get()
            top.destroy()

        ttk.Button(top, text="OK", command=ok).pack(pady=8)
        top.wait_window()
        return result["value"]

    def _do_crypto(self, encrypt: bool):
        algo_name = self.algo_var.get()
        info = ALGORITHMS[algo_name]
        text = self.input_text.get("1.0", "end-1c")
        key = self.key_entry.get("1.0", "end-1c").strip()
        if not text:
            messagebox.showwarning("Fehlt", "Bitte einen Text eingeben.")
            return
        try:
            fn = info["enc"] if encrypt else info["dec"]
            result = fn(text, key)
        except ValueError as e:
            messagebox.showerror("Fehler", str(e))
            return
        except Exception as e:
            messagebox.showerror("Unerwarteter Fehler", str(e))
            return
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", result)

    def _copy_output(self):
        text = self.output_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Kopiert", "Ergebnis wurde in die Zwischenablage kopiert.")

    # ---------------- Tab: Schlüsselverwaltung ----------------

    def _build_tab_keys(self):
        f = self.tab_keys
        top = ttk.Frame(f)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="Schlüsselspeicher entsperren / anlegen", command=self._unlock_keystore_button).pack(side="left")
        ttk.Button(top, text="Sperren", command=self._lock_keystore).pack(side="left", padx=6)
        self.keystore_status_label = ttk.Label(top, text="🔒 gesperrt", foreground="#a33")
        self.keystore_status_label.pack(side="left", padx=12)

        columns = ("label", "typ", "erstellt")
        self.keys_tree = ttk.Treeview(f, columns=columns, show="headings", height=14)
        for c, txt, w in (("label", "Name", 220), ("typ", "Typ", 120), ("erstellt", "Erstellt am", 140)):
            self.keys_tree.heading(c, text=txt)
            self.keys_tree.column(c, width=w)
        self.keys_tree.pack(fill="both", expand=True, padx=10, pady=6)

        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", padx=10, pady=4)
        ttk.Button(btn_row, text="Neuen Schlüssel manuell hinzufügen", command=self._add_key_manual).pack(side="left")
        ttk.Button(btn_row, text="Anzeigen", command=self._show_selected_key).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Kopieren", command=self._copy_selected_key).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Löschen", command=self._delete_selected_key).pack(side="left", padx=6)

    def _ensure_keystore_unlocked(self):
        if self.keystore.is_unlocked():
            return
        if self.keystore.exists():
            while True:
                dlg = MasterPasswordDialog(self, "Schlüsselspeicher entsperren", create_mode=False)
                if dlg.result_password is None:
                    raise KeyStoreLockedError("Abgebrochen.")
                try:
                    self.keystore.unlock(dlg.result_password)
                    break
                except ValueError as e:
                    messagebox.showerror("Fehler", str(e))
        else:
            dlg = MasterPasswordDialog(self, "Schlüsselspeicher anlegen", create_mode=True)
            if dlg.result_password is None:
                raise KeyStoreLockedError("Abgebrochen.")
            self.keystore.create(dlg.result_password)
        self._refresh_key_list()

    def _unlock_keystore_button(self):
        try:
            self._ensure_keystore_unlocked()
        except KeyStoreLockedError:
            pass

    def _lock_keystore(self):
        self.keystore.lock()
        self._refresh_key_list()

    def _refresh_key_list(self):
        for row in self.keys_tree.get_children():
            self.keys_tree.delete(row)
        if self.keystore.is_unlocked():
            self.keystore_status_label.config(text="🔓 entsperrt", foreground="#2a2")
            for k in self.keystore.list_keys():
                self.keys_tree.insert("", "end", iid=k["label"], values=(k["label"], k["typ"], k["erstellt"]))
        else:
            self.keystore_status_label.config(text="🔒 gesperrt", foreground="#a33")

    def _add_key_manual(self):
        try:
            self._ensure_keystore_unlocked()
        except KeyStoreLockedError:
            return
        label = simpledialog.askstring("Name", "Name für den Schlüssel:", parent=self)
        if not label:
            return
        typ = self._ask_choice("Typ", "Um welche Art von Schlüssel handelt es sich?",
                                ["caesar", "vigenere", "xor", "aes", "rsa-public", "rsa-private", "sonstiges"])
        if not typ:
            return
        value = simpledialog.askstring("Wert", "Schlüsselwert:", parent=self)
        if value is None:
            return
        try:
            self.keystore.add_key(label, typ, value)
            self._refresh_key_list()
        except ValueError as e:
            messagebox.showerror("Fehler", str(e))

    def _selected_key_label(self):
        sel = self.keys_tree.selection()
        return sel[0] if sel else None

    def _show_selected_key(self):
        label = self._selected_key_label()
        if not label:
            messagebox.showinfo("Nichts ausgewählt", "Bitte zuerst einen Schlüssel in der Liste auswählen.")
            return
        k = self.keystore.get_key(label)
        top = tk.Toplevel(self)
        top.title(k["label"])
        text = scrolledtext.ScrolledText(top, width=70, height=10, wrap="word")
        text.pack(padx=10, pady=10, fill="both", expand=True)
        text.insert("1.0", str(k["wert"]))
        text.config(state="disabled")

    def _copy_selected_key(self):
        label = self._selected_key_label()
        if not label:
            return
        k = self.keystore.get_key(label)
        self.clipboard_clear()
        self.clipboard_append(str(k["wert"]))
        messagebox.showinfo("Kopiert", f"Wert von '{label}' wurde kopiert.")

    def _delete_selected_key(self):
        label = self._selected_key_label()
        if not label:
            return
        if messagebox.askyesno("Löschen?", f"Schlüssel '{label}' wirklich löschen?"):
            self.keystore.delete_key(label)
            self._refresh_key_list()

    # ---------------- Tab: Obsidian ----------------

    def _build_tab_obsidian(self):
        f = self.tab_obsidian
        info = ("Verknüpfe VP4 mit deinem Obsidian-Vault, um deine gespeicherten Schlüssel dort\n"
                "als Notiz zu sehen und zu verwalten.\n\n"
                "⚠️ Achtung: Die Notiz enthält deine Schlüssel im Klartext. Nur exportieren,\n"
                "wenn du dem Vault-Ordner (und ggf. dessen Synchronisation) vertraust.")
        ttk.Label(f, text=info, justify="left", foreground="#555").pack(anchor="w", padx=10, pady=10)

        row = ttk.Frame(f)
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text="Obsidian-Vault-Ordner:").pack(side="left")
        self.vault_var = tk.StringVar(value=self.config_data.get("obsidian_vault", ""))
        ttk.Entry(row, textvariable=self.vault_var, width=55).pack(side="left", padx=6)
        ttk.Button(row, text="Durchsuchen...", command=self._choose_vault_folder).pack(side="left")

        btn_row = ttk.Frame(f)
        btn_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_row, text="Jetzt nach Obsidian exportieren →", command=self._export_to_obsidian).pack(side="left")
        ttk.Button(btn_row, text="← Aus Obsidian importieren", command=self._import_from_obsidian).pack(side="left", padx=6)

        self.obsidian_status = ttk.Label(f, text="", foreground="#555")
        self.obsidian_status.pack(anchor="w", padx=10, pady=6)

    def _choose_vault_folder(self):
        path = filedialog.askdirectory(title="Obsidian-Vault-Ordner wählen")
        if path:
            self.vault_var.set(path)
            self.config_data["obsidian_vault"] = path
            save_json(CONFIG_FILE, self.config_data)

    def _export_to_obsidian(self):
        try:
            self._ensure_keystore_unlocked()
        except KeyStoreLockedError:
            return
        self.config_data["obsidian_vault"] = self.vault_var.get()
        save_json(CONFIG_FILE, self.config_data)
        try:
            sync = ObsidianSync(self.vault_var.get())
            path = sync.export_keys(self.keystore.list_keys())
            self.obsidian_status.config(text=f"✓ Exportiert nach: {path}", foreground="#2a2")
        except ValueError as e:
            messagebox.showerror("Fehler", str(e))

    def _import_from_obsidian(self):
        try:
            self._ensure_keystore_unlocked()
        except KeyStoreLockedError:
            return
        self.config_data["obsidian_vault"] = self.vault_var.get()
        save_json(CONFIG_FILE, self.config_data)
        try:
            sync = ObsidianSync(self.vault_var.get())
            imported = sync.import_keys()
            self.keystore.replace_all(imported)
            self._refresh_key_list()
            self.obsidian_status.config(text=f"✓ {len(imported)} Schlüssel aus Obsidian importiert.", foreground="#2a2")
        except ValueError as e:
            messagebox.showerror("Fehler", str(e))

    # ---------------- Tab: Chat ----------------

    def _build_tab_chat(self):
        f = self.tab_chat
        top = ttk.Frame(f)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Meine ID:").pack(side="left")
        self.id_label = ttk.Label(top, text=self.my_id, font=("TkDefaultFont", 11, "bold"))
        self.id_label.pack(side="left", padx=6)
        ttk.Button(top, text="Kopieren", command=self._copy_my_id).pack(side="left")
        ttk.Label(top, text="   (diese ID an Freunde weitergeben, damit sie dich hinzufügen können)",
                  foreground="#555").pack(side="left")

        add_row = ttk.Frame(f)
        add_row.pack(fill="x", padx=10, pady=4)
        ttk.Label(add_row, text="Freund-ID hinzufügen:").pack(side="left")
        self.add_id_entry = ttk.Entry(add_row, width=16)
        self.add_id_entry.pack(side="left", padx=4)
        ttk.Label(add_row, text="Name (optional):").pack(side="left")
        self.add_name_entry = ttk.Entry(add_row, width=16)
        self.add_name_entry.pack(side="left", padx=4)
        ttk.Button(add_row, text="Hinzufügen", command=self._add_friend).pack(side="left", padx=4)

        body = ttk.Frame(f)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Freunde:").pack(anchor="w")
        self.friends_list = tk.Listbox(left, width=26, height=20)
        self.friends_list.pack(fill="y", expand=False)
        self.friends_list.bind("<<ListboxSelect>>", self._on_select_friend)
        fbtn = ttk.Frame(left)
        fbtn.pack(fill="x", pady=4)
        ttk.Button(fbtn, text="Gem. Schlüssel setzen", command=self._set_shared_key).pack(fill="x")
        ttk.Button(fbtn, text="Entfernen", command=self._remove_friend).pack(fill="x", pady=(4, 0))

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.chat_title = ttk.Label(right, text="Kein Freund ausgewählt", font=("TkDefaultFont", 10, "bold"))
        self.chat_title.pack(anchor="w")
        self.chat_display = scrolledtext.ScrolledText(right, state="disabled", wrap="word")
        self.chat_display.pack(fill="both", expand=True, pady=4)

        send_row = ttk.Frame(right)
        send_row.pack(fill="x")
        self.chat_entry = ttk.Entry(send_row)
        self.chat_entry.pack(side="left", fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda e: self._send_chat_text())
        ttk.Button(send_row, text="Senden", command=self._send_chat_text).pack(side="left", padx=4)
        ttk.Button(send_row, text="Bild senden", command=lambda: self._send_chat_file("image")).pack(side="left", padx=2)
        ttk.Button(send_row, text="Video senden", command=lambda: self._send_chat_file("video")).pack(side="left", padx=2)
        ttk.Button(send_row, text="Datei senden", command=lambda: self._send_chat_file("file")).pack(side="left", padx=2)

    def _copy_my_id(self):
        self.clipboard_clear()
        self.clipboard_append(self.my_id)

    def _add_friend(self):
        fid = self.add_id_entry.get().strip().upper()
        if not fid:
            return
        if fid == self.my_id:
            messagebox.showwarning("Geht nicht", "Das ist deine eigene ID.")
            return
        name = self.add_name_entry.get().strip()
        self.friends.add(fid, name)
        self.add_id_entry.delete(0, "end")
        self.add_name_entry.delete(0, "end")
        self._refresh_friend_list()

    def _friend_display_name(self, fid):
        info = self.friends.get(fid) or {}
        nick = info.get("nickname")
        online = "🟢" if self.network.is_online(fid) else "⚪"
        enc = "🔒" if info.get("shared_key_b64") else ""
        label = f"{nick} ({fid})" if nick else fid
        return f"{online} {label} {enc}"

    def _refresh_friend_list(self):
        selected_fid = self.active_chat_friend
        self.friends_list.delete(0, "end")
        self._friend_order = list(self.friends.all().keys())
        for fid in self._friend_order:
            self.friends_list.insert("end", self._friend_display_name(fid))
        if selected_fid in self._friend_order:
            idx = self._friend_order.index(selected_fid)
            self.friends_list.selection_set(idx)
        self.after(2000, self._refresh_friend_list)

    def _on_select_friend(self, event):
        sel = self.friends_list.curselection()
        if not sel:
            return
        fid = self._friend_order[sel[0]]
        self.active_chat_friend = fid
        info = self.friends.get(fid) or {}
        nick = info.get("nickname")
        status = "online" if self.network.is_online(fid) else "offline"
        self.chat_title.config(text=f"Chat mit {nick + ' ' if nick else ''}({fid}) - {status}")
        self._render_chat_history(fid)

    def _render_chat_history(self, fid):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", "end")
        for line in self.chat_histories.get(fid, []):
            self.chat_display.insert("end", line + "\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _append_chat_line(self, fid, line):
        self.chat_histories.setdefault(fid, []).append(line)
        if self.active_chat_friend == fid:
            self.chat_display.config(state="normal")
            self.chat_display.insert("end", line + "\n")
            self.chat_display.config(state="disabled")
            self.chat_display.see("end")

    def _remove_friend(self):
        if not self.active_chat_friend:
            return
        if messagebox.askyesno("Entfernen?", f"Freund '{self.active_chat_friend}' wirklich entfernen?"):
            self.friends.remove(self.active_chat_friend)
            self.active_chat_friend = None
            self._refresh_friend_list()

    def _set_shared_key(self):
        if not self.active_chat_friend:
            messagebox.showinfo("Nichts ausgewählt", "Bitte zuerst einen Freund auswählen.")
            return
        top = tk.Toplevel(self)
        top.title("Gemeinsamen Schlüssel setzen")
        ttk.Label(top, text=("Trage hier einen gemeinsamen AES-Schlüssel ein (Base64), den du und dein\n"
                              "Freund BEIDE in eurer jeweiligen App eintragen. Nachrichten/Dateien an diesen\n"
                              "Freund werden dann verschlüsselt übertragen. Wie ihr den Schlüssel austauscht,\n"
                              "bleibt euch überlassen (z.B. persönlich, Anruf, o.ä.)."),
                  justify="left").pack(padx=10, pady=8)
        entry = tk.Entry(top, width=50)
        entry.pack(padx=10, pady=4)
        existing = (self.friends.get(self.active_chat_friend) or {}).get("shared_key_b64")
        if existing:
            entry.insert(0, existing)

        def generate():
            entry.delete(0, "end")
            entry.insert(0, ModernCrypto.generate_aes_key())

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=6)
        ttk.Button(btn_row, text="Neu generieren", command=generate).pack(side="left", padx=4)

        def save():
            self.friends.set_shared_key(self.active_chat_friend, entry.get().strip() or None)
            self._refresh_friend_list()
            top.destroy()

        ttk.Button(btn_row, text="Speichern", command=save).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Entfernen", command=lambda: (self.friends.set_shared_key(self.active_chat_friend, None), top.destroy(), self._refresh_friend_list())).pack(side="left", padx=4)

    def _send_chat_text(self):
        if not self.active_chat_friend:
            messagebox.showinfo("Nichts ausgewählt", "Bitte zuerst einen Freund auswählen.")
            return
        text = self.chat_entry.get().strip()
        if not text:
            return
        try:
            self.network.send_text(self.active_chat_friend, text)
            self._append_chat_line(self.active_chat_friend, f"Du: {text}")
            self.chat_entry.delete(0, "end")
        except ConnectionError as e:
            messagebox.showerror("Fehler", str(e))

    def _send_chat_file(self, kind):
        if not self.active_chat_friend:
            messagebox.showinfo("Nichts ausgewählt", "Bitte zuerst einen Freund auswählen.")
            return
        filetypes = {
            "image": [("Bilder", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("Alle Dateien", "*.*")],
            "video": [("Videos", "*.mp4 *.mov *.avi *.mkv *.webm"), ("Alle Dateien", "*.*")],
            "file": [("Alle Dateien", "*.*")],
        }[kind]
        path = filedialog.askopenfilename(title="Datei wählen", filetypes=filetypes)
        if not path:
            return
        try:
            self.network.send_file(self.active_chat_friend, path, kind)
            self._append_chat_line(self.active_chat_friend, f"Du: [{kind}] {os.path.basename(path)} gesendet")
        except (ConnectionError, ValueError) as e:
            messagebox.showerror("Fehler", str(e))

    # ---------------- Tab: Info / Hilfe ----------------

    def _build_tab_info(self):
        f = self.tab_info
        text = scrolledtext.ScrolledText(f, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", __doc__.strip())
        text.config(state="disabled")

    # ------------------------------------------------------------------
    # Hintergrund-Events (Netzwerk) im Hauptthread verarbeiten
    # ------------------------------------------------------------------

    def _poll_events(self):
        try:
            while True:
                kind, data = self.event_queue.get_nowait()
                if kind == "message":
                    fid = data["from"]
                    lock = "🔒" if data["encrypted"] else "🔓"
                    nick = (self.friends.get(fid) or {}).get("nickname") or fid
                    self._append_chat_line(fid, f"{nick} {lock}: {data['text']}")
                elif kind == "file":
                    fid = data["from"]
                    nick = (self.friends.get(fid) or {}).get("nickname") or fid
                    self._append_chat_line(fid, f"{nick} hat eine Datei geschickt: {data['name']}  -> gespeichert unter {data['path']}")
                elif kind == "peer_update":
                    pass  # Online-Status wird beim nächsten Refresh der Liste sowieso aktualisiert
                elif kind == "error":
                    print("[VP4] Netzwerkfehler:", data)
                elif kind == "info":
                    print("[VP4] Info:", data)
        except queue.Empty:
            pass
        self.after(300, self._poll_events)

    def _on_close(self):
        self.network.stop()
        self.destroy()


# =============================================================================
#  main
# =============================================================================

def main():
    if not _CRYPTO_OK:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Abhängigkeit fehlt",
            "Das Python-Paket 'cryptography' wird benötigt, ist aber nicht installiert.\n\n"
            "Bitte einmalig in einem Terminal ausführen:\n\n"
            "    pip install cryptography\n\n"
            f"(Technischer Fehler: {_CRYPTO_IMPORT_ERROR})",
        )
        sys.exit(1)

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
