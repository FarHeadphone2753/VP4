#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 discord_konfig.py - die eingebauten Discord-Zugangsdaten
=====================================================================
Hier stehen absichtlich nur leere Platzhalter. Die echten Werte setzt
der GitHub-Workflow beim Bauen der .exe ein (Schritt "Discord-Zugang
einsetzen" in .github/workflows/release.yml); sie kommen dort aus den
Repository-Secrets und landen nur in der fertigen .exe - nie in diesem
Quelltext.

WARUM DIESE DATEI ÜBERHAUPT EXISTIERT
--------------------------------------
Damit Freunde nichts einrichten müssen. Sie bekommen die VP4.exe,
starten sie und können schreiben - Token und Kanal stecken schon drin.
Müsste jeder die Werte von Hand eintragen, würde es kaum jemand tun.

WARUM DIE WERTE NICHT EINFACH HIER STEHEN
------------------------------------------
Stünde hier ein echter Bot-Token und die Datei würde committet, gäbe
es zwei Probleme statt einem: GitHubs Secret-Scanning erkennt ihn in
einem öffentlichen Repo automatisch und lässt Discord ihn umgehend
sperren, UND jeder, der den Quelltext liest, könnte ihn missbrauchen -
selbst wenn er nicht gesperrt würde.

Zum Testen aus dem Quelltext heraus (python VP4.py) bleibt diese Datei
leer. Token und Kanal-ID trägt man dann unter Einstellungen → Discord
von Hand ein; was dort steht, geht der eingebauten Voreinstellung
immer vor.

EHRLICH DAZU
-------------
In der .exe ist der Token nicht wirklich versteckt - wer die Datei hat,
kann ihn mit etwas Mühe herausholen. Für einen Freundeskreis, dem man
die Datei ohnehin persönlich schickt, ist das vertretbar. Diese .exe
sollte man deshalb nicht öffentlich zum Download anbieten.
=====================================================================
"""

BOT_TOKEN = ""
KANAL_ID = ""

# Der Schlüssel, den alle mit derselben VP4.exe teilen. Damit können Freunde
# sofort schreiben, ohne vorher einen Schlüssel auszutauschen - das war
# ausdrücklich so gewollt.
#
# Ehrlich dazu: Das ist ein GRUPPEN-Schlüssel. Gegen Discord und gegen
# Fremde im Server schützt er vollständig, untereinander gar nicht - wer
# dieselbe .exe hat, kann jede Nachricht im Kanal mitlesen, auch die
# zwischen zwei anderen. Für einen Freundeskreis ist das ein Gruppenchat,
# und genau so steht es auch im Programm.
#
# Wer es zwischen zwei bestimmten Leuten dichter haben will, trägt für den
# Freund einen eigenen Schlüssel ein (🔑 neben der Freundesliste). Der geht
# dem Gruppenschlüssel immer vor.
GRUPPEN_SCHLUESSEL = ""
