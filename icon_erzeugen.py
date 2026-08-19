#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=====================================================================
 icon_erzeugen.py - erzeugt das Programm-Icon (vp4.ico)
=====================================================================
Muss nur einmal laufen bzw. dann wieder, wenn das Icon anders aussehen
soll:

    python icon_erzeugen.py

Danach liegt vp4.ico im Ordner und wird beim Bauen der .exe verwendet.

Das Icon wird hier gezeichnet statt als Bilddatei mitgeliefert, damit
es sich jederzeit ändern lässt und keine fremde Grafik im Projekt liegt.
Gezeichnet wird ein Schloss auf blauem, abgerundetem Grund - in mehreren
Größen, damit es sowohl in der Taskleiste als auch in großer Ansicht
sauber aussieht.
=====================================================================
"""

from pathlib import Path

from PIL import Image, ImageDraw

# Dieselbe Akzentfarbe wie in der Oberfläche. Der Verlauf geht von hell
# oben nach dunkel unten - beide Töne müssen kräftig genug bleiben, damit
# das weiße Schloss deutlich darauf steht.
BLAU_OBEN = (59, 130, 246)
BLAU_UNTEN = (29, 64, 175)
WEISS = (255, 255, 255)


def schloss_zeichnen(kante: int) -> Image.Image:
    """Zeichnet das Icon in der gewünschten Kantenlänge.

    Gezeichnet wird viermal so groß und danach verkleinert - dadurch
    werden die Rundungen glatt statt ausgefranst.
    """
    f = 4
    g = kante * f
    bild = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)

    # Hintergrund: kräftiger Verlauf, danach auf abgerundete Ecken zugeschnitten.
    # (Erst den Verlauf über die volle Fläche zeichnen und dann maskieren -
    # ein halbdurchsichtiger Verlauf über einer Füllfarbe wäscht die Farbe aus.)
    ecke = int(g * 0.22)
    verlauf = Image.new("RGB", (g, g))
    vd = ImageDraw.Draw(verlauf)
    for y in range(g):
        anteil = y / max(g - 1, 1)
        vd.line([(0, y), (g, y)],
                fill=(round(BLAU_OBEN[0] + (BLAU_UNTEN[0] - BLAU_OBEN[0]) * anteil),
                      round(BLAU_OBEN[1] + (BLAU_UNTEN[1] - BLAU_OBEN[1]) * anteil),
                      round(BLAU_OBEN[2] + (BLAU_UNTEN[2] - BLAU_OBEN[2]) * anteil)))
    maske = Image.new("L", (g, g), 0)
    ImageDraw.Draw(maske).rounded_rectangle([0, 0, g - 1, g - 1], radius=ecke, fill=255)
    bild.paste(verlauf, (0, 0), maske)
    d = ImageDraw.Draw(bild)

    # Schlossbügel: ein dicker Bogen oben
    buegel_breite = int(g * 0.075)
    bx0, bx1 = int(g * 0.315), int(g * 0.685)
    by0, by1 = int(g * 0.20), int(g * 0.58)
    d.arc([bx0, by0, bx1, by1], start=180, end=360,
          fill=WEISS, width=buegel_breite)
    # Die beiden Enden des Bügels bis zum Gehäuse verlängern
    for x in (bx0 + buegel_breite // 2, bx1 - buegel_breite // 2):
        d.line([(x, int(g * 0.39)), (x, int(g * 0.50))],
               fill=WEISS, width=buegel_breite)

    # Gehäuse
    d.rounded_rectangle([int(g * 0.245), int(g * 0.475),
                         int(g * 0.755), int(g * 0.815)],
                        radius=int(g * 0.075), fill=WEISS)

    # Schlüsselloch
    mitte = g // 2
    r = int(g * 0.052)
    d.ellipse([mitte - r, int(g * 0.565) - r, mitte + r, int(g * 0.565) + r],
              fill=BLAU_UNTEN)
    d.rounded_rectangle([mitte - int(r * 0.62), int(g * 0.565),
                         mitte + int(r * 0.62), int(g * 0.725)],
                        radius=int(r * 0.5), fill=BLAU_UNTEN)

    return bild.resize((kante, kante), Image.LANCZOS)


def main():
    ziel = Path(__file__).resolve().parent / "vp4.ico"
    # Windows sucht sich aus diesen Größen die passende heraus
    groessen = [16, 24, 32, 48, 64, 128, 256]
    bilder = [schloss_zeichnen(k) for k in groessen]
    bilder[-1].save(ziel, format="ICO",
                    sizes=[(k, k) for k in groessen],
                    append_images=bilder[:-1])
    print(f"Icon geschrieben: {ziel}")
    print(f"Enthaltene Größen: {', '.join(f'{k}x{k}' for k in groessen)}")

    # Zusätzlich als PNG - praktisch für die Anzeige auf der GitHub-Seite
    png = ziel.with_suffix(".png")
    schloss_zeichnen(256).save(png)
    print(f"Vorschaubild: {png}")


if __name__ == "__main__":
    main()
