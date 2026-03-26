# 🔍 DupeFinder AI — Smart Duplicate File Finder

A Streamlit-based desktop utility that scans your folders for duplicate and similar files using MD5 hashing, perceptual image hashing, and filename analysis.

---

## ✨ Features

| Feature | Tech Used |
|---|---|
| Exact duplicate detection | MD5 hashing |
| Near-duplicate image detection | Perceptual hashing (pHash via `imagehash`) |
| Similar filename grouping | Path stem comparison |
| Space waste visualization | Plotly charts |
| Safe quarantine / delete | `shutil`, `os` |
| Dark cyber UI | Custom Streamlit CSS |

---

## 🚀 Setup & Run

### 1. Clone / download the project
```bash
git clone https://github.com/yourusername/dupefinder-ai
cd dupefinder-ai
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## 🗂️ Project Structure
```
dupefinder-ai/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 🧠 How It Works

1. **Exact Duplicates (MD5)** — Reads every file in chunks and computes an MD5 hash. Files with identical hashes are guaranteed to be byte-for-byte identical.

2. **Near-Duplicate Images (pHash)** — Opens each image with Pillow, converts it to a perceptual hash (a fingerprint based on visual content), then compares hashes using Hamming distance. Images within the threshold distance are flagged as near-duplicates.

3. **Similar Names** — Groups files that share the same filename stem (e.g., `report.docx` and `report.pdf`) so you can decide which version to keep.

---

## 📸 Resume Talking Points

- "Used **MD5 hashing** for O(n) exact duplicate detection instead of O(n²) pairwise comparison"
- "Implemented **perceptual hashing** (pHash) for AI-powered image similarity without any ML model training"
- "Built a quarantine system to safely stage files before permanent deletion"
- "Visualized disk waste per duplicate group using **Plotly** interactive charts"

---

## 🛡️ Safety
- All processing is **100% local** — no files are uploaded anywhere
- **Quarantine mode** moves files to a safe folder instead of deleting immediately
- The oldest file in each group is automatically marked as the "original" to keep

---

*Built with ❤️ using Streamlit, Pillow, imagehash, Plotly*