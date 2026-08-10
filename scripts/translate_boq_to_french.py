#!/usr/bin/env python3
"""Translate Villa Yasmina GF BOQ PDF English text to French, preserving layout 1:1."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

SRC = Path("/home/ubuntu/.cursor/projects/workspace/uploads/VILLA_YASMINA_GF_BOQ_-R1_c641.pdf")
OUT = Path("/workspace/output/VILLA_YASMINA_GF_BOQ_R1_FR.pdf")

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTNAME_REG = "liberationsans"
FONTNAME_BOLD = "liberationsans-bold"

# Exact span-string → French. Keep codes, sizes values, and numbers unchanged
# where they appear alone. Prefer similar length to avoid cell overflow.
TRANSLATIONS: dict[str, str] = {
    # Headers / cover
    "MOROCCO": "MAROC",
    "REVISION 00 ": "RÉVISION 00 ",
    "REVISION 00": "RÉVISION 00",
    "VILLA YASMINA @MOROCCO": "VILLA YASMINA @MAROC",
    "GF  -  REVISION 01": "RDC  -  RÉVISION 01",
    # Column headers
    "Rate": "Prix",
    "Amount": "Montant",
    "Item ": "N° ",
    "No": "Art.",
    "Unit": "Unité",
    "Description": "Description",
    "Qty": "Qté",
    "Element Photo": "Photo élément",
    "Item \nNo Description": "N° Art. Description",  # unlikely as single span
    # Summary
    "GRAND SUMMARY": "RÉCAPITULATIF GÉNÉRAL",
    "ART WORKS": "ŒUVRES D'ART",
    "CARPETS": "TAPIS",
    "LIGHTING": "ÉCLAIRAGE",
    "PAINT & WALLPAPER": "PEINTURE & PAPIER PEINT",
    "LOOSE FURNITURE": "MOBILIER LIBRE",
    "CURTAINS": "RIDEAUX",
    "MARBLE": "MARBRE",
    "FLOOR&WALL TILES": "CARRELAGE SOL&MUR",
    "GYPSUM BOARD": "PLÂTRE / BA13",
    "WOOD & MIRROR": "BOIS & MIROIR",
    "VAT (5%)": "TVA (5%)",
    "ALL CUSTOM DUTY AND FREIGHT": "DROITS DE DOUANE ET FRET",
    "* This is not the final price for the Customs duty and ":
        "* Ceci n'est pas le prix final pour les droits de douane et ",
    "Freight as we didn't receive the customs for most ":
        "le fret car nous n'avons pas reçu les douanes pour la plupart ",
    "items in the Loose furniture and fabrics in the Fit-":
        "des articles du mobilier libre et des tissus des travaux ",
    "out Works, it's going to be confirmed once the client ":
        "d'aménagement ; confirmation une fois que le client ",
    "confirms  which items he will purchase.":
        "confirme  les articles qu'il souhaite acheter.",
    "SCAFFOLDNG ": "ÉCHAFAUDAGE ",
    "EXECUTION AND COORDINATION": "EXÉCUTION ET COORDINATION",
    "SUB-TOTAL": "SOUS-TOTAL",
    "* This price might increase or decrease ":
        "* Ce prix peut augmenter ou diminuer ",
    "depending on what items the client wants to ":
        "selon les articles que le client souhaite ",
    "  GRAND TOTAL": "  TOTAL GÉNÉRAL",
    # Section titles
    "DINING ROOM": "SALLE À MANGER",
    "FURNITURE": "MOBILIER",
    "OFFICE": "BUREAU",
    "HAIR DRESSER": "COIFFURE",
    "FORMAL SITTING AREA": "SALON FORMEL",
    "FAMILY SITTING AREA": "SALON FAMILIAL",
    "GROUND FLOOR": "REZ-DE-CHAUSSÉE",
    "ARTWORK": "ŒUVRE D'ART",
    "RUGS": "TAPIS",
    "BATH ROOM": "SALLE DE BAIN",
    "FLOORING": "REVÊTEMENT DE SOL",
    "Flooring": "Revêtement de sol",
    "PAINT": "PEINTURE",
    "WOOD AND MIRROR": "BOIS ET MIROIR",
    "WOOD , MIRROR AND METAL": "BOIS , MIROIR ET MÉTAL",
    "HALLWAY": "COULOIR",
    # Labels
    "Total Used Fabric:": "Tissu utilisé :",
    "Size: ": "Taille : ",
    "Size:": "Taille :",
    "Size : ": "Taille : ",
    "size: ": "taille : ",
    # Furniture descriptions
    "Made of fabric (FB-00) &  painted wood ":
        "En tissu (FB-00) &  bois peint ",
    "base": "base",
    "chair padded with commercial grade non-":
        "chaise rembourrée mousse mémoire non ",
    "fire rated memory foam / upholstery.":
        "ignifuge commerciale / garnissage.",
    "Made of fabric (FB-00) with a silver metal ":
        "En tissu (FB-00) avec base métal argenté ",
    "office chair padded with commercial ":
        "chaise de bureau rembourrée mousse ",
    "grade non-fire rated memory foam / ":
        "mémoire non ignifuge commerciale / ",
    "upholstery.": "garnissage.",
    "Made of wood top, wood base (WD-01)":
        "Plateau bois, base bois (WD-01)",
    "Made of wood veneer (WD-01) & metal ":
        "En placage bois (WD-01) & métal ",
    "(MT-02)": "(MT-02)",
    "Made of wood (WD-04)top and metal(MT-":
        "En bois (WD-04) plateau et métal(MT-",
    "01) base": "01) base",
    "Made of wood (WD-01)": "En bois (WD-01)",
    "Made of fabric (FB-00) ": "En tissu (FB-00) ",
    "3 person sofa padded with commercial ":
        "Canapé 3 places rembourré mousse ",
    "CUSHION ( CU-01)": "COUSSIN ( CU-01)",
    "CUSHION ( CU-02)": "COUSSIN ( CU-02)",
    "CUSHION ( CU-03)": "COUSSIN ( CU-03)",
    "CUSHION ( CU-04)": "COUSSIN ( CU-04)",
    "CUSHION ( CU-05)": "COUSSIN ( CU-05)",
    "CUSHION ( CU-06)": "COUSSIN ( CU-06)",
    "CUSHION ( CU-07)": "COUSSIN ( CU-07)",
    "CUSHION ( CU-08)": "COUSSIN ( CU-08)",
    "Made of fabric (FB-00) with a metal base ":
        "En tissu (FB-00) avec base métallique ",
    "hair dresser chair padded with ":
        "chaise coiffeuse rembourrée avec ",
    "commercial grade non-fire rated memory ":
        "mousse mémoire non ignifuge ",
    "foam / upholstery.": "commerciale / garnissage.",
    "arm chair padded with commercial grade ":
        "fauteuil rembourré mousse mémoire ",
    "non-fire rated memory foam / upholstery.":
        "non ignifuge commerciale / garnissage.",
    "Made of wood veneer base (WD-01) with ":
        "Base placage bois (WD-01) avec ",
    "wood veneer top": "plateau placage bois",
    "4 person sofa padded with commercial ":
        "Canapé 4 places rembourré mousse ",
    "6 person sofa padded with commercial ":
        "Canapé 6 places rembourré mousse ",
    "5 person sofa padded with commercial ":
        "Canapé 5 places rembourré mousse ",
    "Made of wood veneer (WD-01) ":
        "En placage bois (WD-01) ",
    "Made of wood veneer (WD-01)":
        "En placage bois (WD-01)",
    "Made of wood veneer base & top (WD-":
        "Base & plateau placage bois (WD-",
    "01) ": "01) ",
    "Made of metal base (MTL-02) with ":
        "Base métal (MTL-02) avec ",
    "marble top (MR-02) ": "plateau marbre (MR-02) ",
    "bench padded with commercial grade ":
        "banc rembourré mousse mémoire ",
    "Made of marble  base (MR-01)  with ":
        "Base marbre  (MR-01)  avec ",
    "wood veneer top (WD-01)":
        "plateau placage bois (WD-01)",
    "Made of painted wood (WPT-08) ":
        "En bois peint (WPT-08) ",
    "Made of fabric (FB-00) &  wood veneer ":
        "En tissu (FB-00) &  placage bois ",
    "base (WD-01) ": "base (WD-01) ",
    # Artwork
    "Art work placed in office ":
        "Œuvre d'art placée au bureau ",
    "Art work placed in hallway":
        "Œuvre d'art placée dans le couloir",
    "Art work placed in formal sitting":
        "Œuvre d'art placée au salon formel",
    "Art work placed in family sitting area ":
        "Œuvre d'art placée au salon familial ",
    "Art work placed in washroom":
        "Œuvre d'art placée dans les WC",
    "Art work placed in hair dresser":
        "Œuvre d'art placée à la coiffure",
    # Rugs
    "loose carpet": "tapis libre",
    "placed in entrance": "placé à l'entrée",
    "placed in dining": "placé en salle à manger",
    "placed in hallway": "placé dans le couloir",
    "placed in formal sitting area": "placé au salon formel",
    "placed in family sitting": "placé au salon familial",
    "placed in family sitting area": "placé au salon familial",
    # Curtains
    "TWO-WAY CURTAINS": "RIDEAUX DOUBLE SENS",
    "Supply and installation": "Fourniture et pose",
    "Window: W 240cm x H 300cm": "Fenêtre : L 240cm x H 300cm",
    "Window: W 600cm x H 300cm": "Fenêtre : L 600cm x H 300cm",
    "Window: W 370cm x H 300cm": "Fenêtre : L 370cm x H 300cm",
    "Curtain Box Width : ": "Largeur caisson rideau : ",
    "Wavy Rails + accessories + Knitting + ":
        "Rails ondulés + accessoires + tricot + ",
    "installation": "pose",
    "CUR-00 (Main Fabric)FB-00": "CUR-00 (Tissu principal)FB-00",
    "SH-00(Sheer )FB-00": "SH-00(Voilage )FB-00",
    "ROLLER CURTAINS": "STORES ENROULEURS",
    "curtain : W 60cm x H 280cm": "rideau : L 60cm x H 280cm",
    # Lighting
    "CEILING DIRECT SPOT LIGHT S1": "SPOT PLAFOND DIRECT S1",
    "CEILING DIRECT SPOT LIGHT S2": "SPOT PLAFOND DIRECT S2",
    "CEILING DIRECT SPOT LIGHT S3": "SPOT PLAFOND DIRECT S3",
    "CEILING DIRECT SPOT LIGHT S4": "SPOT PLAFOND DIRECT S4",
    " DIRECT SPOT LIGHT UX1": " SPOT DIRECT UX1",
    "Details : 15 °": "Détails : 15 °",
    "Details : 25 °": "Détails : 25 °",
    "Details : 40 °": "Détails : 40 °",
    "Details : 50 °": "Détails : 50 °",
    "Details : 10 °": "Détails : 10 °",
    "Details : 35 °": "Détails : 35 °",
    "Tube Spot Small SB2": "Tube Spot Petit SB2",
    "Tube Spot Small SB3": "Tube Spot Petit SB3",
    "CEILING INDIRECT LIGHT ": "ÉCLAIRAGE INDIRECT PLAFOND ",
    "LED indirect Lights Roll 10W in cladding":
        "Bande LED indirecte 10W dans le bardage",
    "PENDENT LIGHT (LIGHT-01)": "SUSPENSION (LIGHT-01)",
    "Size: 46cm dia": "Taille : 46cm dia",
    "Size: 30cm dia": "Taille : 30cm dia",
    "chain length : 70cm": "longueur chaîne : 70cm",
    "CLADDING INDIRECT LIGHT ": "ÉCLAIRAGE INDIRECT BARDAGE ",
    "LED indirect Lights Roll 5W in cladding":
        "Bande LED indirecte 5W dans le bardage",
    # Marble / flooring / paint
    "MARBLE COUNTER TOP (ST-01)": "PLAN DE TRAVAIL MARBRE (ST-01)",
    "Supply and installation of marble (ST-01) as ":
        "Fourniture et pose de marbre (ST-01) comme ",
    "shown in picture with structure":
        "montré sur la photo avec structure",
    "COUNTER TOP & CLADDING (ST-01)": "PLAN DE TRAVAIL & HABILLAGE (ST-01)",
    "supply of marble (ST-01) as shown in ":
        "fourniture de marbre (ST-01) comme montré ",
    "picture with structure": "sur la photo avec structure",
    "To SKIRTING": "PLINTHE",
    "Supply and installation of skirting with ":
        "Fourniture et pose de plinthe de ",
    "10cm height same as design & drawing":
        "hauteur 10cm selon design & plans",
    "VINYL FLOORING (VT-01)": "SOL VINYLE (VT-01)",
    "Supply and installation of Vinyl floor same ":
        "Fourniture et pose de sol vinyle selon ",
    "as design & drawing": "design & plans",
    "WALL & FLOORING (TL-01)": "MUR & SOL (TL-01)",
    "Supply and installation of TILES for ":
        "Fourniture et pose de CARRELAGE pour ",
    "washroom same as design & drawing":
        "salle d'eau selon design & plans",
    "To WALL (SP-01) &To CEILING (SP-01)":
        "MUR (SP-01) & PLAFOND (SP-01)",
    "supply and installation of a Special Paint on ":
        "fourniture et pose d'une peinture spéciale sur ",
    "walls same as design & drawing":
        "murs selon design & plans",
    "To CEILING (SP-01 A)": "PLAFOND (SP-01 A)",
    "ceiling same as design & drawing":
        "plafond selon design & plans",
    # Gypsum
    "Gypsum Board": "Plaque de plâtre",
    "Gypsum board Ceiling": "Plafond en plaque de plâtre",
    "supply & installation of gypsum board ":
        "fourniture & pose de plaque de plâtre ",
    "for ceiling with shadow gap same as ":
        "pour plafond avec joint d'ombre selon ",
    "design & drawing": "design & plans",
    "Bulkhead Curtain + indirect light ":
        "Caisson rideau + éclairage indirect ",
    "supply & installation of gypsum board  ":
        "fourniture & pose de plaque de plâtre  ",
    "for bulkhead curtain H 20cm same as ":
        "pour caisson rideau H 20cm selon ",
    "wooden support ": "support bois ",
    "Bulkhead Ceiling design": "Caisson plafond design",
    "for bulkhead ceiling design same as ":
        "pour caisson plafond design selon ",
    # Wood & mirror
    "MIRROR (MR-01)": "MIROIR (MR-01)",
    "supply and installation of bronze mirror with ":
        "fourniture et pose de miroir bronze avec ",
    "2cm black metal frame around it on MDF ":
        "cadre métal noir 2cm sur panneau MDF ",
    "board behind it same as design & drawing":
        "derrière selon design & plans",
    "WOOD VENEER CONSOLE (WD-01)": "CONSOLE PLACAGE BOIS (WD-01)",
    "supply and installation of wood veneer ":
        "fourniture et pose de placage bois ",
    "console (WD-01) with GL-01 Glass shutters ":
        "console (WD-01) avec portes verre GL-01 ",
    "structure same as design & drawing":
        "structure selon design & plans",
    "WOOD VENEER DINING TABLE (WD-02)": "TABLE À MANGER PLACAGE (WD-02)",
    "supply and installation of wood veneer dining ":
        "fourniture et pose de table à manger en ",
    "table (WD-02) with structure same as design ":
        "placage (WD-02) avec structure selon design ",
    "& drawing": "& plans",
    "SILVER MIRROR  WITH FRAME": "MIROIR ARGENTÉ  AVEC CADRE",
    "supply and installation of silver mirror with ":
        "fourniture et pose de miroir argenté avec ",
    "2cm bronze stainless steel frame around it on ":
        "cadre inox bronze 2cm autour sur ",
    "MDF board behind it same as design & ":
        "panneau MDF derrière selon design & ",
    "drawing": "plans",
    "Number of mirrors : 1": "Nombre de miroirs : 1",
    "WOODEN DOOR (90CM)": "PORTE BOIS (90CM)",
    "supply and installation of wooden door made ":
        "fourniture et pose de porte en bois faite ",
    "of wood veneer (WD-01) same as design & ":
        "de placage bois (WD-01) selon design & ",
    "VANITY COUNTER": "MEUBLE VASQUE",
    "supply and installation of Vanity made of ":
        "fourniture et pose de meuble vasque en ",
    "wood veneer (WD-01) same as design & ":
        "placage bois (WD-01) selon design & ",
    "SHELVES WD-01": "ÉTAGÈRES WD-01",
    "supply and installation of shelves made of ":
        "fourniture et pose d'étagères en ",
    "SILVER MIRROR ": "MIROIR ARGENTÉ ",
    "supply and installation of silver mirroron MDF ":
        "fourniture et pose de miroir argenté sur MDF ",
    "WOOD VENEER DRESSER (WD-01)": "COIFFEUSE PLACAGE BOIS (WD-01)",
    "dresser (WD-01) with metal base (MTL-02) & ":
        "coiffeuse (WD-01) avec base métal (MTL-02) & ",
    "WOOD VENEER SHELVES (WD-01)": "ÉTAGÈRES PLACAGE BOIS (WD-01)",
    "shelves (WD-01) with place for indirect light & ":
        "étagères (WD-01) avec emplacement lumière indirecte & ",
    "WOODEN DOOR (100CM)": "PORTE BOIS (100CM)",
    "SLIDING DOOR (220CM)": "PORTE COULISSANTE (220CM)",
    "supply and installation of sliding door made of ":
        "fourniture et pose de porte coulissante en ",
    "wood veneer (WD-01) in 2 parts slidding side ":
        "placage bois (WD-01) en 2 parties côté coulissant ",
    "140cm wide and 80cm fixed side and 5cm ":
        "140cm et côté fixe 80cm avec cadre 5cm ",
    "frame with structure same as design & ":
        "avec structure selon design & ",
    "ENTRANCE WOODEN DOOR (140CM)": "PORTE D'ENTRÉE BOIS (140CM)",
    "supply and installation of wooden main door ":
        "fourniture et pose de porte principale en bois ",
    "made of wood veneer (WD-01) same as ":
        "en placage bois (WD-01) selon ",
    "SHELVES": "ÉTAGÈRES",
    "SHELVES ": "ÉTAGÈRES ",
    "supply and installation of wood shelf structure ":
        "fourniture et pose de structure d'étagère bois ",
    "same as design & drawing": "selon design & plans",
    "WOOD CABINETS (WD-01)": "PLACARDS BOIS (WD-01)",
    "cabinets (WD-01) with structure same as ":
        "placards (WD-01) avec structure selon ",
    "design & drawing": "design & plans",
    "supply and installation of wood cabinets (WD-":
        "fourniture et pose de placards bois (WD-",
    "02) with structure same as design & drawing":
        "02) avec structure selon design & plans",
    "WALL CLADDING (MR-02)": "HABILLAGE MURAL (MR-02)",
    "supply and installation of tinted mirror (MR-":
        "fourniture et pose de miroir teinté (MR-",
    # Size prefixes (partial replacements handled below too)
    "Size: W50cm x D55cm x H80cm": "Taille : L50cm x P55cm x H80cm",
    "Size: W76cm x D78cm x H110cm": "Taille : L76cm x P78cm x H110cm",
    "Size: W180cm x D80cm x H75cm": "Taille : L180cm x P80cm x H75cm",
    "Size: W30cm DIA x H60cm": "Taille : L30cm DIA x H60cm",
    "Size: DIA40cm x H45cm": "Taille : DIA40cm x H45cm",
    "Size: W220cm x D40cm x H60cm": "Taille : L220cm x P40cm x H60cm",
    "Size: W240cm x D100cm x H75cm": "Taille : L240cm x P100cm x H75cm",
    "Size: W45cm x D10cm x H45cm": "Taille : L45cm x P10cm x H45cm",
    "Size: W65cm x D68cm x H95cm": "Taille : L65cm x P68cm x H95cm",
    "Size: W98cm x D86cm x H75cm": "Taille : L98cm x P86cm x H75cm",
    "Size: R:50cm x H:45cm": "Taille : R:50cm x H:45cm",
    "Size: W300cm x D110cm x H80cm": "Taille : L300cm x P110cm x H80cm",
    "Size: W200cm x D110cm x H80cm": "Taille : L200cm x P110cm x H80cm",
    "Size: W80cm x D74cm x H70cm": "Taille : L80cm x P74cm x H70cm",
    "Size: W462cm x D110cm x H80cm": "Taille : L462cm x P110cm x H80cm",
    "Size: W45cm x D30cm x H45cm": "Taille : L45cm x P30cm x H45cm",
    "Size: W60cm x D20cm x H40cm": "Taille : L60cm x P20cm x H40cm",
    "Size: R:24cm x H:55cm": "Taille : R:24cm x H:55cm",
    "Size: W75cm x D45cm x H55cm": "Taille : L75cm x P45cm x H55cm",
    "Size: W200cm x D110cm x H45cm": "Taille : L200cm x P110cm x H45cm",
    "Size: W300cm x D110cm x H45cm": "Taille : L300cm x P110cm x H45cm",
    "Size: W250cm x D32cm x H75cm": "Taille : L250cm x P32cm x H75cm",
    "Size: W100cm x D93cm x H70cm": "Taille : L100cm x P93cm x H70cm",
    "Size: W370cm x D450cm x H75cm": "Taille : L370cm x P450cm x H75cm",
    "Size: W280cm x D107cm x H85cm": "Taille : L280cm x P107cm x H85cm",
    "Size: W250cm x D73cm x H45cm": "Taille : L250cm x P73cm x H45cm",
    "Size: W210cm x D120cm x H35cm": "Taille : L210cm x P120cm x H35cm",
    "Size: DIA 60cm x H55cm": "Taille : DIA 60cm x H55cm",
    "Size: DIA150cm x H75cm": "Taille : DIA150cm x H75cm",
    "Size: W65cm x D20cm x H45cm": "Taille : L65cm x P20cm x H45cm",
    "Size: W45cm x D20cm x H45cm": "Taille : L45cm x P20cm x H45cm",
    "Size: W45cm x D52cm x H85cm": "Taille : L45cm x P52cm x H85cm",
    "Size: W250cm x D44cm x H75cm": "Taille : L250cm x P44cm x H75cm",
    "Size:W170cm x H100cm": "Taille :L170cm x H100cm",
    "Size:W240cm x H 160cm": "Taille :L240cm x H 160cm",
    "Size:W240cm x H 140cm": "Taille :L240cm x H 140cm",
    "Size:W80cm x H 120cm": "Taille :L80cm x H 120cm",
    "Size:W100cm x H 150cm": "Taille :L100cm x H 150cm",
    "size: W 340cm x 150cm": "taille : L 340cm x 150cm",
    "size: W 290cm x 420cm": "taille : L 290cm x 420cm",
    "size: W 370cm x 210cm": "taille : L 370cm x 210cm",
    "size: W 1000cm x 320cm": "taille : L 1000cm x 320cm",
    "size: W 340cm x 390cm": "taille : L 340cm x 390cm",
    "size: DIA 270cm": "taille : DIA 270cm",
    "Size: W:295cm x D:60cm x H:5cm": "Taille : L:295cm x P:60cm x H:5cm",
    "Size : W:380cm x H:280cm": "Taille : L:380cm x H:280cm",
    "Size : W360cm x D:44cm x H:90cm ": "Taille : L360cm x P:44cm x H:90cm ",
    "Size : W295cm x D:140cm x H:75cm ": "Taille : L295cm x P:140cm x H:75cm ",
    "Size : W:260cm x H:100cm": "Taille : L:260cm x H:100cm",
    "Size : W:90cm x H: 280cm ": "Taille : L:90cm x H: 280cm ",
    "Size : W:295cm x H: 75cm x D: 60cm": "Taille : L:295cm x H: 75cm x P: 60cm",
    "Size : W:238cm x H: 234cm x D: 38cm": "Taille : L:238cm x H: 234cm x P: 38cm",
    "Size : W:140cm x H:280cm": "Taille : L:140cm x H:280cm",
    "Size : W308cm x D:60cm x H:15cm ": "Taille : L308cm x P:60cm x H:15cm ",
    "Size : W43cm x D:30cm x H:280cm ": "Taille : L43cm x P:30cm x H:280cm ",
    "Size : W:100cm x H: 280cm ": "Taille : L:100cm x H: 280cm ",
    "Size : W:220cm x H: 280cm ": "Taille : L:220cm x H: 280cm ",
    "Size : W:140cm x H: 280cm ": "Taille : L:140cm x H: 280cm ",
    "Size : W710cm x D:75cm x H:280cm ": "Taille : L710cm x P:75cm x H:280cm ",
    "Size : W170cm x D:31cm x H:230cm ": "Taille : L170cm x P:31cm x H:230cm ",
    "Size : W:520cm x D:60cm x H:90cm ": "Taille : L:520cm x P:60cm x H:90cm ",
    "Size : W:280cm x D:40cm x H:110cm ": "Taille : L:280cm x P:40cm x H:110cm ",
    "Size : W:450cm x H:270cm ": "Taille : L:450cm x H:270cm ",
    # Units commonly used in FR BOQ
    "NO": "U",
    "LM": "ML",
    "M2": "M2",
    "M²": "M²",
}


def int_color_to_rgb(color: int) -> tuple[float, float, float]:
    r = ((color >> 16) & 255) / 255
    g = ((color >> 8) & 255) / 255
    b = (color & 255) / 255
    return (r, g, b)


def sample_fill(
    page: pymupdf.Page,
    bbox: pymupdf.Rect,
    pix: pymupdf.Pixmap,
    text_rgb: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Infer cell background; avoid sampling black grid lines or glyph ink."""
    x0, y0, x1, y1 = bbox
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    candidates = [
        (cx, y0 - 1.5),
        (cx, y1 + 1.5),
        (x1 + 2, cy),
        (x0 + max(4, (x1 - x0) * 0.15), y0 - 1),
        (cx, cy),
        (x0 + 4, cy),
        (x1 - 4, cy),
    ]
    samples: list[tuple[int, int, int]] = []
    for sx, sy in candidates:
        ix = max(0, min(int(round(sx)), pix.width - 1))
        iy = max(0, min(int(round(sy)), pix.height - 1))
        pixel = pix.pixel(ix, iy)
        if len(pixel) >= 3:
            samples.append((pixel[0], pixel[1], pixel[2]))
    if not samples:
        return (1, 1, 1)

    def lum(rgb: tuple[int, int, int]) -> float:
        return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

    text_lum = 0.299 * text_rgb[0] * 255 + 0.587 * text_rgb[1] * 255 + 0.114 * text_rgb[2] * 255

    if text_lum > 180:  # white / light text → need colored/dark fill
        dark = [s for s in samples if lum(s) < 220]
        pick = min(dark or samples, key=lum)
    else:  # dark text → need light / yellow fill; ignore black borders & ink
        light = [s for s in samples if lum(s) > 80]
        if not light:
            light = samples
        # Prefer yellow-ish if present (common category rows)
        yellow = [s for s in light if s[0] > 200 and s[1] > 200 and s[2] < 120]
        if yellow:
            pick = max(yellow, key=lambda s: s[0] + s[1] - s[2])
        else:
            pick = max(light, key=lum)
    return (pick[0] / 255, pick[1] / 255, pick[2] / 255)


def translate_span(text: str) -> str | None:
    """Return French replacement, or None if no change needed."""
    if text in TRANSLATIONS:
        fr = TRANSLATIONS[text]
        return fr if fr != text else None
    # Pattern-based for Size lines not listed
    m = re.match(r"^(Size|size)(\s*:?\s*)(.*)$", text)
    if m and "Size" in m.group(1) or (m and m.group(1) == "size"):
        rest = m.group(3)
        # W → L (largeur), D → P (profondeur) when used as dimension labels
        rest2 = re.sub(r"\bW\s*:", "L:", rest)
        rest2 = re.sub(r"\bW\s+", "L ", rest2)
        rest2 = re.sub(r"\bD\s*:", "P:", rest2)
        rest2 = re.sub(r"\bD\s+", "P ", rest2)
        prefix = "Taille" if m.group(1) == "Size" else "taille"
        return f"{prefix}{m.group(2)}{rest2}"
    return None


def fontname_for(span_font: str, flags: int) -> str:
    bold = bool(flags & pymupdf.TEXT_FONT_BOLD) or "Bold" in span_font
    return FONTNAME_BOLD if bold else FONTNAME_REG


def process(src: Path, out: Path) -> None:
    doc = pymupdf.open(src)
    replaced = 0
    skipped = 0
    missing: set[str] = set()

    for page in doc:
        # Register embedded fonts that support French Unicode on every page
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        # Rasterize at 1x for fill sampling (page coords == pixel coords)
        pix = page.get_pixmap(matrix=pymupdf.Identity, alpha=False)
        d = page.get_text("dict")
        jobs = []
        for block in d["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    if not text.strip():
                        continue
                    fr = translate_span(text)
                    if fr is None:
                        # Track English-looking spans that we left alone
                        if re.search(r"[A-Za-z]{3,}", text) and text not in (
                            "VILLA YASMINA ",
                            "AED",
                            "#REF!",
                            "Description",
                        ):
                            # codes like CHAIR-01, FB-00, WD-01 kept intentionally
                            if re.fullmatch(
                                r"[\s\(\)A-Z0-9\-_/\.]+",
                                text,
                            ) and any(
                                k in text
                                for k in (
                                    "CHAIR",
                                    "TABLE",
                                    "SOFA",
                                    "CONSOLE",
                                    "ARTWORK",
                                    "RUG",
                                    "CU-",
                                    "FB-",
                                    "WD-",
                                    "MT-",
                                    "MR-",
                                    "ST-",
                                    "VT-",
                                    "TL-",
                                    "SP-",
                                    "MTL-",
                                    "WPT-",
                                    "GL-",
                                    "LIGHT-",
                                    "CUR-",
                                    "SH-",
                                    "CH-",
                                    "F1",
                                    "F2",
                                    "F3",
                                    "F4",
                                    "F5",
                                    "F6",
                                    "F7",
                                    "F8",
                                    "F9",
                                    "F10",
                                    "F11",
                                    "L1",
                                    "L2",
                                    "L3",
                                    "L4",
                                    "L5",
                                    "L6",
                                    "L7",
                                    "L8",
                                    "L9",
                                    "L10",
                                    "L11",
                                    "A1",
                                    "A2",
                                    "A3",
                                    "A4",
                                    "A5",
                                    "A6",
                                    "C1",
                                    "C2",
                                    "C3",
                                    "C4",
                                    "C5",
                                    "C6",
                                    "PA1",
                                    "PA2",
                                    "FL1",
                                    "FL2",
                                    "FL3",
                                    "GP1",
                                    "GP2",
                                    "GP3",
                                    "MR1",
                                    "MR2",
                                    "WD1",
                                    "WD2",
                                    "WD3",
                                    "WD4",
                                    "WD-1",
                                    "MI",
                                    "SB2",
                                    "SB3",
                                    "UX1",
                                    "S1",
                                    "S2",
                                    "S3",
                                    "S4",
                                )
                            ):
                                skipped += 1
                                continue
                            if re.fullmatch(r"[A-N]", text):
                                skipped += 1
                                continue
                            if re.fullmatch(r"\d+(\.\d+)?\s*W?", text):
                                skipped += 1
                                continue
                            if re.fullmatch(r"\d+\s*-\s*\d+", text):
                                skipped += 1
                                continue
                            if text.strip() in {"²", "base", "01) base", "base (WD-01) "}:
                                skipped += 1
                                continue
                            missing.add(text)
                        skipped += 1
                        continue
                    bbox = pymupdf.Rect(span["bbox"])
                    text_color = int_color_to_rgb(span["color"])
                    fill = sample_fill(page, bbox, pix, text_color)
                    jobs.append(
                        {
                            "bbox": bbox,
                            "fr": fr,
                            "size": span["size"],
                            "font": fontname_for(span["font"], span["flags"]),
                            "fill": fill,
                            "color": text_color,
                            "origin": span.get("origin", (bbox.x0, bbox.y1 - 1)),
                        }
                    )

        # Apply redactions first (erase), then rewrite text to keep precise baseline
        for job in jobs:
            page.add_redact_annot(job["bbox"], fill=job["fill"], cross_out=False)
        if jobs:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

        # Re-register fonts after redactions (content stream may drop unused fonts)
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        for job in jobs:
            x, y = job["origin"]
            if isinstance(x, (int, float)):
                point = pymupdf.Point(x, y)
            else:
                point = pymupdf.Point(job["bbox"].x0, job["bbox"].y1 - 1.5)
            size = job["size"]
            fontfile = FONT_BOLD if job["font"] == FONTNAME_BOLD else FONT_REG
            font = pymupdf.Font(fontfile=fontfile)
            tw = font.text_length(job["fr"], fontsize=size)
            max_w = max(job["bbox"].width, 1)
            if tw > max_w * 1.08:
                size = max(6.0, size * (max_w / tw) * 0.98)
            page.insert_text(
                point,
                job["fr"],
                fontname=job["font"],
                fontsize=size,
                color=job["color"],
            )
            replaced += 1

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata(
        {
            "title": "VILLA YASMINA GF BOQ - R1 (FR)",
            "author": "User",
            "subject": "Traduction française — même contenu et mise en page",
            "creator": "translate_boq_to_french.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    print(f"Replaced spans: {replaced}")
    print(f"Unchanged spans: {skipped}")
    if missing:
        print(f"Possibly untranslated English spans ({len(missing)}):")
        for t in sorted(missing, key=lambda s: (-len(s), s))[:80]:
            print(f"  {repr(t)}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    process(src, out)
