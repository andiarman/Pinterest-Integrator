# Pinterest Integrator for SketchUp

🔗 Integrasi Pinterest → GitHub → SketchUp untuk koleksi material dan tekstur.

## 🎯 Overview

Sistem ini memungkinkan Anda untuk:
- **Pin dari HP/Tablet/Laptop** → Otomatis masuk ke library SketchUp
- **Zero Maintenance** → Tidak perlu server atau database berbayar
- **Multi-Device Sync** → GitHub sebagai "database" gratis

## 📁 Project Structure

```
integrator/
├── index.html          # Frontend Material Library UI
├── styles.css          # Dark theme styling
├── app.js              # JavaScript application logic
├── config.json         # Pinterest board configuration
├── data/
│   └── library.json    # Material database
├── scripts/
│   ├── sync_pinterest.py    # Python sync script
│   └── requirements.txt     # Python dependencies
└── .github/
    └── workflows/
        └── sync-pinterest.yml  # GitHub Actions workflow
```

## 🚀 Quick Start

### 1. Fork Repository
Fork repo ini ke akun GitHub Anda.

### 2. Configure Boards
Edit `config.json` dan tambahkan URL board Pinterest Anda:

```json
{
    "boards": [
        {
            "name": "Tekstur Kayu",
            "url": "https://pinterest.com/yourusername/tekstur-kayu"
        }
    ]
}
```

### 3. Enable GitHub Actions
- Buka Settings → Actions → General
- Pilih "Allow all actions"
- Enable "Read and write permissions" untuk workflow

### 4. Run Sync
- Buka tab "Actions"
- Pilih "Sync Pinterest Boards"
- Klik "Run workflow"

### 5. Access Library
Setelah sync, akses library di:
```
https://raw.githubusercontent.com/USERNAME/REPO/main/data/library.json
```

## ⚙️ Configuration

### config.json

| Field | Description |
|-------|-------------|
| `boards` | Array of Pinterest boards to sync |
| `tag_mappings` | Auto-tagging keywords |
| `excluded_keywords` | Filter out unwanted pins |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PINTEREST_BOARDS` | JSON array of board URLs (optional override) |

## 🎨 Frontend Features

- **Visual Grid** - Pinterest-style material display
- **Search** - Real-time search by name/tag
- **Filter** - Filter by category (Kayu, Batik, Batu, dll)
- **One-Click Apply** - Ready for SketchUp integration

## 🔧 Development

### Run Locally

```bash
# Serve with Python
python -m http.server 8000

# Open browser
# http://localhost:8000
```

### Test Sync Script

```bash
cd scripts
pip install -r requirements.txt
python sync_pinterest.py
```

## 📦 SketchUp Integration (Coming Soon)

The frontend is designed to work inside SketchUp's WebDialog. The `window.PinterestIntegrator` object provides bridge functions for Ruby integration.

## 📝 License

MIT License - Feel free to use and modify!
