"""Generate a deterministic Stage 2 synthetic product catalog."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import TypedDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import Product


RANDOM_SEED = 20260621
PRODUCTS_PER_PARTNER = 50
OUTPUT_PATH = Path(__file__).with_name("products.json")


class ItemTemplate(TypedDict):
    name: str
    name_de: str
    description: str
    description_de: str
    tags: list[str]
    tags_de: list[str]
    price_min: float
    price_max: float
    modifiers: list[tuple[str, str]]


class CategoryTemplate(TypedDict):
    category: str
    category_de: str
    brands: list[str]
    items: list[ItemTemplate]


def item(
    name: str,
    name_de: str,
    description: str,
    description_de: str,
    tags: list[str],
    tags_de: list[str],
    price_min: float,
    price_max: float,
    modifiers: list[tuple[str, str]],
) -> ItemTemplate:
    return {
        "name": name,
        "name_de": name_de,
        "description": description,
        "description_de": description_de,
        "tags": tags,
        "tags_de": tags_de,
        "price_min": price_min,
        "price_max": price_max,
        "modifiers": modifiers,
    }


CATALOG_TEMPLATES: dict[str, list[CategoryTemplate]] = {
    "dm": [
        {
            "category": "baby care",
            "category_de": "babypflege",
            "brands": ["Babylove", "Pampers", "Penaten", "HiPP Babysanft"],
            "items": [
                item(
                    "Baby Diapers Size 4",
                    "Babywindeln Größe 4",
                    "Soft absorbent diapers for babies from 9 to 14 kg, suitable for daytime and overnight use.",
                    "Weiche, saugfähige Windeln für Babys von 9 bis 14 kg, geeignet für Tag und Nacht.",
                    ["drugstore", "baby care", "baby diapers", "diapers", "size 4"],
                    ["drogerie", "babypflege", "babywindeln", "windeln", "größe 4"],
                    7.45,
                    13.95,
                    [("42 pcs", "42 Stück"), ("jumbo pack", "Jumbopack"), ("sensitive fit", "Sensitiv-Passform")],
                ),
                item(
                    "Sensitive Wet Wipes",
                    "Sensitive Feuchttücher",
                    "Fragrance-free wet wipes for diaper changes, hands, and quick cleanups on the go.",
                    "Parfümfreie Feuchttücher zum Wickeln, für Hände und zur schnellen Reinigung unterwegs.",
                    ["drugstore", "baby care", "wet wipes", "sensitive", "fragrance free"],
                    ["drogerie", "babypflege", "feuchttücher", "sensitiv", "parfümfrei"],
                    1.25,
                    3.95,
                    [("80 pcs", "80 Stück"), ("travel pack", "Reisepackung"), ("extra soft", "extra weich")],
                ),
                item(
                    "Baby Care Lotion",
                    "Baby Pflegelotion",
                    "Mild body lotion for dry and sensitive baby skin after bathing or changing.",
                    "Milde Körperlotion für trockene und empfindliche Babyhaut nach dem Baden oder Wickeln.",
                    ["drugstore", "baby care", "baby lotion", "sensitive skin"],
                    ["drogerie", "babypflege", "babylotion", "empfindliche haut"],
                    2.25,
                    5.95,
                    [("200 ml", "200 ml"), ("with almond oil", "mit Mandelöl"), ("daily care", "Tagespflege")],
                ),
                item(
                    "Baby Bath Wash",
                    "Baby Waschgel",
                    "Gentle wash gel for baby bath time, hair, and sensitive skin.",
                    "Sanftes Waschgel für Babybad, Haare und empfindliche Haut.",
                    ["drugstore", "baby care", "baby bath", "wash gel"],
                    ["drogerie", "babypflege", "babybad", "waschgel"],
                    2.75,
                    6.25,
                    [("head to toe", "Kopf bis Fuß"), ("300 ml", "300 ml"), ("soap free", "seifenfrei")],
                ),
            ],
        },
        {
            "category": "cosmetics",
            "category_de": "kosmetik",
            "brands": ["Balea", "Alverde", "Maybelline", "L'Oreal Paris"],
            "items": [
                item(
                    "Hydrating Face Cream",
                    "Feuchtigkeit Gesichtscreme",
                    "Light moisturizing cream for normal and combination skin with a non-greasy finish.",
                    "Leichte Feuchtigkeitscreme für normale Haut und Mischhaut mit nicht fettendem Finish.",
                    ["drugstore", "cosmetics", "face cream", "moisturizer", "skin care"],
                    ["drogerie", "kosmetik", "gesichtscreme", "feuchtigkeit", "hautpflege"],
                    2.95,
                    12.95,
                    [("50 ml", "50 ml"), ("hyaluron", "Hyaluron"), ("day cream", "Tagescreme")],
                ),
                item(
                    "Volume Mascara",
                    "Volumen Mascara",
                    "Black mascara for defined lashes and everyday eye makeup.",
                    "Schwarze Mascara für definierte Wimpern und tägliches Augen-Make-up.",
                    ["drugstore", "cosmetics", "mascara", "makeup", "lashes"],
                    ["drogerie", "kosmetik", "mascara", "makeup", "wimpern"],
                    3.95,
                    14.95,
                    [("black", "schwarz"), ("waterproof", "wasserfest"), ("extra volume", "extra Volumen")],
                ),
                item(
                    "Nourishing Lip Balm",
                    "Pflegender Lippenbalsam",
                    "Pocket-size lip balm for dry lips with everyday moisture protection.",
                    "Lippenpflege für trockene Lippen mit Feuchtigkeitsschutz für jeden Tag.",
                    ["drugstore", "cosmetics", "lip balm", "lip care", "dry lips"],
                    ["drogerie", "kosmetik", "lippenbalsam", "lippenpflege", "trockene lippen"],
                    0.95,
                    4.45,
                    [("shea butter", "Sheabutter"), ("cherry", "Kirsche"), ("SPF 15", "LSF 15")],
                ),
                item(
                    "Micellar Makeup Remover",
                    "Mizellen Make-up Entferner",
                    "Micellar cleansing water for removing makeup, sunscreen, and daily residue.",
                    "Mizellenwasser zum Entfernen von Make-up, Sonnencreme und Rückständen des Tages.",
                    ["drugstore", "cosmetics", "makeup remover", "micellar water", "cleansing"],
                    ["drogerie", "kosmetik", "make-up entferner", "mizellenwasser", "reinigung"],
                    1.95,
                    6.95,
                    [("400 ml", "400 ml"), ("for sensitive skin", "für sensible Haut"), ("oil free", "ölfrei")],
                ),
            ],
        },
        {
            "category": "oral care",
            "category_de": "mundpflege",
            "brands": ["Dontodent", "Oral-B", "Elmex", "Colgate"],
            "items": [
                item(
                    "Sensitive Toothpaste",
                    "Sensitiv-Zahnpasta",
                    "Fluoride toothpaste for sensitive teeth, enamel protection, and fresh breath.",
                    "Fluorid-Zahnpasta für empfindliche Zähne, Zahnschmelzschutz und frischen Atem.",
                    ["drugstore", "oral care", "toothpaste", "sensitive teeth", "fluoride"],
                    ["drogerie", "mundpflege", "zahnpasta", "sensible zähne", "fluorid"],
                    0.85,
                    4.95,
                    [("75 ml", "75 ml"), ("extra fresh", "extra frisch"), ("enamel care", "Zahnschmelzschutz")],
                ),
                item(
                    "Medium Toothbrush",
                    "Mittelharte Zahnbürste",
                    "Manual toothbrush with medium bristles for everyday dental cleaning.",
                    "Handzahnbürste mit mittleren Borsten für die tägliche Zahnreinigung.",
                    ["drugstore", "oral care", "toothbrush", "medium bristles"],
                    ["drogerie", "mundpflege", "zahnbürste", "mittelhart"],
                    0.95,
                    5.95,
                    [("2 pack", "2er-Pack"), ("soft grip", "Soft-Grip"), ("compact head", "Kompaktkopf")],
                ),
                item(
                    "Fresh Mint Mouthwash",
                    "Frische Minze Mundspülung",
                    "Alcohol-free mouthwash for fresh breath and daily oral hygiene.",
                    "Alkoholfreie Mundspülung für frischen Atem und tägliche Mundhygiene.",
                    ["drugstore", "oral care", "mouthwash", "fresh breath", "mint"],
                    ["drogerie", "mundpflege", "mundspülung", "frischer atem", "minze"],
                    1.45,
                    6.45,
                    [("500 ml", "500 ml"), ("alcohol free", "alkoholfrei"), ("gum care", "Zahnfleischpflege")],
                ),
            ],
        },
        {
            "category": "hair care",
            "category_de": "haarpflege",
            "brands": ["Balea", "Garnier", "Nivea", "Schwarzkopf"],
            "items": [
                item(
                    "Anti-Dandruff Shampoo",
                    "Anti-Schuppen Shampoo",
                    "Shampoo for flaky scalp and oily roots, suitable for frequent washing.",
                    "Shampoo gegen Schuppen und fettige Ansätze, geeignet für häufiges Waschen.",
                    ["drugstore", "hair care", "anti dandruff", "shampoo", "scalp"],
                    ["drogerie", "haarpflege", "anti-schuppen", "shampoo", "kopfhaut"],
                    1.25,
                    8.95,
                    [("300 ml", "300 ml"), ("mint fresh", "Minze frisch"), ("daily use", "tägliche Anwendung")],
                ),
                item(
                    "Color Protection Conditioner",
                    "Color-Schutz Spülung",
                    "Conditioner for colored hair that helps smooth lengths and protect shine.",
                    "Spülung für coloriertes Haar, glättet die Längen und schützt den Glanz.",
                    ["drugstore", "hair care", "conditioner", "color protection"],
                    ["drogerie", "haarpflege", "spülung", "color-schutz"],
                    1.45,
                    9.95,
                    [("200 ml", "200 ml"), ("shine care", "Glanzpflege"), ("for colored hair", "für coloriertes Haar")],
                ),
                item(
                    "Repair Hair Mask",
                    "Repair Haarkur",
                    "Intensive hair mask for dry, brittle, or heat-styled hair.",
                    "Intensive Haarkur für trockenes, brüchiges oder hitzegestyltes Haar.",
                    ["drugstore", "hair care", "hair mask", "repair", "dry hair"],
                    ["drogerie", "haarpflege", "haarkur", "repair", "trockenes haar"],
                    1.95,
                    10.95,
                    [("250 ml", "250 ml"), ("keratin care", "Keratinpflege"), ("weekly treatment", "Wochenkur")],
                ),
            ],
        },
        {
            "category": "household cleaning",
            "category_de": "haushaltsreinigung",
            "brands": ["Denkmit", "Frosch", "Viss", "Sidolin"],
            "items": [
                item(
                    "Color Laundry Detergent",
                    "Color Waschmittel",
                    "Liquid detergent for colored laundry, low-temperature washes, and everyday loads.",
                    "Flüssiges Waschmittel für Buntwäsche, niedrige Temperaturen und Alltagswäsche.",
                    ["drugstore", "household cleaning", "laundry detergent", "color laundry"],
                    ["drogerie", "haushaltsreinigung", "waschmittel", "buntwäsche"],
                    2.45,
                    9.95,
                    [("20 washes", "20 Waschladungen"), ("1.1 l", "1,1 l"), ("family bottle", "Familienflasche")],
                ),
                item(
                    "Dishwasher Tabs",
                    "Spülmaschinentabs",
                    "Dishwasher tabs for clean plates, glasses, and cutlery without pre-rinsing.",
                    "Spülmaschinentabs für sauberes Geschirr, Gläser und Besteck ohne Vorspülen.",
                    ["drugstore", "household cleaning", "dishwasher tabs", "dishwashing"],
                    ["drogerie", "haushaltsreinigung", "spülmaschinentabs", "spülen"],
                    2.95,
                    11.95,
                    [("40 tabs", "40 Tabs"), ("all in one", "All-in-One"), ("lemon fresh", "Zitronenfrische")],
                ),
                item(
                    "All-Purpose Cleaning Spray",
                    "Allzweck-Reinigungsspray",
                    "Spray cleaner for kitchen counters, bathroom surfaces, tiles, and everyday spills.",
                    "Sprühreiniger für Küchenflächen, Badoberflächen, Fliesen und alltägliche Flecken.",
                    ["drugstore", "household cleaning", "cleaning spray", "all purpose cleaner"],
                    ["drogerie", "haushaltsreinigung", "reinigungsspray", "allzweckreiniger"],
                    1.25,
                    5.95,
                    [("750 ml", "750 ml"), ("citrus", "Zitrus"), ("refillable", "nachfüllbar")],
                ),
            ],
        },
        {
            "category": "personal hygiene",
            "category_de": "körperpflege",
            "brands": ["Balea", "Nivea", "Jessa", "SebaMed"],
            "items": [
                item(
                    "Lavender Shower Gel",
                    "Lavendel Duschgel",
                    "Gentle shower gel with lavender scent for daily body care.",
                    "Sanftes Duschgel mit Lavendelduft für die tägliche Körperpflege.",
                    ["drugstore", "personal hygiene", "shower gel", "lavender"],
                    ["drogerie", "körperpflege", "duschgel", "lavendel"],
                    0.95,
                    5.95,
                    [("300 ml", "300 ml"), ("relaxing scent", "entspannender Duft"), ("pH skin neutral", "pH-hautneutral")],
                ),
                item(
                    "Fresh Deodorant Roll-On",
                    "Frische Deo Roll-On",
                    "Roll-on deodorant for reliable everyday freshness and underarm protection.",
                    "Roll-on-Deo für zuverlässige Frische und Schutz im Alltag.",
                    ["drugstore", "personal hygiene", "deodorant", "roll on"],
                    ["drogerie", "körperpflege", "deo", "roll-on"],
                    1.15,
                    6.95,
                    [("50 ml", "50 ml"), ("48h protection", "48h Schutz"), ("aluminum free", "ohne Aluminium")],
                ),
                item(
                    "Cream Hand Soap Refill",
                    "Cremeseife Nachfüllpack",
                    "Mild liquid soap refill for frequent hand washing in kitchen or bathroom.",
                    "Milde Flüssigseife zum Nachfüllen für häufiges Händewaschen in Küche oder Bad.",
                    ["drugstore", "personal hygiene", "hand soap", "refill"],
                    ["drogerie", "körperpflege", "handseife", "nachfüllpack"],
                    0.75,
                    3.95,
                    [("500 ml", "500 ml"), ("milk and honey", "Milch und Honig"), ("sensitive", "sensitiv")],
                ),
            ],
        },
    ],
    "edeka": [
        {
            "category": "pasta and grains",
            "category_de": "nudeln und getreide",
            "brands": ["EDEKA", "Gut & Günstig", "Barilla", "Oryza"],
            "items": [
                item(
                    "Spaghetti Pasta",
                    "Spaghetti Nudeln",
                    "Classic durum wheat spaghetti for tomato sauce, pesto, and weeknight pasta dishes.",
                    "Klassische Spaghetti aus Hartweizen für Tomatensauce, Pesto und schnelle Pastagerichte.",
                    ["grocery", "pasta", "spaghetti", "pantry", "meal ingredient"],
                    ["lebensmittel", "nudeln", "spaghetti", "vorrat", "zutat"],
                    0.79,
                    2.99,
                    [("500 g", "500 g"), ("no. 5", "Nr. 5"), ("family pack", "Familienpackung")],
                ),
                item(
                    "Basmati Rice",
                    "Basmati Reis",
                    "Long-grain basmati rice for curries, bowls, stir-fries, and side dishes.",
                    "Langkorn-Basmati-Reis für Currys, Bowls, Pfannengerichte und Beilagen.",
                    ["grocery", "rice", "grains", "pantry", "meal ingredient"],
                    ["lebensmittel", "reis", "getreide", "vorrat", "zutat"],
                    1.49,
                    4.99,
                    [("1 kg", "1 kg"), ("loose grain", "locker körnig"), ("aromatic", "aromatisch")],
                ),
                item(
                    "Couscous",
                    "Couscous",
                    "Fine couscous for salads, roasted vegetables, and quick warm meals.",
                    "Feiner Couscous für Salate, Ofengemüse und schnelle warme Gerichte.",
                    ["grocery", "grains", "couscous", "pantry"],
                    ["lebensmittel", "getreide", "couscous", "vorrat"],
                    1.19,
                    3.49,
                    [("500 g", "500 g"), ("quick cook", "schnell garend"), ("Mediterranean", "mediterran")],
                ),
            ],
        },
        {
            "category": "dairy",
            "category_de": "molkerei",
            "brands": ["EDEKA", "Gut & Günstig", "Alnatura", "Weihenstephan"],
            "items": [
                item(
                    "Fresh Milk 1.5%",
                    "Frische Milch 1,5%",
                    "Low-fat fresh milk for cereal, coffee, baking, and everyday cooking.",
                    "Fettarme frische Milch für Müsli, Kaffee, Backen und tägliches Kochen.",
                    ["grocery", "dairy", "milk", "breakfast", "cooking"],
                    ["lebensmittel", "molkerei", "milch", "frühstück", "kochen"],
                    0.99,
                    1.79,
                    [("1 l", "1 l"), ("low fat", "fettarm"), ("fresh bottle", "Frischeflasche")],
                ),
                item(
                    "Greek Yogurt",
                    "Griechischer Joghurt",
                    "Creamy yogurt for breakfast bowls, snacks, dips, and sauces.",
                    "Cremiger Joghurt für Frühstücksbowls, Snacks, Dips und Saucen.",
                    ["grocery", "dairy", "yogurt", "breakfast", "protein"],
                    ["lebensmittel", "molkerei", "joghurt", "frühstück", "protein"],
                    1.29,
                    3.49,
                    [("500 g", "500 g"), ("10% fat", "10% Fett"), ("natural", "natur")],
                ),
                item(
                    "Parmesan Cheese",
                    "Parmesan Käse",
                    "Hard cheese for pasta, risotto, salads, and Italian-style cooking.",
                    "Hartkäse für Pasta, Risotto, Salate und italienische Küche.",
                    ["grocery", "dairy", "cheese", "parmesan", "pasta topping"],
                    ["lebensmittel", "molkerei", "käse", "parmesan", "pasta"],
                    1.99,
                    5.99,
                    [("grated 100 g", "gerieben 100 g"), ("piece 200 g", "Stück 200 g"), ("aged", "gereift")],
                ),
            ],
        },
        {
            "category": "fresh produce",
            "category_de": "frische produkte",
            "brands": ["EDEKA", "EDEKA Bio", "Fresh Farms", "Regional Markt"],
            "items": [
                item(
                    "Cherry Tomatoes",
                    "Cherrytomaten",
                    "Sweet small tomatoes for salads, pasta, lunch boxes, and quick snacks.",
                    "Süße kleine Tomaten für Salate, Pasta, Lunchboxen und schnelle Snacks.",
                    ["grocery", "fresh produce", "tomatoes", "cherry tomatoes", "vegetables"],
                    ["lebensmittel", "frisch", "tomaten", "cherrytomaten", "gemüse"],
                    1.49,
                    3.99,
                    [("250 g", "250 g"), ("on the vine", "an der Rispe"), ("snack size", "Snackgröße")],
                ),
                item(
                    "Fresh Basil",
                    "Frischer Basilikum",
                    "Fresh basil plant for pesto, tomato sauce, salads, and Italian cooking.",
                    "Frischer Basilikumtopf für Pesto, Tomatensauce, Salate und italienische Küche.",
                    ["grocery", "fresh produce", "herbs", "basil", "pesto"],
                    ["lebensmittel", "frisch", "kräuter", "basilikum", "pesto"],
                    0.99,
                    2.49,
                    [("potted herb", "Kräutertopf"), ("organic", "bio"), ("extra fresh", "extra frisch")],
                ),
                item(
                    "Gala Apples",
                    "Gala Äpfel",
                    "Crisp apples for lunch boxes, baking, porridge, and everyday snacking.",
                    "Knackige Äpfel für Lunchboxen, Backen, Porridge und Snacks im Alltag.",
                    ["grocery", "fresh produce", "fruit", "apples"],
                    ["lebensmittel", "frisch", "obst", "äpfel"],
                    1.79,
                    3.49,
                    [("1 kg", "1 kg"), ("regional", "regional"), ("sweet and crisp", "süß und knackig")],
                ),
            ],
        },
        {
            "category": "bakery",
            "category_de": "bäckerei",
            "brands": ["EDEKA", "Harry", "Mestemacher", "Unser Bäcker"],
            "items": [
                item(
                    "Whole Grain Bread",
                    "Vollkornbrot",
                    "Sliced whole grain bread for sandwiches, breakfast, and packed lunches.",
                    "Geschnittenes Vollkornbrot für Sandwiches, Frühstück und Pausenbrot.",
                    ["grocery", "bakery", "bread", "whole grain", "breakfast"],
                    ["lebensmittel", "bäckerei", "brot", "vollkorn", "frühstück"],
                    1.29,
                    3.49,
                    [("500 g", "500 g"), ("seeded", "mit Saaten"), ("sliced", "geschnitten")],
                ),
                item(
                    "Pretzel Rolls",
                    "Laugenbrötchen",
                    "Soft pretzel rolls for breakfast, school lunches, and savory snacks.",
                    "Weiche Laugenbrötchen für Frühstück, Schulbrot und herzhafte Snacks.",
                    ["grocery", "bakery", "rolls", "pretzel rolls"],
                    ["lebensmittel", "bäckerei", "brötchen", "laugenbrötchen"],
                    0.79,
                    2.49,
                    [("4 pcs", "4 Stück"), ("fresh baked", "frisch gebacken"), ("with salt", "mit Salz")],
                ),
                item(
                    "Butter Croissants",
                    "Buttercroissants",
                    "Flaky croissants for breakfast, brunch, and coffee breaks.",
                    "Blättrige Croissants für Frühstück, Brunch und Kaffeepausen.",
                    ["grocery", "bakery", "croissant", "pastry", "breakfast"],
                    ["lebensmittel", "bäckerei", "croissant", "gebäck", "frühstück"],
                    1.49,
                    4.49,
                    [("4 pcs", "4 Stück"), ("bake-off", "zum Aufbacken"), ("buttery", "buttrig")],
                ),
            ],
        },
        {
            "category": "beverages",
            "category_de": "getränke",
            "brands": ["EDEKA", "Gut & Günstig", "Gerolsteiner", "Voelkel"],
            "items": [
                item(
                    "Sparkling Mineral Water",
                    "Mineralwasser Sprudel",
                    "Sparkling mineral water for everyday hydration, meals, and office use.",
                    "Sprudelndes Mineralwasser für Alltag, Mahlzeiten und Büro.",
                    ["grocery", "beverages", "water", "sparkling water"],
                    ["lebensmittel", "getränke", "wasser", "sprudel"],
                    0.49,
                    5.99,
                    [("1.5 l", "1,5 l"), ("6 pack", "6er-Pack"), ("returnable bottle", "Mehrwegflasche")],
                ),
                item(
                    "Orange Juice",
                    "Orangensaft",
                    "Fruit juice for breakfast, smoothies, and brunch drinks.",
                    "Fruchtsaft für Frühstück, Smoothies und Brunch-Getränke.",
                    ["grocery", "beverages", "orange juice", "breakfast"],
                    ["lebensmittel", "getränke", "orangensaft", "frühstück"],
                    1.29,
                    3.99,
                    [("1 l", "1 l"), ("not from concentrate", "Direktsaft"), ("with pulp", "mit Fruchtfleisch")],
                ),
                item(
                    "Ground Filter Coffee",
                    "Gemahlener Filterkaffee",
                    "Roasted ground coffee for filter machines, breakfast, and office kitchens.",
                    "Gerösteter gemahlener Kaffee für Filtermaschinen, Frühstück und Büroküchen.",
                    ["grocery", "beverages", "coffee", "filter coffee"],
                    ["lebensmittel", "getränke", "kaffee", "filterkaffee"],
                    3.49,
                    8.99,
                    [("500 g", "500 g"), ("medium roast", "mittlere Röstung"), ("aromatic", "aromatisch")],
                ),
            ],
        },
        {
            "category": "organic food",
            "category_de": "bio lebensmittel",
            "brands": ["EDEKA Bio", "Alnatura", "dmBio", "Bio Zentrale"],
            "items": [
                item(
                    "Organic Tomato Sauce",
                    "Bio-Tomatensauce",
                    "Organic tomato sauce for spaghetti, lasagna, pizza, and quick family meals.",
                    "Bio-Tomatensauce für Spaghetti, Lasagne, Pizza und schnelle Familiengerichte.",
                    ["grocery", "organic food", "tomato sauce", "pasta sauce", "bio"],
                    ["lebensmittel", "bio", "tomatensauce", "pastasauce", "bio-tomatensauce"],
                    1.49,
                    3.49,
                    [("400 g", "400 g"), ("with basil", "mit Basilikum"), ("chunky", "stückig")],
                ),
                item(
                    "Organic Oat Drink",
                    "Bio Haferdrink",
                    "Plant-based oat drink for coffee, cereal, smoothies, and vegan cooking.",
                    "Pflanzlicher Haferdrink für Kaffee, Müsli, Smoothies und veganes Kochen.",
                    ["grocery", "organic food", "oat drink", "vegan", "plant based"],
                    ["lebensmittel", "bio", "haferdrink", "vegan", "pflanzlich"],
                    1.29,
                    2.99,
                    [("1 l", "1 l"), ("barista", "Barista"), ("no added sugar", "ohne Zuckerzusatz")],
                ),
                item(
                    "Organic Breakfast Muesli",
                    "Bio Frühstücksmüsli",
                    "Organic oat muesli with seeds and dried fruit for breakfast bowls.",
                    "Bio-Hafermüsli mit Saaten und Trockenfrüchten für Frühstücksbowls.",
                    ["grocery", "organic food", "muesli", "breakfast", "oats"],
                    ["lebensmittel", "bio", "müsli", "frühstück", "hafer"],
                    2.49,
                    5.99,
                    [("750 g", "750 g"), ("berries", "Beeren"), ("no added sugar", "ohne Zuckerzusatz")],
                ),
            ],
        },
        {
            "category": "meat and fish",
            "category_de": "fleisch und fisch",
            "brands": ["EDEKA", "Gut & Günstig", "Biohof", "Nordsee"],
            "items": [
                item(
                    "Chicken Breast Fillet",
                    "Hähnchenbrustfilet",
                    "Fresh chicken breast fillet for stir-fries, salads, wraps, and meal prep.",
                    "Frisches Hähnchenbrustfilet für Pfannengerichte, Salate, Wraps und Meal Prep.",
                    ["grocery", "meat and fish", "chicken breast", "protein", "fresh meat"],
                    ["lebensmittel", "fleisch", "hähnchenbrust", "protein", "frischfleisch"],
                    4.99,
                    9.99,
                    [("400 g", "400 g"), ("skinless", "ohne Haut"), ("ready to cook", "küchenfertig")],
                ),
                item(
                    "Salmon Fillet",
                    "Lachsfilet",
                    "Fresh salmon fillet for oven dishes, pan frying, bowls, and healthy meals.",
                    "Frisches Lachsfilet für Ofengerichte, Pfanne, Bowls und gesunde Mahlzeiten.",
                    ["grocery", "meat and fish", "salmon", "fish", "protein"],
                    ["lebensmittel", "fisch", "lachs", "lachsfilet", "protein"],
                    6.99,
                    14.99,
                    [("250 g", "250 g"), ("skin on", "mit Haut"), ("fresh counter", "Frischetheke")],
                ),
                item(
                    "Minced Beef",
                    "Rinderhackfleisch",
                    "Minced beef for burgers, bolognese sauce, chili, and casseroles.",
                    "Rinderhack für Burger, Bolognese, Chili und Aufläufe.",
                    ["grocery", "meat and fish", "minced beef", "beef", "protein"],
                    ["lebensmittel", "fleisch", "rinderhack", "rind", "protein"],
                    3.99,
                    8.99,
                    [("500 g", "500 g"), ("lean", "mager"), ("fresh pack", "Frischepackung")],
                ),
            ],
        },
    ],
    "amazon": [
        {
            "category": "electronics",
            "category_de": "elektronik",
            "brands": ["Amazon Basics", "Anker", "Logitech", "Samsung"],
            "items": [
                item(
                    "Wireless Headphones",
                    "Kabellose Kopfhörer",
                    "Bluetooth over-ear headphones for music, video calls, travel, and commuting.",
                    "Bluetooth Over-Ear-Kopfhörer für Musik, Videocalls, Reisen und Pendeln.",
                    ["general merchandise", "electronics", "wireless headphones", "bluetooth", "audio"],
                    ["warenhaus", "elektronik", "kabellose kopfhörer", "bluetooth", "audio"],
                    24.99,
                    129.99,
                    [("black", "schwarz"), ("noise cancelling", "Noise Cancelling"), ("40h battery", "40h Akku")],
                ),
                item(
                    "USB-C Charging Cable",
                    "USB-C Ladekabel",
                    "Durable USB-C charging cable for phones, tablets, laptops, and power banks.",
                    "Robustes USB-C-Ladekabel für Smartphones, Tablets, Laptops und Powerbanks.",
                    ["general merchandise", "electronics", "usb-c", "charging cable", "phone cable"],
                    ["warenhaus", "elektronik", "usb-c", "ladekabel", "handykabel"],
                    5.99,
                    18.99,
                    [("1.8 m", "1,8 m"), ("fast charging", "Schnellladen"), ("braided", "geflochten")],
                ),
                item(
                    "Portable Power Bank",
                    "Mobile Powerbank",
                    "Compact portable charger with USB-C output for phones, headphones, and travel.",
                    "Kompakte mobile Powerbank mit USB-C-Ausgang für Smartphones, Kopfhörer und Reisen.",
                    ["general merchandise", "electronics", "power bank", "portable charger", "usb-c"],
                    ["warenhaus", "elektronik", "powerbank", "mobiles ladegerät", "usb-c"],
                    14.99,
                    39.99,
                    [("10000 mAh", "10000 mAh"), ("20W USB-C", "20W USB-C"), ("travel size", "Reisegröße")],
                ),
            ],
        },
        {
            "category": "kitchen accessories",
            "category_de": "küchenzubehör",
            "brands": ["KitchenAid", "WMF", "OXO", "Amazon Basics"],
            "items": [
                item(
                    "Stainless Steel Pan",
                    "Edelstahlpfanne",
                    "Durable frying pan for searing vegetables, eggs, meat, and everyday dinners.",
                    "Robuste Pfanne zum Anbraten von Gemüse, Eiern, Fleisch und Alltagsgerichten.",
                    ["general merchandise", "kitchen accessories", "stainless steel pan", "cookware"],
                    ["warenhaus", "küchenzubehör", "edelstahlpfanne", "kochgeschirr"],
                    24.99,
                    79.99,
                    [("28 cm", "28 cm"), ("induction", "Induktion"), ("oven safe", "ofenfest")],
                ),
                item(
                    "Digital Kitchen Scale",
                    "Digitale Küchenwaage",
                    "Precise kitchen scale for baking, coffee, meal prep, and portion control.",
                    "Präzise Küchenwaage zum Backen, für Kaffee, Meal Prep und Portionieren.",
                    ["general merchandise", "kitchen accessories", "kitchen scale", "baking"],
                    ["warenhaus", "küchenzubehör", "küchenwaage", "backen"],
                    8.99,
                    24.99,
                    [("5 kg", "5 kg"), ("with bowl", "mit Schüssel"), ("slim design", "flaches Design")],
                ),
                item(
                    "Insulated Water Bottle",
                    "Isolierte Trinkflasche",
                    "Stainless steel bottle that keeps drinks cold or hot for commuting and sports.",
                    "Edelstahlflasche hält Getränke kalt oder heiß für Pendeln und Sport.",
                    ["general merchandise", "kitchen accessories", "water bottle", "stainless steel"],
                    ["warenhaus", "küchenzubehör", "trinkflasche", "edelstahl"],
                    10.99,
                    29.99,
                    [("750 ml", "750 ml"), ("leak proof", "auslaufsicher"), ("matte black", "mattschwarz")],
                ),
            ],
        },
        {
            "category": "home office",
            "category_de": "homeoffice",
            "brands": ["Logitech", "Fellowes", "WorkLift", "Amazon Basics"],
            "items": [
                item(
                    "Ergonomic Office Mouse",
                    "Ergonomische Büromaus",
                    "Wireless ergonomic mouse for long workdays, spreadsheets, and laptop setups.",
                    "Kabellose ergonomische Maus für lange Arbeitstage, Tabellen und Laptop-Arbeitsplätze.",
                    ["general merchandise", "home office", "ergonomic mouse", "wireless mouse"],
                    ["warenhaus", "homeoffice", "ergonomische maus", "kabellose maus"],
                    14.99,
                    69.99,
                    [("right hand", "rechtshändig"), ("silent click", "leiser Klick"), ("Bluetooth", "Bluetooth")],
                ),
                item(
                    "LED Desk Lamp",
                    "LED Schreibtischlampe",
                    "Adjustable desk lamp with dimmable LED light for reading, studying, and work.",
                    "Verstellbare Schreibtischlampe mit dimmbarem LED-Licht zum Lesen, Lernen und Arbeiten.",
                    ["general merchandise", "home office", "desk lamp", "led light", "study"],
                    ["warenhaus", "homeoffice", "schreibtischlampe", "led licht", "lernen"],
                    18.99,
                    69.99,
                    [("with USB port", "mit USB-Anschluss"), ("warm white", "warmweiß"), ("touch control", "Touch-Bedienung")],
                ),
                item(
                    "Adjustable Laptop Stand",
                    "Verstellbarer Laptopständer",
                    "Aluminum laptop stand for ergonomic video calls, typing, and desk organization.",
                    "Laptopständer aus Aluminium für ergonomische Videocalls, Tippen und Ordnung am Schreibtisch.",
                    ["general merchandise", "home office", "laptop stand", "ergonomic"],
                    ["warenhaus", "homeoffice", "laptopständer", "ergonomisch"],
                    16.99,
                    59.99,
                    [("aluminum", "Aluminium"), ("foldable", "faltbar"), ("for 13-16 inch", "für 13-16 Zoll")],
                ),
            ],
        },
        {
            "category": "books",
            "category_de": "bücher",
            "brands": ["Penguin", "O'Reilly", "DK", "Rheinwerk"],
            "items": [
                item(
                    "Python Programming Book",
                    "Python Programmierbuch",
                    "Practical programming book with exercises, examples, and beginner-friendly explanations.",
                    "Praxisnahes Programmierbuch mit Übungen, Beispielen und verständlichen Erklärungen.",
                    ["general merchandise", "books", "programming", "python", "learning"],
                    ["warenhaus", "bücher", "programmierung", "python", "lernen"],
                    14.99,
                    49.99,
                    [("paperback", "Taschenbuch"), ("beginner guide", "Einsteigerbuch"), ("2nd edition", "2. Auflage")],
                ),
                item(
                    "Children's Picture Book",
                    "Kinder Bilderbuch",
                    "Illustrated story book for bedtime reading and early language development.",
                    "Illustriertes Geschichtenbuch zum Vorlesen und für frühe Sprachentwicklung.",
                    ["general merchandise", "books", "children book", "picture book"],
                    ["warenhaus", "bücher", "kinderbuch", "bilderbuch"],
                    5.99,
                    19.99,
                    [("hardcover", "Hardcover"), ("ages 3+", "ab 3 Jahren"), ("bedtime story", "Gutenachtgeschichte")],
                ),
                item(
                    "Everyday Cookbook",
                    "Alltags Kochbuch",
                    "Recipe book with simple weeknight meals, shopping lists, and family-friendly dishes.",
                    "Rezeptbuch mit einfachen Gerichten für die Woche, Einkaufslisten und Familienrezepten.",
                    ["general merchandise", "books", "cookbook", "recipes", "meal planning"],
                    ["warenhaus", "bücher", "kochbuch", "rezepte", "wochenplanung"],
                    9.99,
                    34.99,
                    [("quick meals", "schnelle Gerichte"), ("vegetarian chapter", "vegetarisches Kapitel"), ("hardcover", "Hardcover")],
                ),
            ],
        },
        {
            "category": "toys",
            "category_de": "spielzeug",
            "brands": ["LEGO", "Ravensburger", "Playmobil", "Hasbro"],
            "items": [
                item(
                    "Family Strategy Board Game",
                    "Familienspiel Strategiespiel",
                    "Board game for family game nights, tactical decisions, and two to five players.",
                    "Brettspiel für Familienabende, taktische Entscheidungen und zwei bis fünf Spieler.",
                    ["general merchandise", "toys", "board game", "family game", "strategy"],
                    ["warenhaus", "spielzeug", "brettspiel", "familienspiel", "strategie"],
                    12.99,
                    49.99,
                    [("ages 8+", "ab 8 Jahren"), ("2-5 players", "2-5 Spieler"), ("45 min", "45 Minuten")],
                ),
                item(
                    "Building Blocks Set",
                    "Bausteine Set",
                    "Creative building set for vehicles, houses, and imaginative play.",
                    "Kreatives Bauset für Fahrzeuge, Häuser und fantasievolles Spielen.",
                    ["general merchandise", "toys", "building blocks", "creative play"],
                    ["warenhaus", "spielzeug", "bausteine", "kreatives spielen"],
                    9.99,
                    89.99,
                    [("120 pcs", "120 Teile"), ("city theme", "Stadt-Thema"), ("storage box", "Aufbewahrungsbox")],
                ),
                item(
                    "Puzzle 1000 Pieces",
                    "Puzzle 1000 Teile",
                    "Large jigsaw puzzle for quiet evenings, weekends, and focused play.",
                    "Großes Puzzle für ruhige Abende, Wochenenden und konzentriertes Spielen.",
                    ["general merchandise", "toys", "puzzle", "1000 pieces"],
                    ["warenhaus", "spielzeug", "puzzle", "1000 teile"],
                    7.99,
                    24.99,
                    [("landscape", "Landschaft"), ("museum art", "Kunstmotiv"), ("premium cardboard", "Premium-Karton")],
                ),
            ],
        },
        {
            "category": "sports",
            "category_de": "sport",
            "brands": ["Nike", "Adidas", "FitLine", "Under Armour"],
            "items": [
                item(
                    "Non-Slip Yoga Mat",
                    "Rutschfeste Yogamatte",
                    "Cushioned exercise mat for yoga, stretching, pilates, and home workouts.",
                    "Gepolsterte Trainingsmatte für Yoga, Dehnen, Pilates und Workouts zu Hause.",
                    ["general merchandise", "sports", "yoga mat", "fitness", "home workout"],
                    ["warenhaus", "sport", "yogamatte", "fitness", "home workout"],
                    12.99,
                    44.99,
                    [("6 mm", "6 mm"), ("with carry strap", "mit Tragegurt"), ("extra long", "extra lang")],
                ),
                item(
                    "Lightweight Running Shoes",
                    "Leichte Laufschuhe",
                    "Neutral running shoes for road training, fitness runs, and daily walking.",
                    "Neutrale Laufschuhe für Straßentraining, Fitnessläufe und tägliches Gehen.",
                    ["general merchandise", "sports", "running shoes", "training"],
                    ["warenhaus", "sport", "laufschuhe", "training"],
                    39.99,
                    139.99,
                    [("men", "Herren"), ("women", "Damen"), ("road running", "Straßenlauf")],
                ),
                item(
                    "Resistance Bands Set",
                    "Fitnessbänder Set",
                    "Resistance bands for strength training, mobility exercises, and rehabilitation.",
                    "Fitnessbänder für Krafttraining, Mobilitätsübungen und Rehabilitation.",
                    ["general merchandise", "sports", "resistance bands", "strength training"],
                    ["warenhaus", "sport", "fitnessbänder", "krafttraining"],
                    8.99,
                    29.99,
                    [("5 bands", "5 Bänder"), ("with door anchor", "mit Türanker"), ("travel pouch", "Reisetasche")],
                ),
            ],
        },
        {
            "category": "home appliances",
            "category_de": "haushaltsgeräte",
            "brands": ["Philips", "Bosch", "KitchenPro", "Russell Hobbs"],
            "items": [
                item(
                    "Compact Air Fryer",
                    "Kompakte Heißluftfritteuse",
                    "Compact air fryer for fries, vegetables, chicken, and quick weeknight meals.",
                    "Kompakte Heißluftfritteuse für Pommes, Gemüse, Hähnchen und schnelle Alltagsgerichte.",
                    ["general merchandise", "home appliances", "air fryer", "kitchen appliance"],
                    ["warenhaus", "haushaltsgeräte", "heißluftfritteuse", "küchengerät"],
                    49.99,
                    129.99,
                    [("3.5 l", "3,5 l"), ("digital display", "Digitaldisplay"), ("low oil cooking", "fettarmes Kochen")],
                ),
                item(
                    "Robot Vacuum Cleaner",
                    "Saugroboter",
                    "Smart robot vacuum for hard floors, carpets, pet hair, and daily cleaning routines.",
                    "Smarter Saugroboter für Hartböden, Teppiche, Tierhaare und tägliche Reinigung.",
                    ["general merchandise", "home appliances", "robot vacuum", "cleaning"],
                    ["warenhaus", "haushaltsgeräte", "saugroboter", "reinigung"],
                    119.99,
                    349.99,
                    [("app control", "App-Steuerung"), ("pet hair", "Tierhaare"), ("self charging", "selbstladend")],
                ),
                item(
                    "Electric Kettle",
                    "Wasserkocher",
                    "Electric kettle for tea, coffee, instant meals, and fast boiling water.",
                    "Wasserkocher für Tee, Kaffee, Instant-Gerichte und schnell kochendes Wasser.",
                    ["general merchandise", "home appliances", "electric kettle", "tea"],
                    ["warenhaus", "haushaltsgeräte", "wasserkocher", "tee"],
                    19.99,
                    79.99,
                    [("1.7 l", "1,7 l"), ("temperature control", "Temperaturwahl"), ("stainless steel", "Edelstahl")],
                ),
            ],
        },
    ],
}


def build_catalog() -> list[Product]:
    """Build and validate the complete deterministic product catalog."""

    rng = random.Random(RANDOM_SEED)
    products: list[Product] = []

    for partner, categories in CATALOG_TEMPLATES.items():
        products.extend(_build_partner_products(partner, categories, rng))

    _validate_unique_ids(products)
    return products


def write_catalog(path: str | Path = OUTPUT_PATH) -> Path:
    """Write the generated catalog as pretty-formatted UTF-8 JSON."""

    catalog_path = Path(path)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    products = build_catalog()
    catalog_path.write_text(
        json.dumps(
            [product.model_dump(mode="json") for product in products],
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return catalog_path


def _build_partner_products(
    partner: str,
    categories: list[CategoryTemplate],
    rng: random.Random,
) -> list[Product]:
    products: list[Product] = []

    for index in range(1, PRODUCTS_PER_PARTNER + 1):
        category_template = categories[(index - 1) % len(categories)]
        item_index = ((index - 1) // len(categories)) % len(category_template["items"])
        item_template = category_template["items"][item_index]
        modifier_index = ((index - 1) // (len(categories) * len(category_template["items"]))) % len(
            item_template["modifiers"]
        )
        modifier_en, modifier_de = item_template["modifiers"][modifier_index]
        brand = rng.choice(category_template["brands"])
        product_id = f"{partner}-{index:03d}"

        products.append(
            Product(
                product_id=product_id,
                partner=partner,
                name=_join_name_parts(brand, item_template["name"], modifier_en),
                name_de=_join_name_parts(brand, item_template["name_de"], modifier_de),
                category=category_template["category"],
                description=_description(
                    item_template["description"],
                    modifier_en,
                    category_template["category"],
                ),
                description_de=_description_de(
                    item_template["description_de"],
                    modifier_de,
                    category_template["category_de"],
                ),
                brand=brand,
                price=_price(rng, item_template["price_min"], item_template["price_max"]),
                currency="EUR",
                tags=[
                    partner,
                    category_template["category"],
                    modifier_en,
                    *item_template["tags"],
                ],
                tags_de=[
                    partner,
                    category_template["category_de"],
                    modifier_de,
                    *item_template["tags_de"],
                ],
                availability=rng.random() > 0.08,
                popularity_score=round(rng.uniform(0.25, 0.98), 2),
                is_promotion=rng.random() < 0.22,
                product_url=_product_url(partner, product_id),
            )
        )

    return products


def _join_name_parts(*parts: str) -> str:
    return " ".join(part for part in parts if part).strip()


def _description(base_description: str, modifier: str, category: str) -> str:
    return (
        f"{base_description} The {modifier} variant is useful for search queries "
        f"about {category}, brand preferences, product size, and household shopping intent."
    )


def _description_de(base_description: str, modifier: str, category_de: str) -> str:
    return (
        f"{base_description} Die Variante {modifier} ist relevant für Suchanfragen "
        f"zu {category_de}, Marke, Packungsgröße und Einkaufsabsicht."
    )


def _price(rng: random.Random, minimum: float, maximum: float) -> float:
    return round(rng.uniform(minimum, maximum), 2)


def _product_url(partner: str, product_id: str) -> str:
    partner_domains = {
        "dm": "https://www.dm.example/product",
        "edeka": "https://www.edeka.example/product",
        "amazon": "https://www.amazon.example/dp",
    }
    return f"{partner_domains[partner]}/{product_id}"


def _validate_unique_ids(products: list[Product]) -> None:
    product_ids = [product.product_id for product in products]
    duplicate_ids = {
        product_id for product_id in product_ids if product_ids.count(product_id) > 1
    }
    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"duplicate product_id values: {duplicates}")


def main() -> None:
    products = build_catalog()
    catalog_path = write_catalog()
    print(f"Wrote {len(products)} products to {catalog_path}")


if __name__ == "__main__":
    main()
