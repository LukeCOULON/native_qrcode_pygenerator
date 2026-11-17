# QRNativeGen 🐍

**QRNativeGen** is a QR Code generator written entirely in native Python, without any external dependencies.

It allows you to convert an IP address, URL or text into a QR Code, display it directly in your terminal and export it as a PNG image.

## ✨ Features

- Local QR Code generation.
- IPv4 and IPv6 support.
- HTTP and HTTPS URL support.
- UTF-8 encoding.
- Terminal QR Code display.
- PNG image export.
- Customizable image resolution.
- Reed-Solomon error correction.
- Automatic QR mask selection.
- No external dependencies.
- Python standard library only.

## 📋 Requirements

- Python 3.8 or newer.
- No additional packages required.

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/LukeCOULON/native_qrcode_pygenerator.git
```

Navigate to the project directory:

```bash
cd native_qrcode_pygenerator
```

No additional installation is required.

## 🚀 Usage

### Display a QR Code

```bash
python qrnativegen.py https://google.com
```

### Generate a QR Code from an IP address

```bash
python qrnativegen.py 192.168.1.1
```

### Save as PNG

```bash
python qrnativegen.py https://google.com --save
```

By default, the generated image is saved as:

```text
qrcode.png
```

### Choose a custom filename

```bash
python qrnativegen.py https://google.com --save google.png
```

### Customize image resolution

```bash
python qrnativegen.py https://google.com --save google.png --scale 15
```

The `--scale` option defines the number of pixels used for each QR Code module.

## ⚙️ Available options

| Argument | Description |
|---|---|
| `target` | IP address, URL or text to encode |
| `--save` | Save the QR Code as PNG |
| `--save filename.png` | Choose the output filename |
| `--scale N` | Set image resolution |
| `--help` | Display help |

## 🧠 Technical implementation

QRNativeGen implements the core mechanisms of QR Code Model 2:

- **Byte Mode:** data encoding.
- **UTF-8:** international character support.
- **GF(256):** Galois field arithmetic.
- **Reed-Solomon:** error correction.
- **Interleaving:** data and error correction block interleaving.
- **Finder Patterns:** position detection patterns.
- **Alignment Patterns:** alignment patterns.
- **Timing Patterns:** synchronization patterns.
- **BCH Encoding:** format and version information.
- **Mask Selection:** automatic selection among eight masks.
- **PNG Encoder:** image generation without external graphics libraries.

## 📐 Specifications

| Specification | Value |
|---|---|
| Standard | QR Code Model 2 |
| Versions | 1–10 |
| Encoding | Byte Mode / UTF-8 |
| Error correction | ECC-L |
| Masks | 0–7 |
| Export format | PNG |
| Dependencies | None |

## 📁 Project structure

```text
native_qrcode_pygenerator/
│
├── qrnativegen.py
├── README.md
└── qrcode.png
```

## 🔒 Privacy

QRNativeGen runs entirely locally.

- No data is sent to external servers.
- No Internet connection is required to generate QR Codes.
- No external libraries are used.

An Internet connection may still be required to access a generated QR Code pointing to a remote website.

## ⚠️ Limitations

- Supported QR versions: 1 to 10.
- Error correction level: ECC-L.
- Byte Mode encoding only.
- Maximum capacity depends on the QR version and payload size.

## 📜 License

See the repository for licensing information.

---

**QRNativeGen** — Native Python QR Code Generator.

Made with Python 🐍

**GitHub:** https://github.com/LukeCOULON/native_qrcode_pygenerator
