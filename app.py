import streamlit as st
import os
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict
from PIL import Image
import imagehash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import humanize  # pip install humanize
import io
import base64
from fpdf import FPDF
try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DupSense",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  (dark cyber aesthetic)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: #131313;
    color: #e5e2e1;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1c1b1b;
    border-right: 1px solid #353534;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #1c1b1b;
    border: 1px solid #353534;
    border-radius: 0.75rem;
    padding: 16px;
}

/* Buttons */
.stButton > button {
    background: #4edea3;
    color: #003824;
    border: none;
    border-radius: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.05em;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #6ffbbe;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(78, 222, 163, 0.2);
    color: #002113;
}

/* Danger button */
.danger-btn > button {
    background: #ffb4ab !important;
    color: #690005 !important;
}
.danger-btn > button:hover {
    background: #ffdad6 !important;
    box-shadow: 0 4px 12px rgba(255, 180, 171, 0.2) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: #4edea3;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #86948a !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #4edea3 !important;
    border-bottom-color: #4edea3 !important;
}

/* Expander */
details {
    background: #1c1b1b;
    border: 1px solid #353534;
    border-radius: 0.5rem;
}

/* DataFrames */
.stDataFrame {
    border: 1px solid #353534;
    border-radius: 0.5rem;
}

/* Title */
.title-glow {
    font-family: 'Inter', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    color: #e5e2e1;
    letter-spacing: -0.04em;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-family: 'JetBrains Mono', monospace;
    color: #86948a;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    margin-bottom: 2rem;
}

/* Duplicate group card */
.dup-card {
    background: #1c1b1b;
    border: 1px solid #353534;
    border-left: 3px solid #4edea3;
    border-radius: 0.5rem;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #bbcabf;
}

.dup-card .original {
    color: #4edea3;
    font-weight: 700;
}

.dup-card .duplicate {
    color: #ffb4ab;
}

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
}

.badge-exact { background: #353534; color: #4edea3; }
.badge-image { background: #353534; color: #89ceff; }
.badge-name  { background: #353534; color: #10b981; }

.stat-row {
    display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.5rem;
}
.stat-box {
    flex: 1; min-width: 130px;
    background: #1c1b1b;
    border: 1px solid #353534;
    border-radius: 0.75rem;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
}
.stat-box:hover {
    transform: translateY(-4px);
    border-color: #4edea3;
    box-shadow: 0 8px 24px rgba(78, 222, 163, 0.1);
}
.stat-box .val {
    font-size: 1.4rem;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
    color: #4edea3;
    margin: 8px 0;
}
.stat-box .lbl {
    font-size: 0.85rem;
    color: #e5e2e1;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.stat-box .desc {
    font-size: 0.75rem;
    color: #86948a;
    margin-top: 8px;
    line-height: 1.4;
}

.cta-box {
    background: linear-gradient(135deg, rgba(78,222,163,0.1), rgba(0,0,0,0));
    border: 1px solid #4edea3;
    border-radius: 0.75rem;
    padding: 20px;
    text-align: center;
    margin-top: 2rem;
    font-family: 'JetBrains Mono', monospace;
    color: #e5e2e1;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_file_hash(filepath: str, chunk_size: int = 65536) -> str:
    """Compute MD5 hash of a file (fast exact-duplicate detection)."""
    hasher = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None


def get_image_hash(filepath: str) -> str:
    """Compute perceptual hash for images (near-duplicate detection)."""
    try:
        img = Image.open(filepath)
        return str(imagehash.phash(img))
    except Exception:
        return None


def is_safe(filepath: str, safe_zones: list) -> bool:
    """Check if a file path falls under any defined Safe Zones."""
    if not safe_zones:
        return False
    target = os.path.normpath(filepath).lower()
    for sz in safe_zones:
        if target.startswith(os.path.normpath(sz).lower()):
            return True
    return False


def get_original(files: list, strategy: str, safe_zones: list) -> dict:
    """Determine which file in a group should be kept as the original."""
    safe_files = [f for f in files if is_safe(f["path"], safe_zones)]
    candidates = safe_files if safe_files else files
    
    if strategy == "Oldest Created":
        return min(candidates, key=lambda f: f["modified"])
    elif strategy == "Newest Created":
        return max(candidates, key=lambda f: f["modified"])
    elif strategy == "Shortest File Path":
        return min(candidates, key=lambda f: len(f["path"]))
    elif strategy == "Largest File Size":
        return max(candidates, key=lambda f: f["size"])
    return candidates[0]


def scan_directory(folder: str, scan_subfolders: bool = True,
                   check_images: bool = True, check_names: bool = True,
                   check_text: bool = True,
                   image_threshold: int = 10, min_size_bytes: int = 0,
                   exclude_exts: list = None):
    """
    Scan a directory for:
    1. Exact duplicates   → same MD5 hash
    2. Near-duplicate images → perceptual hash distance ≤ threshold
    3. Similar file names → same stem, different extension
    Returns a dict with results and statistics.
    """
    if exclude_exts is None:
        exclude_exts = []
    
    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    all_files = []
    progress = st.progress(0, text="📂 Collecting files…")

    # Walk directory
    if scan_subfolders:
        walker = os.walk(folder)
    else:
        walker = [(folder, [], os.listdir(folder))]

    for root, dirs, files in walker:
        # Skip hidden / system folders
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname.startswith("."):
                continue
            full = os.path.join(root, fname)
            try:
                size = os.path.getsize(full)
                ext = Path(fname).suffix.lower()
                
                if size < min_size_bytes:
                    continue
                if ext in exclude_exts:
                    continue
                
                all_files.append({
                    "path": full,
                    "name": fname,
                    "stem": Path(fname).stem.lower(),
                    "ext": ext,
                    "size": size,
                    "modified": datetime.fromtimestamp(os.path.getmtime(full)),
                    "is_image": ext in IMAGE_EXTS,
                })
            except OSError:
                pass

    total = len(all_files)
    if total == 0:
        progress.empty()
        return None

    # ── 1. Exact duplicates via MD5 ──────────────────────────────────
    hash_map = defaultdict(list)
    for i, f in enumerate(all_files):
        progress.progress((i + 1) / total, text=f"🔍 Hashing files… ({i+1}/{total})")
        h = get_file_hash(f["path"])
        if h:
            f["hash"] = h
            hash_map[h].append(f)

    exact_groups = {h: files for h, files in hash_map.items() if len(files) > 1}

    # ── 2. Near-duplicate images ────────────────────────────────────
    image_groups = []
    if check_images:
        images = [f for f in all_files if f["is_image"]]
        img_hashes = []
        for i, f in enumerate(images):
            progress.progress((i + 1) / len(images) if images else 1,
                              text=f"Comparing images… ({i+1}/{len(images)})")
            ih = get_image_hash(f["path"])
            if ih:
                img_hashes.append((f, ih))

        # Pairwise comparison — group near-duplicates
        used = set()
        for i, (f1, h1) in enumerate(img_hashes):
            if f1["path"] in used:
                continue
            group = [f1]
            for j, (f2, h2) in enumerate(img_hashes):
                if i == j or f2["path"] in used:
                    continue
                dist = imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)
                if 0 < dist <= image_threshold:
                    group.append(f2)
            if len(group) > 1:
                for g in group:
                    used.add(g["path"])
                # Only add if not already caught as exact duplicate
                group_paths = {g["path"] for g in group}
                already_exact = any(
                    group_paths.issubset({f["path"] for f in files})
                    for files in exact_groups.values()
                )
                if not already_exact:
                    image_groups.append(group)

    # ── 3. Similar file names ────────────────────────────────────────
    name_groups = []
    if check_names:
        stem_map = defaultdict(list)
        for f in all_files:
            stem_map[f["stem"]].append(f)
        for stem, files in stem_map.items():
            exts = {f["ext"] for f in files}
            if len(exts) > 1 and len(files) > 1:
                name_groups.append(files)

    # ── 4. Near-duplicate text (Fuzzy Matching) ─────────────────────
    text_groups = []
    if check_text and fuzz:
        TEXT_EXTS = {".txt", ".md", ".csv", ".json", ".py", ".js", ".html"}
        texts = [f for f in all_files if f["ext"] in TEXT_EXTS]
        text_contents = []
        for i, f in enumerate(texts):
            progress.progress((i + 1) / len(texts) if texts else 1, text=f"Reading text files… ({i+1}/{len(texts)})")
            try:
                with open(f["path"], "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read(10000)
                    if content.strip():
                        text_contents.append((f, content))
            except Exception:
                pass
        
        visited = set()
        for i in range(len(text_contents)):
            if i in visited: continue
            f1, c1 = text_contents[i]
            group = [f1]
            progress.progress((i + 1) / len(text_contents), text=f"Fuzzy matching text… ({i+1}/{len(text_contents)})")
            for j in range(i + 1, len(text_contents)):
                if j in visited: continue
                f2, c2 = text_contents[j]
                if fuzz.token_sort_ratio(c1, c2) > 90:
                    group.append(f2)
                    visited.add(j)
            
            if len(group) > 1:
                text_groups.append(group)

    progress.empty()

    # ── Stats ────────────────────────────────────────────────────────
    exact_waste = sum(
        sum(f["size"] for f in files[1:])
        for files in exact_groups.values()
    )
    return {
        "total_files": total,
        "exact_groups": exact_groups,
        "image_groups": image_groups,
        "name_groups": name_groups,
        "text_groups": text_groups,
        "exact_waste_bytes": exact_waste,
        "all_files": all_files,
    }


def format_size(n_bytes: int) -> str:
    return humanize.naturalsize(n_bytes, binary=True)


def safe_delete(filepath: str) -> bool:
    try:
        os.remove(filepath)
        return True
    except OSError:
        return False


def move_to_quarantine(filepath: str, quarantine_dir: str) -> bool:
    try:
        os.makedirs(quarantine_dir, exist_ok=True)
        dest = os.path.join(quarantine_dir, os.path.basename(filepath))
        # Avoid name collision
        if os.path.exists(dest):
            base, ext = os.path.splitext(dest)
            dest = f"{base}_{int(datetime.now().timestamp())}{ext}"
        shutil.move(filepath, dest)
        return True
    except OSError:
        return False


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    folder_input = st.text_input(
        "📁 Folder Path",
        placeholder="e.g. C:\\Users\\You\\Documents",
        help="Paste the full path to the folder you want to scan."
    )

    scan_subfolders = st.toggle("Scan Subfolders", value=True)

    st.markdown("**Detection Methods**")
    detect_exact  = st.checkbox("Exact Duplicates (MD5 Hash)", value=True)
    detect_images = st.checkbox("Near-Duplicate Images (AI)", value=True)
    detect_names  = st.checkbox("Similar File Names",          value=True)
    detect_text   = st.checkbox("Text Content Similarity (AI)", value=True)

    if detect_images:
        img_threshold = st.slider(
            "Image Similarity Threshold",
            min_value=1, max_value=20, value=10,
            help="Lower = stricter match. 10 is a good default."
        )
    else:
        img_threshold = 10

    st.markdown("**Smart Selection**")
    auto_select_strategy = st.selectbox(
        "Auto-Select Original By",
        ["Oldest Created", "Newest Created", "Shortest File Path", "Largest File Size"],
        index=0,
        help="How the app decides which file is the 'Original'."
    )
    
    safe_zones_input = st.text_area(
        "Safe Zones (Folder Paths)",
        placeholder="e.g. C:\\Windows\nC:\\ImportantDocs",
        help="Files in these folders will NEVER be automatically deleted."
    )
    safe_zones_list = [sz.strip() for sz in safe_zones_input.split("\n") if sz.strip()]

    st.markdown("**Advanced Filters**")
    min_size_kb = st.number_input("Minimum File Size (KB)", min_value=0, value=0, help="Ignore files smaller than this size.")
    exclude_exts_input = st.text_input("Exclude Extensions", placeholder=".exe, .dll", help="Comma-separated list of extensions to ignore.")
    
    exclude_exts_list = []
    if exclude_exts_input:
        exclude_exts_list = [ext.strip().lower() for ext in exclude_exts_input.split(",") if ext.strip()]
        # ensure they start with dot
        exclude_exts_list = [ext if ext.startswith(".") else f".{ext}" for ext in exclude_exts_list]

    st.divider()
    action = st.radio(
        "🗑️ Action on Duplicates",
        ["Move to Quarantine Folder", "Permanently Delete"],
        index=0,
        help="Quarantine is safer - you can review before deleting permanently."
    )

    quarantine_path = ""
    if action == "Move to Quarantine Folder":
        quarantine_path = st.text_input(
            "Quarantine Path",
            value=os.path.join(os.path.expanduser("~"), "DupeFinder_Quarantine"),
        )

    scan_btn = st.button("Start Scan", use_container_width=True)

    st.divider()
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#334155;line-height:1.8'>
    All processing is <b>local</b>.<br>
    No files leave your machine.<br><br>
    <b>Tip:</b> Always quarantine<br>before deleting permanently.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────
st.markdown('<div class="title-glow">DupeFinder AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">// SMART DUPLICATE FILE DETECTION & CLEANUP</div>', unsafe_allow_html=True)

if scan_btn:
    st.session_state['run_scan'] = True

# ── Welcome state ────────────────────────────
if not st.session_state.get('run_scan', False):
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="stat-box">
            <div class="val">MD5 Hashing</div>
            <div class="lbl">Exact Duplicates</div>
            <div class="desc">Scans files byte-for-byte to guarantee 100% accurate detection of identical files, regardless of their names.</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stat-box">
            <div class="val">pHash Engine</div>
            <div class="lbl">Image Similarity</div>
            <div class="desc">Uses perceptual hashing to find images that look visually identical, even if resized, compressed, or reformatted.</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="stat-box">
            <div class="val">Stem Grouping</div>
            <div class="lbl">Similar Names</div>
            <div class="desc">Groups files that share the exact same base name but have different extensions (e.g., report.docx & report.pdf).</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="cta-box">
        Configure your parameters in the sidebar and click <b>Start Scan</b> to clean your system.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Validate folder ──────────────────────────
if not folder_input or not os.path.isdir(folder_input):
    st.error("❌ Please enter a valid folder path in the sidebar.")
    st.session_state['run_scan'] = False
    st.stop()

# ── Run scan ─────────────────────────────────
if scan_btn or 'scan_results' not in st.session_state:
    with st.spinner("Scanning… this may take a moment for large folders."):
        results = scan_directory(
            folder=folder_input,
            scan_subfolders=scan_subfolders,
            check_images=detect_images,
            check_names=detect_names,
            check_text=detect_text,
            image_threshold=img_threshold,
            min_size_bytes=min_size_kb * 1024,
            exclude_exts=exclude_exts_list,
        )
        st.session_state['scan_results'] = results
else:
    results = st.session_state['scan_results']

if results is None:
    st.warning("No files found in the selected folder.")
    st.session_state['run_scan'] = False
    st.stop()

# ── Summary metrics ──────────────────────────
st.markdown("### Scan Summary")

eg = results["exact_groups"]
ig = results["image_groups"]
ng = results["name_groups"]
tg = results.get("text_groups", [])
waste = results["exact_waste_bytes"]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Files",        results["total_files"])
m2.metric("Exact Dup Groups",   len(eg))
m3.metric("Image Dup Groups",   len(ig))
m4.metric("Name-Similar Groups",len(ng))
m5.metric("Recoverable Space",  format_size(waste))

st.divider()

col_exp1, col_exp2 = st.columns(2)
with col_exp1:
    # CSV Export
    csv_data = []
    for h, files in eg.items():
        original = get_original(files, auto_select_strategy, safe_zones_list)
        for f in files:
            if f["path"] != original["path"]:
                csv_data.append({
                    "Original File": original["path"], 
                    "Duplicate Found": f["path"], 
                    "Space Wasted": format_size(f["size"])
                })
    if csv_data:
        df_csv = pd.DataFrame(csv_data)
        csv_bytes = df_csv.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Duplicates to CSV",
            data=csv_bytes,
            file_name="duplicates_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.button("📥 Export Duplicates to CSV", disabled=True, use_container_width=True)

with col_exp2:
    # PDF Export
    if eg:
        def generate_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=16)
            pdf.cell(200, 10, text="DupeFinder AI - Scan Report", new_x="LMARGIN", new_y="NEXT", align='C')
            pdf.set_font("Helvetica", size=12)
            pdf.cell(200, 10, text=f"Total Space Wasted: {format_size(waste)}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            
            def safe_text(t):
                return str(t).encode('latin-1', 'replace').decode('latin-1')
                
            pdf.set_font("Helvetica", size=10)
            for idx, (h, files) in enumerate(list(eg.items())[:50]): # limit to 50 for pdf size
                original = get_original(files, auto_select_strategy, safe_zones_list)
                dupes = [f for f in files if f["path"] != original["path"]]
                pdf.set_font("Helvetica", 'B', 10)
                pdf.cell(200, 8, text=safe_text(f"Group {idx+1}: {original['name']}"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", '', 9)
                pdf.cell(200, 6, text=safe_text(f"KEEP: {original['path']}"), new_x="LMARGIN", new_y="NEXT")
                for d in dupes:
                    pdf.cell(200, 6, text=safe_text(f"DUPE: {d['path']}"), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(4)
            
            return bytes(pdf.output())
            
        try:
            pdf_bytes = generate_pdf()
            st.download_button(
                label="📄 Export Report to PDF",
                data=pdf_bytes,
                file_name="scan_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.button("📄 Generate PDF Report (Error)", disabled=True, use_container_width=True)
            st.error(f"Failed to generate PDF: {e}")
    else:
        st.button("📄 Export Report to PDF", disabled=True, use_container_width=True)

st.divider()

# ── Charts ────────────────────────────────────
if eg or ig or ng or tg:
    c1, c2 = st.columns(2)

    with c1:
        # Pie chart — file type distribution
        ext_counts = defaultdict(int)
        for f in results["all_files"]:
            ext_counts[f["ext"] or "no ext"] += 1
        df_ext = pd.DataFrame(ext_counts.items(), columns=["Extension", "Count"]).sort_values("Count", ascending=False).head(10)
        fig_pie = px.pie(
            df_ext, names="Extension", values="Count",
            title="File Types Scanned",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            hole=0.4,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        # Bar — waste per exact-dup group
        if eg:
            group_data = []
            for h, files in list(eg.items())[:15]:
                waste_g = sum(f["size"] for f in files[1:])
                group_data.append({
                    "Group": Path(files[0]["name"]).stem[:18] + "…",
                    "Wasted (KB)": round(waste_g / 1024, 1),
                    "Copies": len(files) - 1,
                })
            df_waste = pd.DataFrame(group_data).sort_values("Wasted (KB)", ascending=False)
            fig_bar = px.bar(
                df_waste, x="Group", y="Wasted (KB)", color="Copies",
                title="Space Wasted per Duplicate Group",
                color_continuous_scale="Purples",
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis_tickangle=-30,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No exact duplicates found — nothing to chart.")

    # Full Width Treemap
    if eg:
        st.markdown("<br>**Interactive Disk Map (Wasted Space by Folder)**", unsafe_allow_html=True)
        tm_data = []
        for h, files in eg.items():
            original = get_original(files, auto_select_strategy, safe_zones_list)
            for f in files:
                if f["path"] != original["path"]:
                    tm_data.append({
                        "Folder": os.path.dirname(f["path"]),
                        "Size": f["size"]
                    })
        if tm_data:
            df_tm = pd.DataFrame(tm_data)
            df_folder_waste = df_tm.groupby("Folder", as_index=False)["Size"].sum()
            df_folder_waste["Root"] = "Wasted Space"
            fig_tm = px.treemap(
                df_folder_waste, 
                path=["Root", "Folder"], 
                values="Size",
                color="Size",
                color_continuous_scale="tealgrn",
                hover_data={"Size": ":.2f"}
            )
            fig_tm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#bbcabf",
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_tm, use_container_width=True)

    st.divider()

# ─────────────────────────────────────────────
#  TABS — Results
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"Exact Duplicates ({len(eg)})",
    f"Image Near-Duplicates ({len(ig)})",
    f"Similar Names ({len(ng)})",
    f"Text Similarity ({len(tg)})",
    f"All Files ({results['total_files']})",
    "🗄️ Quarantine",
])

# ── Tab 1: Exact Duplicates ───────────────────
with tab1:
    if not eg:
        st.success("No exact duplicate files found!")
    else:
        st.markdown(f"Found **{len(eg)} groups** of exact duplicates. "
                    f"Cleaning them up would recover **{format_size(waste)}**.")

        files_to_remove = []

        for idx, (h, files) in enumerate(eg.items()):
            original = get_original(files, auto_select_strategy, safe_zones_list)
            dupes    = [f for f in files if f["path"] != original["path"]]

            with st.expander(
                f"Group {idx+1} — {original['name']}  •  "
                f"{len(dupes)} duplicate(s)  •  "
                f"{format_size(sum(f['size'] for f in dupes))} wasted"
            ):
                st.markdown(f"""
                <div class="dup-card">
                    <span class="badge badge-exact">EXACT</span>&nbsp;
                    <span class="original">✅ KEEP → {original['path']}</span><br>
                    <small>{format_size(original['size'])} • modified {original['modified'].strftime('%Y-%m-%d %H:%M')}</small>
                </div>""", unsafe_allow_html=True)

                for d in dupes:
                    st.markdown(f"""
                    <div class="dup-card">
                        <span class="duplicate">🗑️ DUPE → {d['path']}</span><br>
                        <small>{format_size(d['size'])} • modified {d['modified'].strftime('%Y-%m-%d %H:%M')}</small>
                    </div>""", unsafe_allow_html=True)
                    files_to_remove.append(d["path"])

        st.divider()
        if files_to_remove:
            st.markdown(f"**{len(files_to_remove)} duplicate files** selected for removal.")
            if st.button(f"🗑️ Remove All Exact Duplicates ({len(files_to_remove)} files)",
                         key="del_exact"):
                success, fail = 0, 0
                prog = st.progress(0)
                for i, fp in enumerate(files_to_remove):
                    prog.progress((i + 1) / len(files_to_remove))
                    if is_safe(fp, safe_zones_list):
                        st.error(f"Protected (Safe Zone): {fp}")
                        fail += 1
                        continue
                    if action == "Permanently Delete":
                        ok = safe_delete(fp)
                    else:
                        ok = move_to_quarantine(fp, quarantine_path)
                    if ok: success += 1
                    else:  fail += 1
                prog.empty()
                st.success(f"Done! {success} files {'deleted' if action == 'Permanently Delete' else 'quarantined'}. {fail} failed.")


# ── Tab 2: Image Near-Duplicates ──────────────
with tab2:
    if not detect_images:
        st.info("Image detection was disabled. Enable it in the sidebar.")
    elif not ig:
        st.success("No near-duplicate images found!")
    else:
        st.markdown(f"Found **{len(ig)} groups** of visually similar images.")
        side_by_side = st.toggle("Side-by-Side Compare Mode", value=False)
        for idx, group in enumerate(ig):
            with st.expander(f"Image Group {idx+1} — {len(group)} similar images"):
                if side_by_side and len(group) == 2:
                    cols = st.columns(2)
                    for col, f in zip(cols, group):
                        with col:
                            st.markdown(f"**{f['name']}** - {format_size(f['size'])}")
                            try:
                                img = Image.open(f["path"])
                                st.image(img, use_container_width=True)
                            except Exception:
                                pass
                else:
                    cols = st.columns(min(len(group), 4))
                    for col, f in zip(cols, group):
                        with col:
                            try:
                                img = Image.open(f["path"])
                                img.thumbnail((200, 200))
                                st.image(img, caption=f["name"], use_container_width=True)
                                st.caption(format_size(f["size"]))
                            except Exception:
                                st.warning(f"Cannot preview: {f['name']}")

                paths = [f["path"] for f in group]
                original = get_original(group, auto_select_strategy, safe_zones_list)
                default_idx = paths.index(original["path"]) if original["path"] in paths else 0
                
                st.markdown("Which file would you like to **keep**?")
                keep_choice = st.selectbox(
                    "Keep:", paths,
                    index=default_idx,
                    key=f"img_keep_{idx}"
                )
                if st.button(f"Apply for Group {idx+1}", key=f"img_act_{idx}"):
                    for f in group:
                        if f["path"] != keep_choice:
                            if is_safe(f["path"], safe_zones_list):
                                st.error(f"Protected (Safe Zone): {f['path']}")
                            else:
                                if action == "Permanently Delete":
                                    safe_delete(f["path"])
                                else:
                                    move_to_quarantine(f["path"], quarantine_path)
                    st.success(f"Done! Kept: {os.path.basename(keep_choice)}")


# ── Tab 3: Similar Names ──────────────────────
with tab3:
    if not detect_names:
        st.info("Name similarity detection was disabled. Enable it in the sidebar.")
    elif not ng:
        st.success("No similar-named files found!")
    else:
        st.markdown(f"Found **{len(ng)} groups** of files with the same name but different extensions.")
        rows = []
        for group in ng:
            for f in group:
                rows.append({
                    "File Name": f["name"],
                    "Path": f["path"],
                    "Size": format_size(f["size"]),
                    "Extension": f["ext"],
                    "Modified": f["modified"].strftime("%Y-%m-%d %H:%M"),
                })
        df_names = pd.DataFrame(rows)
        df_names.insert(0, "Select", False)
        edited_df = st.data_editor(
            df_names,
            column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
            disabled=["File Name", "Path", "Size", "Extension", "Modified"],
            hide_index=True,
            use_container_width=True,
            key="editor_tab3"
        )
        selected_paths = edited_df[edited_df["Select"]]["Path"].tolist()
        if selected_paths:
            if st.button(f"🗑️ Remove Selected Files ({len(selected_paths)})", key="del_tab3"):
                success, fail = 0, 0
                for fp in selected_paths:
                    if is_safe(fp, safe_zones_list):
                        st.error(f"Protected (Safe Zone): {fp}")
                        fail += 1
                        continue
                    if action == "Permanently Delete":
                        ok = safe_delete(fp)
                    else:
                        ok = move_to_quarantine(fp, quarantine_path)
                    if ok: success += 1
                    else: fail += 1
                st.success(f"{success} processed. {fail} failed. Please rescan to update results.")


# ── Tab 4: Text Similarity ────────────────────
with tab4:
    if not detect_text:
        st.info("Text similarity detection was disabled. Enable it in the sidebar.")
    elif not tg:
        st.success("No similar text files found!")
    else:
        st.markdown(f"Found **{len(tg)} groups** of highly similar text files.")
        for idx, group in enumerate(tg):
            with st.expander(f"Text Group {idx+1} — {len(group)} similar files"):
                paths = [f["path"] for f in group]
                original = get_original(group, auto_select_strategy, safe_zones_list)
                default_idx = paths.index(original["path"]) if original["path"] in paths else 0
                
                for f in group:
                    if f["path"] == original["path"]:
                        st.markdown(f"**Original:** `{f['path']}` ({format_size(f['size'])})")
                    else:
                        st.markdown(f"**Duplicate:** `{f['path']}` ({format_size(f['size'])})")
                
                st.markdown("Which file would you like to **keep**?")
                keep_choice = st.selectbox(
                    "Keep:", paths,
                    index=default_idx,
                    key=f"txt_keep_{idx}"
                )
                if st.button(f"Apply for Group {idx+1}", key=f"txt_act_{idx}"):
                    for f in group:
                        if f["path"] != keep_choice:
                            if is_safe(f["path"], safe_zones_list):
                                st.error(f"Protected (Safe Zone): {f['path']}")
                            else:
                                if action == "Permanently Delete":
                                    safe_delete(f["path"])
                                else:
                                    move_to_quarantine(f["path"], quarantine_path)
                    st.success(f"Done! Kept: {os.path.basename(keep_choice)}")

# ── Tab 5: All Files Scanned ──────────────────
with tab5:
    st.markdown(f"Found **{results['total_files']} files** in total.")
    rows = []
    for f in results["all_files"]:
        status = "Unique"
        if f.get("hash") in eg and len(eg[f["hash"]]) > 1:
            status = "Exact Duplicate"
        rows.append({
            "File Name": f["name"],
            "Path": f["path"],
            "Size": format_size(f["size"]),
            "Extension": f["ext"],
            "Modified": f["modified"].strftime("%Y-%m-%d %H:%M"),
            "Status": status
        })
    df_all = pd.DataFrame(rows)
    if not df_all.empty:
        cols = ["Status", "File Name", "Path", "Size", "Extension", "Modified"]
        df_all = df_all[cols]
        df_all.insert(0, "Select", False)
        edited_df = st.data_editor(
            df_all,
            column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
            disabled=cols,
            hide_index=True,
            use_container_width=True,
            key="editor_tab4"
        )
        selected_paths = edited_df[edited_df["Select"]]["Path"].tolist()
        if selected_paths:
            if st.button(f"🗑️ Remove Selected Files ({len(selected_paths)})", key="del_tab4"):
                success, fail = 0, 0
                for fp in selected_paths:
                    if is_safe(fp, safe_zones_list):
                        st.error(f"Protected (Safe Zone): {fp}")
                        fail += 1
                        continue
                    if action == "Permanently Delete":
                        ok = safe_delete(fp)
                    else:
                        ok = move_to_quarantine(fp, quarantine_path)
                    if ok: success += 1
                    else: fail += 1
                st.success(f" {success} processed. {fail} failed. Please rescan to update results.")


# ── Tab 6: Quarantine Manager ─────────────────
with tab6:
    st.markdown(f"**Quarantine Folder:** `{quarantine_path}`")
    if not os.path.exists(quarantine_path) or len(os.listdir(quarantine_path)) == 0:
        st.success("✅ Quarantine is currently empty.")
    else:
        q_files = []
        for root, _, files in os.walk(quarantine_path):
            for fname in files:
                full = os.path.join(root, fname)
                q_files.append({
                    "File Name": fname,
                    "Path": full,
                    "Size": format_size(os.path.getsize(full)),
                    "Quarantined On": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")
                })
        
        df_q = pd.DataFrame(q_files)
        df_q.insert(0, "Select", False)
        
        edited_q = st.data_editor(
            df_q,
            column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
            disabled=["File Name", "Path", "Size", "Quarantined On"],
            hide_index=True,
            use_container_width=True,
            key="editor_tab5"
        )
        
        selected_q = edited_q[edited_q["Select"]]["Path"].tolist()
        
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            if st.button("🗑️ Empty Entire Quarantine", use_container_width=True, key="empty_q"):
                count = 0
                for f in q_files:
                    if safe_delete(f["Path"]): count += 1
                st.success(f"Emptied {count} files from Quarantine.")
        with col_q2:
            if selected_q:
                if st.button(f"↩️ Restore Selected ({len(selected_q)})", use_container_width=True, key="restore_q"):
                    restored_dir = os.path.join(folder_input, "Restored_From_Quarantine")
                    os.makedirs(restored_dir, exist_ok=True)
                    r_count = 0
                    for sq in selected_q:
                        try:
                            shutil.move(sq, os.path.join(restored_dir, os.path.basename(sq)))
                            r_count += 1
                        except Exception:
                            pass
                    st.success(f"Restored {r_count} files to `{restored_dir}`.")

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='font-family:Space Mono,monospace;font-size:0.7rem;
            color:#1e3a5f;text-align:center;padding:8px'>
    DupeFinder AI • Built with Streamlit + Pillow + imagehash + Plotly
    • All processing is 100% local
</div>
""", unsafe_allow_html=True)