<div align="center">

# DupSense<span style="color:#4edea3">_</span>
**Premium Local Storage Manager**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

*Reclaim your storage. Zero cloud required.*

</div>

---

## 📌 Overview
**DupSense** is a high-fidelity, standalone desktop utility engineered to find and eliminate wasted storage space safely. Built with Python and Streamlit, it features a stunning dark-mode interface and utilizes advanced algorithms to detect exact binary duplicates, near-duplicate images, and heavily identical text files.

Unlike cloud-based cleaners, **all processing is 100% local**. Your files never leave your machine.

---

## ✨ Pro-Level Features

*   **🛡️ Absolute Directory Protection (Safe Zones)**
    Declare critical paths (e.g., `C:\Windows`). DupSense will scan them to find duplicates elsewhere, but will actively block you from ever modifying or deleting the protected originals.
*   **🖼️ AI Image Diffing (pHash)**
    Uses perceptual hashing to find images that are visually identical, even if compressed, resized, or watermarked. Features a Side-by-Side compare mode for high-res visual inspection.
*   **📝 Fuzzy Text Matching**
    Powered by `thefuzz`. Scans `.txt`, `.md`, and code files to detect versions that are >90% identical in content, catching the "final_v2_edit.txt" clutter.
*   **🗺️ Interactive Treemaps**
    Stop guessing where your storage went. View massive Plotly-powered Treemaps that visualize your entire directory hierarchy and pinpoint exactly which folders are hoarding the most duplicates.
*   **🗄️ Quarantine Manager**
    Never permanently delete by mistake. Move suspect files to a dedicated staging Quarantine, where you can safely restore them to their original location with one click.
*   **🧠 Smart Auto-Select**
    Configure the engine to automatically prefer keeping the `Oldest Created`, `Newest Created`, `Largest File Size`, or `Shortest File Path`.

---

## 🚀 Installation & Usage

### Option 1: Standalone Windows App
The easiest way to use DupSense is to download the compiled `.exe` from the [Releases Tab](../../releases). No Python installation required!

### Option 2: Run Locally (Developers)
If you wish to run the app via Python or contribute to the source code:

1. **Clone the repository**
   ```bash
   git clone https://github.com/rizzit17/DupSense.git
   cd DupSense
   ```

2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have `thefuzz` and `python-Levenshtein` installed for the AI text matching module).*

3. **Launch the Dashboard**
   ```bash
   streamlit run app.py
   ```

---

## 📦 Compiling the Executable
If you want to build the `.exe` yourself:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "app.py;." run_dupsense.py
```
*The compiled executable will appear in the `dist/` directory.*

---

## 🌐 Landing Page & Deployment
A beautifully styled Vercel landing page is included in the `/website` directory.
- Built with raw HTML and Tailwind CSS (CDN).
- Designed to match a "Premium Editorial Dark" portfolio aesthetic.
- Deployed simply by pointing Vercel's Root Directory setting to the `/website` folder.

---

<div align="center">
  Built with ❤️ locally. Protected completely. 
</div>
