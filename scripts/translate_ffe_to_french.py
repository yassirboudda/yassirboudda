#!/usr/bin/env python3
"""Translate Villa Yasmina FF&E Specification PDF to French, preserving layout 1:1."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

SRC = Path(
    "/home/ubuntu/.cursor/projects/workspace/uploads/Villa_Yasmina__Morocco_FF_E_08Sep2025_771d.pdf"
)
OUT = Path("/workspace/output/Villa_Yasmina_Morocco_FFE_FR_08Sep2025.pdf")

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTNAME_REG = "liberationsans"
FONTNAME_BOLD = "liberationsans-bold"

TRANSLATIONS: dict[str, str] = {
    # Column headers
    "CODE      ": "CODE      ",
    "MODEL": "MODÈLE",
    "PHOTO": "PHOTO",
    "COMPANY": "FOURNISSEUR",
    "DIMENSION": "DIMENSION",
    "FINISH": "FINITION",
    "AREA": "ZONE",
    "QTY": "QTÉ",
    # Titles
    "VILLA YASMINA @MOROCCO ": "VILLA YASMINA @MAROC ",
    "FF&E SPECIFICATION": "SPÉCIFICATION FF&E",
    "LOOSE FURNITURES": "MOBILIER LIBRE",
    "DECORATIVE LIGHTS": "LUMINAIRES DÉCORATIFS",
    "ARCHITECTURAL LIGHTS": "LUMINAIRES ARCHITECTURAUX",
    "RUGS": "TAPIS",
    "ARTWORKS": "ŒUVRES D'ART",
    "ARTWORK": "ŒUVRE D'ART",
    "CURTAINS & BLINDS": "RIDEAUX & STORES",
    "ACCESSORIES": "ACCESSOIRES",
    # Areas
    "GROUND FLOOR - DINING ROOM": "RDC - SALLE À MANGER",
    "GROUND FLOOR - OFFICE ROOM": "RDC - BUREAU",
    "GROUND FLOOR - FORMAL SITTING ": "RDC - SALON FORMEL ",
    "GROUND FLOOR - FAMILY SITIING ": "RDC - SALON FAMILIAL ",
    "GROUND FLOOR - FAMILY SITTING ": "RDC - SALON FAMILIAL ",
    "GROUND FLOOR -FAMILY SITTING ": "RDC - SALON FAMILIAL ",
    "GROUND FLOOR - DRESSING ROOM ": "RDC - DRESSING ",
    "GROUND FLOOR - DRESSING": "RDC - DRESSING",
    "GROUND FLOOR - ENTRANCE ": "RDC - ENTRÉE ",
    "GROUND FLOOR - HALLWAY": "RDC - COULOIR",
    "GROUND FLOOR - BATHROOM": "RDC - SALLE DE BAIN",
    "GROUND FLOOR - GYM": "RDC - SALLE DE SPORT",
    "GROUND FLOOR - STAIR AREA": "RDC - ZONE ESCALIER",
    "GROUND FLOOR - DINING ROOM, ": "RDC - SALLE À MANGER, ",
    "GROUND FLOOR - DINING ": "RDC - SALLE À MANGER ",
    "ROOM/HALLWAY": "COULOIR",
    "FAMILY SITTING AREA": "SALON FAMILIAL",
    "AREA / PANTRY": "ZONE / OFFICE",
    "AREA/PANTRY": "ZONE/OFFICE",
    "AREA / HALLWAY": "ZONE / COULOIR",
    "HALLWAY": "COULOIR",
    "FIRST FLOOR - FAMILY SITIING AREA ": "1ER ÉTAGE - SALON FAMILIAL ",
    "FIRST FLOOR - HALLWAY": "1ER ÉTAGE - COULOIR",
    "FIRST FLOOR - MASTER SITIING ": "1ER ÉTAGE - SALON MASTER ",
    "FIRST FLOOR - MASTER SITTING": "1ER ÉTAGE - SALON MASTER",
    "FIRST FLOOR - MASTER BEDROOM": "1ER ÉTAGE - CHAMBRE MASTER",
    "FIRST FLOOR - TYPICAL BEDROOMS 1 - ": "1ER ÉTAGE - CHAMBRES TYPES 1 - ",
    "FIRST FLOOR -TYPICAL BEDROOMS": "1ER ÉTAGE - CHAMBRES TYPES",
    "FIRST FLOOR - TYPICAL BEDROOMS": "1ER ÉTAGE - CHAMBRES TYPES",
    "FIRST FLOOR - MASTER BATHROOM": "1ER ÉTAGE - SDB MASTER",
    "FIRST FLOOR - TYPICAL BATHROOMS": "1ER ÉTAGE - SDB TYPES",
    "5 ": "5 ",
    # Common labels
    "DIMENSIONS:": "DIMENSIONS :",
    "DIMENSIONS": "DIMENSIONS",
    "OVERALL DIMENSIONS:": "DIMENSIONS GLOBALES :",
    "OVERALL DIMENSIONS": "DIMENSIONS GLOBALES",
    "OVERALL:": "GLOBAL :",
    "SEAT DIMENSIONS:": "DIMENSIONS ASSISE :",
    "Height: 780mm": "Hauteur : 780mm",
    "Depth: 540mm": "Profondeur : 540mm",
    "Width: 510mm": "Largeur : 510mm",
    "Seat height: 480mm": "Hauteur assise : 480mm",
    "Height: 750mm": "Hauteur : 750mm",
    "Length: 2950mm": "Longueur : 2950mm",
    "Width: 1400mm": "Largeur : 1400mm",
    "Height: 440mm": "Hauteur : 440mm",
    "Depth: 350mm": "Profondeur : 350mm",
    "Height: 2420 L x 1080 D x 820 H (mm)": "Hauteur : 2420 L x 1080 P x 820 H (mm)",
    "Height: 42 cm": "Hauteur : 42 cm",
    "FRAME: BRASS": "STRUCTURE : LAITON",
    "FABRIC: TOFFEE": "TISSU : TOFFEE",
    "FABRIC: VILLA NOVA ": "TISSU : VILLA NOVA ",
    "FABRIC: ": "TISSU : ",
    "FABRIC: VILLA NOVA": "TISSU : VILLA NOVA",
    "FABRIC: WHITE, CHUNKY BOUCLE": "TISSU : BLANC, BOUCLÉ ÉPAIS",
    "TOP & BASE: ": "PLATEAU & BASE : ",
    " DARK GREY OAK": " CHÊNE GRIS FONCÉ",
    "DARK GREY ": "GRIS FONCÉ ",
    "OAK": "CHÊNE",
    "LEGS: BEECHWOOD LEGS": "PIEDS : PIEDS EN HÊTRE",
    "DINING TABLE - CUSTOM ": "TABLE À MANGER - SUR ",
    "MADE": "MESURE",
    "BY CONTRACTOR": "PAR L'ENTREPRENEUR",
    "FRANKA DINING CHAIR": "CHAISE FRANK A SALLE À MANGER",
    # Fix FRANKA - keep brand
    # Actually keep product names more carefully below
    "1750 SOFA - SOFA 242 CM": "CANAPÉ 1750 - CANAPÉ 242 CM",
    "TECNI NOVA - DELUXE ": "TECNI NOVA - DELUXE ",
    "FURNISHING": "AMEUBLEMENT",
    "OAK SOLID WOOD RATTAN  ": "RATTAN BOIS CHÊNE MASSIF  ",
    "FOUR DRAWER TV CABINET ": "MEUBLE TV QUATRE TIROIRS ",
    "SMOKED": "FUMÉ",
    "RATTAN FINISH TO BE STAINED TO MATCH THE FINISH ":
        "FINITION RATTAN À TEINTER POUR CORRESPONDRE ",
    "AS IN THE RENDERS/3D": "AUX RENDUS/3D",
    "NERO WHITE MARBLE ": "MARBRE BLANC NERO ",
    "ROUND ACCENT TABLE": "TABLE D'APPOINT RONDE",
    "HEIGHT: 25 IN": "HAUTEUR : 25 IN",
    "DIAMETER: 19 IN": "DIAMÈTRE : 19 IN",
    "FLOOR TO APRON": "SOL AU TABLIER",
    "HEIGHT: 24.25 IN": "HAUTEUR : 24.25 IN",
    "BASE DIAMETER: 12 IN": "DIAMÈTRE BASE : 12 IN",
    "SOLID WHITE MARBLE TOP": "PLATEAU MARBRE BLANC MASSIF",
    "WEIGHTED CAST ALUMINUM BASE WITH BRASS ":
        "BASE ALUMINIUM COULÉ LESTÉE AVEC LAITON ",
    "POWDERCOAT FINISH": "FINITION POUDRE",
    "PROST SMALL METAL ": "PETITE TABLE MÉTAL PROST ",
    "ROUND DRINK TABLE": "TABLE À BOISSONS RONDE",
    "WIDTH: 12 IN": "LARGEUR : 12 IN",
    "DEPTH: 12 IN": "PROFONDEUR : 12 IN",
    "HEIGHT: 19.5 IN": "HAUTEUR : 19.5 IN",
    "ALUMINUM TOP AND CAST-ALUMINUM BASE":
        "PLATEAU ALUMINIUM ET BASE ALUMINIUM COULÉ",
    "IRON COLUMN": "COLONNE EN FER",
    "ANTIQUED FINISH": "FINITION ANTIQUAIRE",
    "WIDTH: 154.94CM": "LARGEUR : 154.94CM",
    "HEIGHT: 76.2CM": "HAUTEUR : 76.2CM",
    "DEPTH: 76.2CM": "PROFONDEUR : 76.2CM",
    "MERMELADA ESTUDIOFIBERSTONE, A COMPOSITE ":
        "MERMELADA ESTUDIO FIBERSTONE, COMPOSITE ",
    "MATERIAL, WITH SATIN BLACK RESIN COATING":
        "AVEC REVÊTEMENT RÉSINE NOIR SATINÉ",
    "CATERINA NATURAL ": "CATERINA NATUREL ",
    "UPHOLSTERED OFFICE CHAIR ": "CHAISE DE BUREAU GARNIE ",
    "WITH BRASS BASE": "AVEC BASE LAITON",
    "WIDTH: 68.0 CM": "LARGEUR : 68.0 CM",
    "DEPTH: 65.0 CM": "PROFONDEUR : 65.0 CM",
    "HEIGHT: 79.5 CM": "HAUTEUR : 79.5 CM",
    "HEIGHT: 44.98 CM": "HAUTEUR : 44.98 CM",
    "TUBULAR IRON FRAME AND BASE WITH BURNISHED ":
        "STRUCTURE ET BASE FER TUBULAIRE BRUNI ",
    "BRASS FINISH": "FINITION LAITON",
    "POLYESTER FABRIC": "TISSU POLYESTER",
    "CUSTOM MADE SOFA ": "CANAPÉ SUR MESURE ",
    "6 PERSON SOFA PADDED WITH COMMERCIAL GRADE ":
        "CANAPÉ 6 PLACES REMBOURRÉ MOUSSE ",
    "NON-FIRE RATED MEMORY FOAM / UPHOLSTERY ":
        "MÉMOIRE NON IGNIFUGE / GARNISSAGE ",
    "FABRIC - MJ TESSUTI": "TISSU - MJ TESSUTI",
    "COLOR 04": "COULEUR 04",
    "COLOR -01": "COULEUR -01",
    "SLOU ARMCHAIR - APRILLA ": "FAUTEUIL SLOU - APRILLA ",
    "WIDTH: 100 CM": "LARGEUR : 100 CM",
    "DEPTH: 85 CM": "PROFONDEUR : 85 CM",
    "HEIGHT: 73 CM": "HAUTEUR : 73 CM",
    "SEAT WIDTH: 48 CM": "LARGEUR ASSISE : 48 CM",
    "SEAT DEPTH: 56 CM": "PROFONDEUR ASSISE : 56 CM",
    "SEAT HEIGHT: 45 CM": "HAUTEUR ASSISE : 45 CM",
    "FRAME: CALIBRATED SOFTWOOD TIMBER, BIRCH ":
        "STRUCTURE : BOIS RÉSINEUX CALIBRÉ, BOULEAU ",
    "PLYWOOD": "CONTREPLAQUÉ",
    "UPHOLSTERY: VILLA NOVA": "GARNISSAGE : VILLA NOVA",
    "WILLY CHARCOAL BROWN ": "WILLY MARRON CHARBON ",
    "ROUND PEDESTAL SIDE ": "TABLE D'APPOINT PIÉDESTAL ",
    "TABLE BY LEANNE FORD": "RONDE PAR LEANNE FORD",
    "WIDTH: 16.5 IN": "LARGEUR : 16.5 IN",
    "DEPTH: 16.5 IN": "PROFONDEUR : 16.5 IN",
    "HEIGHT: 22 IN": "HAUTEUR : 22 IN",
    "TABLE TOP THICKNESS": "ÉPAISSEUR PLATEAU",
    "WIDTH: 1.5 IN": "LARGEUR : 1.5 IN",
    "CONCRETE, STONE, SAND, METAL AND ADDITIVE":
        "BÉTON, PIERRE, SABLE, MÉTAL ET ADDITIF",
    "CUSTOM MADE COFFEE ": "TABLE BASSE SUR ",
    "TABLE ": "MESURE ",
    "TABLE": "TABLE",
    "TABLE 1 - 170W X 110L X 45H CM": "TABLE 1 - 170L X 110P X 45H CM",
    "TABLE 2 - 120W X 110L X 45H CM": "TABLE 2 - 120L X 110P X 45H CM",
    "TOP: ": "PLATEAU : ",
    "BASE: BRUSHED BLACK STAINLESS STEEL":
        "BASE : ACIER INOX NOIR BROSSÉ",
    "AVERY MODULAR SOFA": "CANAPÉ MODULAIRE AVERY",
    "LOOM COLLECTION": "COLLECTION LOOM",
    "DIMENSIONS: 340CM L X 91CM W X 79CM H":
        "DIMENSIONS : 340CM L X 91CM LARG X 79CM H",
    "SEAT HEIGHT: APPROX. 46CM": "HAUTEUR ASSISE : ENV. 46CM",
    "SEAT DEPTH: APPROX. 63CM": "PROFONDEUR ASSISE : ENV. 63CM",
    "ARM HEIGHT: 73CM": "HAUTEUR BRAS : 73CM",
    "FRAME: ENGINEERED HARDWOOD PINE WOOD ":
        "STRUCTURE : BOIS DE PIN TECHNIQUE ",
    "FRAME": "STRUCTURE",
    "TO BE REUPHOLSTERED TO: VILLA NOVA ":
        "À REGARNIR EN : VILLA NOVA ",
    "AVERY 2 SEATER": "AVERY 2 PLACES",
    "DIMENSIONS: 180CM L X 91CM W X 79CM H":
        "DIMENSIONS : 180CM L X 91CM LARG X 79CM H",
    "GEM 201 ARM CHAIR": "FAUTEUIL GEM 201",
    "LENGTH: 84CM ": "LONGUEUR : 84CM ",
    "WIDTH: 8.8CM ": "LARGEUR : 8.8CM ",
    "HEIGHT: 88CM ": "HAUTEUR : 88CM ",
    "INTERNAL FRAME COMPOSITION: MIX OF SOLID ":
        "COMPOSITION STRUCTURE INTERNE : MÉLANGE DE ",
    "WOOD SEIKE AND LAUREL AND PLYWOOD BOARD":
        "BOIS SEIKE ET LAURIER ET CONTREPLAQUÉ",
    "STRUCTURE COMPOSITION: SEIKE SOLID WOOD":
        "COMPOSITION STRUCTURE : BOIS SEIKE MASSIF",
    "SEAT CUSHION AND BACK COMPOSITION: HIGH-":
        "COMPOSITION ASSISE ET DOSSIER : MOUSSE HAUTE ",
    "DENSITY FOAM / DENSITY 30 (KG/M3) COVERED WITH ":
        "DENSITÉ / DENSITÉ 30 (KG/M3) RECOUVERTE DE ",
    "DACRON": "DACRON",
    "CUSTOM MADE CONSOLE ": "CONSOLE SUR MESURE ",
    "LENGTH: 250CM ": "LONGUEUR : 250CM ",
    "WIDTH: 32.5CM ": "LARGEUR : 32.5CM ",
    "HEIGHT: 75CM ": "HAUTEUR : 75CM ",
    "WALNUT WOOD NATURAL FINISH ": "FINITION NOYER NATUREL ",
    "UNWIND MODULAR 2-PIECE ": "CANAPÉ SECTIONNEL MODULAIRE ",
    "SLIPCOVERED SECTIONAL ": "2 PIÈCES AVEC HOUSSE ",
    "SOFA": "CANAPÉ",
    "Height: 100'' L x 44.48'' D x 34.25'' H (INCHES)":
        "Hauteur : 100'' L x 44.48'' P x 34.25'' H (POUCES)",
    "TO BE REUPHOLSTERED TO SELECTED FABRIC ":
        "À REGARNIR AVEC LE TISSU SÉLECTIONNÉ ",
    "TO BE REUPHOLSTERED TO SELECTED FABRIC":
        "À REGARNIR AVEC LE TISSU SÉLECTIONNÉ",
    "MIRO BLACK MARBLE END ": "TABLE D'APPOINT MARBRE NOIR ",
    "TABLE WITH BLACK WOOD ": "MIRO AVEC BASE BOIS ",
    "BASE": "NOIR",
    "WIDTH: 50.8CM": "LARGEUR : 50.8CM",
    "HEIGHT: 60.706CM": "HAUTEUR : 60.706CM",
    "DEPTH: 50.8CM": "PROFONDEUR : 50.8CM",
    "BLACK MARBLE AND ENGINEERED WOOD TOP":
        "PLATEAU MARBRE NOIR ET BOIS TECHNIQUE",
    "SOLID MAHOGANY AND EBONIZED OAK VENEER BASE ":
        "BASE ACAJOU MASSIF ET PLACAGE CHÊNE ÉBÉNISÉ ",
    "WITH WIREBRUSHED FINISH": "AVEC FINITION BROSSÉE",
    "STEEL MENDING PLATE WITH BLACK POWDERCOAT ":
        "PLAQUE ACIER AVEC POUDRE NOIRE ",
    "CUSTOM MADE OTTOMAN": "OTTOMAN SUR MESURE",
    "WIDTH: 250CM": "LARGEUR : 250CM",
    "HEIGHT: 45CM": "HAUTEUR : 45CM",
    "DEPTH: 73CM": "PROFONDEUR : 73CM",
    "NADIA BLACK CANE DINING ": "CHAISE NADIA CANNAGE NOIR ",
    "CHAIR": "SALLE À MANGER",
    "WIDTH: 46.355CM": "LARGEUR : 46.355CM",
    "HEIGHT: 81.28CM": "HAUTEUR : 81.28CM",
    "SEAT HEIGHT: 46.99CM": "HAUTEUR ASSISE : 46.99CM",
    "SEAT DEPTH: 43.18CM": "PROFONDEUR ASSISE : 43.18CM",
    "SEAT TO BE REUPHOLSTERED TO SELECTED FABRIC":
        "ASSISE À REGARNIR AVEC LE TISSU SÉLECTIONNÉ",
    "CUSTOM MADE DINING ": "TABLE À MANGER SUR ",
    "DIAMETER: 150 CM": "DIAMÈTRE : 150 CM",
    "HEIGHT: 75 CM": "HAUTEUR : 75 CM",
    "HEIGHT: 75CM": "HAUTEUR : 75CM",
    "DEPTH: 44CM": "PROFONDEUR : 44CM",
    "FITZ CHANNELED RUSSET ": "FAUTEUIL PIVOTANT FITZ CANNELÉ ",
    "VELVET SWIVEL CHAIR": "VELOURS ROUX",
    "WIDTH: 97.79CM": "LARGEUR : 97.79CM",
    "HEIGHT: 69.85CM": "HAUTEUR : 69.85CM",
    "DEPTH: 82.55CM": "PROFONDEUR : 82.55CM",
    "SEAT WIDTH: 58.42CM": "LARGEUR ASSISE : 58.42CM",
    "SEAT DEPTH: 58.42CM": "PROFONDEUR ASSISE : 58.42CM",
    "ARM HEIGHT: 60.325CM": "HAUTEUR BRAS : 60.325CM",
    "SEAT HEIGHT: 44.45CM": "HAUTEUR ASSISE : 44.45CM",
    "COTTON/POLY VELVET": "VELOURS COTON/POLY",
    "SINUOUS WIRE SPRING SUSPENSION": "SUSPENSION RESSORTS ONDULÉS",
    "SWIVEL BASE": "BASE PIVOTANTE",
    "FLEUR END TABLE WOOD - ": "TABLE D'APPOINT FLEUR BOIS - ",
    "WALNUT": "NOYER",
    "46 CM L X 46 CM W X 49 CM H": "46 CM L X 46 CM LARG X 49 CM H",
    "WALNUT WOOD FINISH ": "FINITION BOIS NOYER ",
    "TONSUR BARBER CHAIR": "FAUTEUIL BARBIER TONSUR",
    "BOZZI CHAIR": "CHAISE BOZZI",
    "WIDTH: 80.01CM": "LARGEUR : 80.01CM",
    "HEIGHT: 106.045CM": "HAUTEUR : 106.045CM",
    "DEPTH: 88.9CM": "PROFONDEUR : 88.9CM",
    "WIDTH: 57.15CM": "LARGEUR : 57.15CM",
    "HEIGHT: 40.64CM": "HAUTEUR : 40.64CM",
    "DEPTH: 55.88CM": "PROFONDEUR : 55.88CM",
    "BOUCLE UPHOLSTERY": "GARNISSAGE BOUCLÉ",
    "SOLID OAK LEGS, BLEACHED AND WIRE-BRUSHED":
        "PIEDS CHÊNE MASSIF, BLANCHIS ET BROSSÉS",
    "PARSIFAL END TABLE WOOD -": "TABLE D'APPOINT PARSIFAL BOIS -",
    "BROWN": "MARRON",
    "50 CM L X 50 CM W X 55 CM H": "50 CM L X 50 CM LARG X 55 CM H",
    "WOODEN FINISH - BROWN": "FINITION BOIS - MARRON",
    "OPEN BOX: PICTOGRAPH ": "CONSOLE MÉDIA OPEN BOX : ",
    "MEDIA CONSOLE (68\"–84\")": "PICTOGRAPH (68\"–84\")",
    '68"W X 19"D X 27"H': '68"L X 19"P X 27"H',
    "SIDE COMPARTMENT (2):": "COMPARTIMENT LATÉRAL (2) :",
    '15.4"W X 17"D X 16.4"H': '15.4"L X 17"P X 16.4"H',
    "MIDDLE COMPARTMENT (1):": "COMPARTIMENT CENTRAL (1) :",
    '31.7"W X 17"D X 16.4"H': '31.7"L X 17"P X 16.4"H',
    "CLEARANCE UNDERNEATH:": "DÉGAGEMENT DESSOUS :",
    "KILN-DRIED SOLID MANGO WOOD.": "MANGUIER MASSIF SÉCHÉ AU FOUR.",
    "METAL LEGS IN AN ANTIQUE BRASS FINISH.":
        "PIEDS MÉTAL FINITION LAITON ANTIQUE.",
    "WIDTH: 170CM": "LARGEUR : 170CM",
    "HEIGHT: 40CM": "HAUTEUR : 40CM",
    "DEPTH: 64CM": "PROFONDEUR : 64CM",
    "TOP & BASE: DARK OAK WOOD FINISH":
        "PLATEAU & BASE : FINITION CHÊNE FONCÉ",
    "WIDTH: 320CM": "LARGEUR : 320CM",
    "HEIGHT: 85CM": "HAUTEUR : 85CM",
    "DEPTH: 96-200CM": "PROFONDEUR : 96-200CM",
    "SOFA UPHOLSTERED IN SELECTED FINISH":
        "CANAPÉ GARNI DANS LA FINITION SÉLECTIONNÉE",
    "SIDE TABLE TWISTER": "TABLE D'APPOINT TWISTER",
    "DIAMETER:": "DIAMÈTRE :",
    "FINISH:": "FINITION :",
    "POWDER COATED ALUMINIUM (100% RECYCLED)":
        "ALUMINIUM PEINT POUDRE (100% RECYCLÉ)",
    "COLOUR:": "COULEUR :",
    "BLACK": "NOIR",
    "CUSTOM MADE TV CONSOLE": "MEUBLE TV SUR MESURE",
    "DEPTH: 40CM": "PROFONDEUR : 40CM",
    "WALNUT WOOD ": "BOIS NOYER ",
    "CUSTOM MADE SEATING ": "BANC D'ASSISE SUR ",
    "BENCH": "MESURE",
    "WIDTH: 200CM": "LARGEUR : 200CM",
    "DEPTH: 50CM": "PROFONDEUR : 50CM",
    "BASE: DARK OAK WOOD FINISH": "BASE : FINITION CHÊNE FONCÉ",
    "SEATING: VFM DESIGN": "ASSISE : VFM DESIGN",
    "HAVEN WIDE BED (KING-": "LIT LARGE HAVEN (KING-",
    "STANDARD)": "STANDARD)",
    "347.22CM W X 236.22CM D X 115.57CM H":
        "347.22CM L X 236.22CM P X 115.57CM H",
    "HEADBOARD:": "TÊTE DE LIT :",
    "347.22CM W X 20.32CM D X 115.57CM H":
        "347.22CM L X 20.32CM P X 115.57CM H",
    "CUSTOM MADE SIDE TABLE ": "TABLE D'APPOINT SUR MESURE ",
    "WIDTH: 50CM": "LARGEUR : 50CM",
    "HEIGHT: 52CM": "HAUTEUR : 52CM",
    "SIDE TABLE FINISH TO MATCH THE MIRROR FRAME ":
        "FINITION TABLE D'APPOINT À ASSORTIR AU CADRE ",
    "FINISH IN THE ROOM ": "MIROIR DE LA PIÈCE ",
    "BED WITH HEADBOARD": "LIT AVEC TÊTE DE LIT",
    "BED SIZE: W200CM X D200CM X H55CM":
        "TAILLE LIT : L200CM X P200CM X H55CM",
    "HEADBOARD SIZE: W350CM X D5CM X H125CM":
        "TAILLE TÊTE DE LIT : L350CM X P5CM X H125CM",
    " HEAD BOARD IN LIGHT OAK WOOD AND ":
        " TÊTE DE LIT EN CHÊNE CLAIR ET ",
    "UPHOLSTERY FINISH": "FINITION GARNISSAGE",
    "BED BASE IN UPHOLSTERY FINISH": "SOMMIER EN FINITION GARNISSAGE",
    "CUSTOM MADE BED SIDE ": "TABLE DE CHEVET SUR ",
    "TOP, DRAWERS AND LEGS: LIGHT OAK WOOD FINISH ":
        "DESSUS, TIROIRS ET PIEDS : FINITION CHÊNE CLAIR ",
    "MELROSE CHAIR": "CHAISE MELROSE",
    "WIDTH: 70CM": "LARGEUR : 70CM",
    "HEIGHT:75CM": "HAUTEUR :75CM",
    "DEPTH: 95CM": "PROFONDEUR : 95CM",
    "UPHOLSTERY MATERIAL: PREMIUM BOUCLE":
        "MATÉRIAU GARNISSAGE : BOUCLÉ PREMIUM",
    "BASE MATERIAL: SOLID PLYWOOD":
        "MATÉRIAU BASE : CONTREPLAQUÉ MASSIF",
    "MANGO WOOD SIDE TABLE": "TABLE D'APPOINT MANGUIER",
    "DIAMETER 13 IN. ": "DIAMÈTRE 13 IN. ",
    "HEIGHT APPROX. 19 IN.": "HAUTEUR ENV. 19 IN.",
    "TO BE STAINED TO MATCH THE FINISH AS IN THE ":
        "À TEINTER POUR CORRESPONDRE À LA FINITION ",
    "DESIGN ": "DU DESIGN ",
    "WIDTH: 240CM": "LARGEUR : 240CM",
    # Lighting
    "NOOI WALL LAMP": "APPLIQUE MURALE NOOI",
    "METAL: MATTE BLACK STEEL": "MÉTAL : ACIER NOIR MAT",
    "SHADE: CREAM LINEN TEXTILE": "ABAT-JOUR : LIN CRÈME",
    "ACRYLIC: OPAL": "ACRYLIQUE : OPALE",
    "Karina Light Brown ": "Lampe de table Karina marron ",
    "Terracotta Table Lamp": "clair terre cuite",
    "Levant Pendant Bronze With ": "Suspension Levant bronze avec ",
    "Shade": "abat-jour",
    "THE HOME LIBRARY ": "THE HOME LIBRARY ",
    "LIGHTING & INTERIORS": "ÉCLAIRAGE & INTÉRIEURS",
    "TOP, CABINETRY& FRAMES: ": "DESSUS, MENUISERIE & CADRES : ",
    "SHUTTER: ": "PORTE : ",
    "CLEAR GLASS": "VERRE CLAIR",
    "HANDLES: ": "POIGNÉES : ",
    " BRASS": " LAITON",
    'Elias 17.75" Wide 3-Light ': 'Suspension Elias 17.75" large 3 ',
    "Dome Matte Black And Gold ": "lumières dôme noir mat et or ",
    "Pendant": "suspension",
    "9.5 inches tall, 17.8 inches wide, 17.8 ":
        "9.5 pouces de haut, 17.8 pouces de large, 17.8 ",
    "inches long, 7.0 pounds in weight.":
        "pouces de long, 7.0 livres.",
    "FINISH: BLACK": "FINITION : NOIR",
    "Work lamp, off-white": "Lampe de travail, blanc cassé",
    "Max.: 11 W": "Max. : 11 W",
    "Shade diameter: 19 cm": "Diamètre abat-jour : 19 cm",
    "Cord length: 1.5 m": "Longueur câble : 1.5 m",
    "OFF WHITE COLOR": "COULEUR BLANC CASSÉ",
    "CEILING DIRECT SPOT LIGHT ": "SPOT PLAFOND DIRECT ",
    "Details : 15 °": "Détails : 15 °",
    "Details : 25 °": "Détails : 25 °",
    "Details : 40 °": "Détails : 40 °",
    "AS PER DRAWING": "SELON PLAN",
    "AS PER ": "SELON ",
    "DRAWING": "PLAN",
    "AS PER IMAGE": "SELON IMAGE",
    "TUBE SPOT LIGHT SB2": "TUBE SPOT SB2",
    # Rugs
    "LOOSE RUG": "TAPIS LIBRE",
    "Contact: Fidelis": "Contact : Fidelis",
    "LENGTH: 340 CM": "LONGUEUR : 340 CM",
    "WIDTH: 150 CM": "LARGEUR : 150 CM",
    "100% BAMBOO SILK & CUT / LOOP PILE , +- 3KGS/ ":
        "100% SOIE BAMBOU & VELOURS COUPÉ / BOUCLÉ , +- 3KGS/ ",
    "SQM AND TOTAL HEIGHT 13mm": "M2 ET HAUTEUR TOTALE 13mm",
    "LENGTH: 420 CM": "LONGUEUR : 420 CM",
    "WIDTH: 290 CM": "LARGEUR : 290 CM",
    "LENGTH: 370 CM": "LONGUEUR : 370 CM",
    "WIDTH: 210 CM": "LARGEUR : 210 CM",
    "LENGTH: 1100 CM": "LONGUEUR : 1100 CM",
    "WIDTH: 325 CM": "LARGEUR : 325 CM",
    "LENGTH: 390 CM": "LONGUEUR : 390 CM",
    "WIDTH: 342 CM": "LARGEUR : 342 CM",
    "LENGTH: 270 CM": "LONGUEUR : 270 CM",
    "WIDTH: 270 CM": "LARGEUR : 270 CM",
    "WIDTH: 230 CM": "LARGEUR : 230 CM",
    "LENGTH: 400 CM": "LONGUEUR : 400 CM",
    "WIDTH: 300 CM": "LARGEUR : 300 CM",
    "LENGTH: 310 CM": "LONGUEUR : 310 CM",
    "WIDTH: 260 CM": "LARGEUR : 260 CM",
    # Artwork
    "SOUL ART & INTERIOR ": "SOUL ART & INTERIOR ",
    "STUDIO": "STUDIO",
    "Contact: MR. AMR SAFI": "Contact : M. AMR SAFI",
    "PAINTING USING ACRYLIC ON CANVAS, STRETCHED ":
        "PEINTURE ACRYLIQUE SUR TOILE, TENDUE ",
    "ON WOODEN STRETCHER WITH SUPPORT AT THE ":
        "SUR CHÂSSIS BOIS AVEC RENFORT À L' ",
    "BACK, FRAMED WITH WOODEN FRAME":
        "ARRIÈRE, ENCADRÉE CADRE BOIS",
    "WALL STICKER": "STICKER MURAL",
    "WALL STICKER ": "STICKER MURAL ",
    # Curtains
    "MAIN FABRIC NON BLACK ": "TISSU PRINCIPAL NON ",
    "OUT FABRIC ": "OCCULTANT ",
    "SEAWAVE RAIL ": "RAIL SEAWAVE ",
    "CHIFFON FABRIC ": "TISSU MOUSSELINE ",
    "M TRACK": "RAIL M",
    "MAIN FABRIC BLACK OUT ": "TISSU PRINCIPAL ",
    "FABRIC ": "OCCULTANT ",
    "WITH BLACKOUT LINING": "AVEC DOUBLURE OCCULTANTE",
    "MAIN FABRIC NON  BLACK ": "TISSU PRINCIPAL NON  ",
    "OUT CURTAIN": "OCCULTANT",
    "CURTAIN": "RIDEAU",
    "BLINDS": "STORES",
    "SKIPTON SUNSCREEN BLINDS - UC112":
        "STORES SOLAIRES SKIPTON - UC112",
    # Accessories
    "PLANT WITH POT": "PLANTE AVEC POT",
    "Contact: Danica Torres": "Contact : Danica Torres",
    "Contact: Kinan Safi": "Contact : Kinan Safi",
    "TERRACOTA DÉCOR POTS": "POTS DÉCOR TERRE CUITE",
    " PLANT HT: 1700 MM": " HT PLANTE : 1700 MM",
    "POT SIZE: 400 MM DIA & HT": "TAILLE POT : 400 MM DIA & HT",
    # Dimension labels W/D/H already in many strings; generic patterns below
    "W170cm x H100cm": "L170cm x H100cm",
    "W240cm x H 160cm": "L240cm x H 160cm",
    "W240cm x H 140cm": "L240cm x H 140cm",
    "W80cm x H 120cm": "L80cm x H 120cm",
    "W100cm x H 150cm": "L100cm x H 150cm",
    "W150cm x H170cm": "L150cm x H170cm",
    "W120cm x H160cm": "L120cm x H160cm",
    "W200cm x H130cm": "L200cm x H130cm",
    "W170cm x H110cm": "L170cm x H110cm",
    "W100cm x H130cm": "L100cm x H130cm",
    "W90cm x H120cm": "L90cm x H120cm",
    "W462CM X D110CM X H80CM": "L462CM X P110CM X H80CM",
    "W200CM X D110CM X H45CM": "L200CM X P110CM X H45CM",
    "W210CM X D120CM X H35CM": "L210CM X P120CM X H35CM",
    # Fix FRANKA - redo properly
}

# Override the bad FRANKA translation
TRANSLATIONS["FRANKA DINING CHAIR"] = "CHAISE DE SALLE À MANGER FRANKA"

# Ambiguous short tokens that appear in many contexts — handle carefully.
# "BASE", "TABLE ", "CHAIR", "MADE", "FABRIC ", "FINISH" are contextual.
# Remove dangerous short mappings that break other spans:
for bad in ("BASE", "TABLE ", "CHAIR", "MADE", "FABRIC ", "FINISH", "TABLE", "SOFA", "OAK", "BLACK", "BROWN", "WALNUT", "BENCH", "Shade", "Pendant", "DRAWING", "FRAME", "STUDIO", "5 "):
    TRANSLATIONS.pop(bad, None)

# Re-add contextual full-line ones already present; add safe alternatives:
TRANSLATIONS.update({
    "MADE": "MESURE",  # only used after "CUSTOM "/"DINING TABLE - CUSTOM "
    "TABLE ": "TABLE ",  # keep as TABLE for coffee table line break - wait
})
# "CUSTOM MADE COFFEE " + "TABLE " → "TABLE BASSE SUR " + "MESURE "
TRANSLATIONS["CUSTOM MADE COFFEE "] = "TABLE BASSE SUR "
TRANSLATIONS["TABLE "] = "MESURE "
# But "CUSTOM MADE CONSOLE " + nothing with TABLE on same - CS-02 uses "CUSTOM MADE CONSOLE " and "TABLE " separately on page 6
# Page 6: "CUSTOM MADE CONSOLE \nTABLE \nBY CONTRACTOR" 
# So TABLE alone as "MESURE" is wrong for console table.
# Better: "TABLE " → "TABLE " unchanged, and fold coffee into one if possible.
TRANSLATIONS["CUSTOM MADE COFFEE "] = "TABLE BASSE SUR MESURE "
TRANSLATIONS["TABLE "] = "TABLE "
TRANSLATIONS.pop("MADE", None)
# DINING TABLE - CUSTOM + MADE
TRANSLATIONS["DINING TABLE - CUSTOM "] = "TABLE À MANGER - SUR MESURE "
TRANSLATIONS["CUSTOM MADE DINING "] = "TABLE À MANGER SUR MESURE "
# "CUSTOM MADE SEATING " + "BENCH"
TRANSLATIONS["CUSTOM MADE SEATING "] = "BANC D'ASSISE SUR MESURE "
TRANSLATIONS["BENCH"] = "BANC"
# "CUSTOM MADE BED SIDE " + "TABLE" (page 9 shows TABLE on next line as part of TB-16)
# unique has 'CUSTOM MADE BED SIDE ' and separately 'TABLE' 
TRANSLATIONS["CUSTOM MADE BED SIDE "] = "TABLE DE CHEVET SUR MESURE "
TRANSLATIONS["TABLE"] = "TABLE"
# MIRO lines: "TABLE WITH BLACK WOOD " + "BASE"
TRANSLATIONS["TABLE WITH BLACK WOOD "] = "AVEC BASE BOIS NOIR "
TRANSLATIONS["BASE"] = "BASE"
# NADIA: "NADIA BLACK CANE DINING " + "CHAIR"
TRANSLATIONS["NADIA BLACK CANE DINING "] = "CHAISE NADIA CANNAGE NOIR "
TRANSLATIONS["CHAIR"] = "CHAISE"
# Lighting shade/pendant - product name lines, translate carefully
TRANSLATIONS["Shade"] = "abat-jour"
TRANSLATIONS["Pendant"] = "suspension"
TRANSLATIONS["DRAWING"] = "PLAN"
TRANSLATIONS["FRAME"] = "STRUCTURE"
TRANSLATIONS["OAK"] = "CHÊNE"
TRANSLATIONS["BLACK"] = "NOIR"
TRANSLATIONS["BROWN"] = "MARRON"
TRANSLATIONS["WALNUT"] = "NOYER"
TRANSLATIONS["SOFA"] = "CANAPÉ"
TRANSLATIONS["FINISH"] = "FINITION"  # column header - also used as label "FINISH:"
# Wait FINISH column header and "FINISH:" - FINISH alone is column header
# "FINISH:" already mapped. Good.

# Fix seating bench - don't double
TRANSLATIONS["CUSTOM MADE SEATING "] = "BANC D'ASSISE "
TRANSLATIONS["BENCH"] = "SUR MESURE"

# Fix coffee table double
TRANSLATIONS["CUSTOM MADE COFFEE "] = "TABLE BASSE SUR "
# TABLE " as MESURE when following coffee - but conflicts with console TABLE
# Keep TABLE " as TABLE and accept "TABLE BASSE SUR / TABLE" or use:
TRANSLATIONS["CUSTOM MADE COFFEE "] = "TABLE BASSE SUR MESURE"
TRANSLATIONS["TABLE "] = " "
TRANSLATIONS["MADE"] = " "  # continuation of "… SUR MESURE" on prior line
TRANSLATIONS["FABRIC "] = "TISSU "
TRANSLATIONS["STANDARD)"] = "STANDARD)"
TRANSLATIONS["CODE      "] = "CODE      "
TRANSLATIONS["DIMENSION"] = "DIMENSION"
TRANSLATIONS["DIMENSIONS"] = "DIMENSIONS"
TRANSLATIONS["PHOTO"] = "PHOTO"
TRANSLATIONS["DACRON"] = "DACRON"
TRANSLATIONS["RANARP"] = "RANARP"
TRANSLATIONS["STUDIO"] = "STUDIO"
TRANSLATIONS["TABLE"] = "TABLE"
TRANSLATIONS["BASE"] = "BASE"


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

    text_lum = (
        0.299 * text_rgb[0] * 255
        + 0.587 * text_rgb[1] * 255
        + 0.114 * text_rgb[2] * 255
    )
    if text_lum > 180:
        dark = [s for s in samples if lum(s) < 220]
        pick = min(dark or samples, key=lum)
    else:
        light = [s for s in samples if lum(s) > 80]
        if not light:
            light = samples
        yellow = [s for s in light if s[0] > 200 and s[1] > 200 and s[2] < 120]
        if yellow:
            pick = max(yellow, key=lambda s: s[0] + s[1] - s[2])
        else:
            pick = max(light, key=lum)
    return (pick[0] / 255, pick[1] / 255, pick[2] / 255)


_DIM_LABELS = [
    (re.compile(r"^(Height|HEIGHT|Hauteur)\s*:\s*", re.I), "Hauteur : "),
    (re.compile(r"^(Width|WIDTH|Largeur)\s*:\s*", re.I), "Largeur : "),
    (re.compile(r"^(Depth|DEPTH|Profondeur)\s*:\s*", re.I), "Profondeur : "),
    (re.compile(r"^(Length|LENGTH|Longueur)\s*:\s*", re.I), "Longueur : "),
    (re.compile(r"^(Diameter|DIAMETER|Diamètre)\s*:\s*", re.I), "Diamètre : "),
    (re.compile(r"^(Seat height|SEAT HEIGHT)\s*:\s*", re.I), "Hauteur assise : "),
    (re.compile(r"^(Seat width|SEAT WIDTH)\s*:\s*", re.I), "Largeur assise : "),
    (re.compile(r"^(Seat depth|SEAT DEPTH)\s*:\s*", re.I), "Profondeur assise : "),
    (re.compile(r"^(Arm height|ARM HEIGHT)\s*:\s*", re.I), "Hauteur bras : "),
    (re.compile(r"^(Cord length)\s*:\s*", re.I), "Longueur câble : "),
    (re.compile(r"^(Shade diameter)\s*:\s*", re.I), "Diamètre abat-jour : "),
    (re.compile(r"^(Base diameter|BASE DIAMETER)\s*:\s*", re.I), "Diamètre base : "),
]


def translate_span(text: str) -> str | None:
    if text in TRANSLATIONS:
        fr = TRANSLATIONS[text]
        return None if fr == text else fr
    for pat, prefix in _DIM_LABELS:
        m = pat.match(text)
        if m:
            rest = text[m.end() :]
            # Convert W/D dimension tokens in remainder when clear
            rest2 = rest
            return prefix + rest2
    # Generic DIMENSIONS: already handled; Contact:
    m = re.match(r"^Contact:\s*(.*)$", text)
    if m:
        return f"Contact : {m.group(1)}"
    m = re.match(r"^Details\s*:\s*(.*)$", text)
    if m:
        return f"Détails : {m.group(1)}"
    return None


def fontname_for(span_font: str, flags: int) -> str:
    bold = bool(flags & pymupdf.TEXT_FONT_BOLD) or "Bold" in span_font
    return FONTNAME_BOLD if bold else FONTNAME_REG


def process(src: Path, out: Path) -> None:
    doc = pymupdf.open(src)
    replaced = 0
    skipped = 0
    missing: set[str] = set()

    code_re = re.compile(
        r"^(CH|TB|SF|CS|BD|DEL|L|S|RUG|ART|CUR|SHR|BLI|ACC|WD|GL|MT)-\d+\s*$"
        r"|^[LS]\d+$|^S[1-4]$|^WD-01\s*$|^GL-01\s*$|^MT-01$"
    )

    for page in doc:
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)
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
                        if re.search(r"[A-Za-zÀ-ÿ]{3,}", text):
                            if code_re.match(text.strip()):
                                skipped += 1
                                continue
                            if re.fullmatch(r"\d+(\.\d+)?", text.strip()):
                                skipped += 1
                                continue
                            # brand / contact leftovers tracked
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

        for job in jobs:
            page.add_redact_annot(job["bbox"], fill=job["fill"], cross_out=False)
        if jobs:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        for job in jobs:
            x, y = job["origin"]
            point = (
                pymupdf.Point(x, y)
                if isinstance(x, (int, float))
                else pymupdf.Point(job["bbox"].x0, job["bbox"].y1 - 1.5)
            )
            size = job["size"]
            fontfile = FONT_BOLD if job["font"] == FONTNAME_BOLD else FONT_REG
            font = pymupdf.Font(fontfile=fontfile)
            tw = font.text_length(job["fr"], fontsize=size)
            max_w = max(job["bbox"].width, 1)
            if tw > max_w * 1.08:
                size = max(5.5, size * (max_w / tw) * 0.98)
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
            "title": "VILLA YASMINA @MAROC - Spécification FF&E (FR)",
            "author": "User",
            "subject": "Traduction française — même contenu et mise en page",
            "creator": "translate_ffe_to_french.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    print(f"Replaced spans: {replaced}")
    print(f"Unchanged spans: {skipped}")
    if missing:
        # Filter obvious keepers (brands, codes, names)
        keepers = []
        for t in sorted(missing, key=lambda s: (-len(s), s)):
            if re.search(
                r"(CASA BLANCO|CRATE|BARREL|CB2|IKEA|WEST ELM|HOTE|DANTONE|"
                r"BLOOMING|PAN HOME|MALYS|POLSPOTTEN|KANABA|H&M|LAMPS PLUS|"
                r"EGE|ROMO|VILLA NOVA|LUX SUEDE|MJ TESSUTI|CORRIS|LUCERNE|"
                r"NIMBUS|AnosLuz|TECNI|LOOM|ADRIANA|LEANNE|JOULIAN|AMR SAFI|"
                r"Kinan|Danica|PLANTERS|LUXURY|HOME LIBRARY|IBL|MIRTH|"
                r"V3244|V3424|MJ1006|UC112|Tel:|@|CM|MM|IN|W\d|X\d|\+\d)",
                t,
                re.I,
            ):
                continue
            if re.fullmatch(r"[\d\s\.\-xX×Ø''\"/]+", t):
                continue
            keepers.append(t)
        print(f"Possibly untranslated ({len(keepers)}):")
        for t in keepers[:100]:
            print(f"  {repr(t)}")


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else SRC
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    process(src, out)
