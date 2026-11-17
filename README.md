# QRNativeGen 🐍

**QRNativeGen** est un générateur de QR Codes développé entièrement en Python natif, sans aucune bibliothèque externe.

Il permet de convertir une adresse IP, une URL ou du texte en QR Code, de l'afficher directement dans le terminal et de l'exporter au format PNG.

## ✨ Fonctionnalités

- Génération de QR Codes en local.
- Support des adresses IPv4 et IPv6.
- Support des URLs HTTP et HTTPS.
- Encodage des données en UTF-8.
- Affichage directement dans le terminal.
- Export au format PNG.
- Choix de la résolution de l'image.
- Correction d'erreurs Reed-Solomon.
- Sélection automatique du masque QR.
- Aucune dépendance externe.
- Utilisation exclusive de la bibliothèque standard Python.

## 📋 Prérequis

- Python 3.8 ou supérieur.
- Aucun paquet externe à installer.

## 📦 Installation

Clone le dépôt :

```bash
git clone https://github.com/USERNAME/QRNativeGen.git
```

Accède au répertoire :

```bash
cd QRNativeGen
```

Aucune installation supplémentaire n'est nécessaire.

## 🚀 Utilisation

### Afficher un QR Code

```bash
python qrnativegen.py https://google.com
```

### Générer un QR Code à partir d'une IP

```bash
python qrnativegen.py 192.168.1.1
```

### Enregistrer en PNG

```bash
python qrnativegen.py https://google.com --save
```

Par défaut, le fichier sera enregistré sous :

```text
qrcode.png
```

### Personnaliser le nom du fichier

```bash
python qrnativegen.py https://google.com --save google.png
```

### Modifier la résolution

```bash
python qrnativegen.py https://google.com --save google.png --scale 15
```

Le paramètre `--scale` définit le nombre de pixels utilisés pour représenter chaque module du QR Code.

## ⚙️ Options disponibles

| Argument | Description |
|---|---|
| `target` | IP, URL ou texte à encoder |
| `--save` | Enregistre le QR Code en PNG |
| `--save fichier.png` | Définit le nom du fichier |
| `--scale N` | Définit la résolution de l'image |
| `--help` | Affiche l'aide |

## 🧠 Fonctionnement technique

QRNativeGen implémente directement les mécanismes de génération des QR Codes Model 2 :

- **Byte Mode** : encodage des données.
- **UTF-8** : prise en charge des caractères internationaux.
- **GF(256)** : opérations dans un corps de Galois.
- **Reed-Solomon** : correction des erreurs.
- **Interleaving** : entrelacement des blocs de données.
- **Finder Patterns** : motifs de localisation.
- **Alignment Patterns** : motifs d'alignement.
- **Timing Patterns** : motifs de synchronisation.
- **BCH Encoding** : informations de format et de version.
- **Mask Selection** : sélection automatique parmi les huit masques.
- **PNG Encoder** : génération d'images sans bibliothèque graphique externe.

## 📐 Spécifications

| Caractéristique | Valeur |
|---|---|
| Standard | QR Code Model 2 |
| Versions | 1 à 10 |
| Encodage | Byte Mode / UTF-8 |
| Correction d'erreurs | ECC-L |
| Masques | 0 à 7 |
| Format d'export | PNG |
| Dépendances | Aucune |

## 📁 Structure du projet

```text
QRNativeGen/
│
├── qrnativegen.py
├── README.md
└── qrcode.png
```

## 🔒 Confidentialité

QRNativeGen fonctionne entièrement en local.

- Aucune donnée n'est envoyée à un serveur.
- Aucune connexion Internet n'est nécessaire pour générer un QR Code.
- Aucune bibliothèque externe n'est utilisée.

La connexion Internet reste évidemment nécessaire pour accéder à une URL encodée qui pointe vers un site distant.

## ⚠️ Limitations

- Versions QR prises en charge : 1 à 10.
- Niveau de correction d'erreurs : ECC-L.
- Encodage Byte Mode uniquement.
- Capacité maximale dépendante de la version et de la taille des données.

## 📜 Licence

Projet libre d'utilisation, de modification et de distribution.

---

**QRNativeGen** — Native Python QR Code Generator.

*Made with Python 🐍*
