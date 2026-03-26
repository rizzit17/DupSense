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

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DupeFinder AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  (dark cyber aesthetic)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Dark background */
.stApp {
    background: #0a0e1a;
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f1528;
    border-right: 1px solid #1e2d4a;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111827, #1a2234);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #7c3aed);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.05em;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4);
}

/* Danger button */
.danger-btn > button {
    background: linear-gradient(135deg, #dc2626, #9f1239) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #1d4ed8, #7c3aed);
}

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #94a3b8 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom-color: #818cf8 !important;
}

/* Expander */
details {
    background: #111827;
    border: 1px solid #1e2d4a;
    border-radius: 8px;
}

/* DataFrames */
.stDataFrame {
    border: 1px solid #1e3a5f;
    border-radius: 8px;
}

/* Title glow */
.title-glow {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-family: 'Space Mono', monospace;
    color: #4b6282;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    margin-bottom: 2rem;
}

/* Duplicate group card */
.dup-card {
    background: #111827;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #7c3aed;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    color: #94a3b8;
}

.dup-card .original {
    color: #34d399;
    font-weight: 700;
}

.dup-card .duplicate {
    color: #f87171;
}

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
}

.badge-exact { background: #1e3a5f; color: #60a5fa; }
.badge-image { background: #1e1b4b; color: #a78bfa; }
.badge-name  { background: #14291f; color: #34d399; }

.stat-row {
    display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.5rem;
}
.stat-box {
    flex: 1; min-width: 130px;
    background: #111827;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 14px;
    text-align: center;
}
.stat-box .val {
    font-size: 1.6rem;
    font-weight: 800;
    font-family: 'Space Mono', monospace;
    color: #818cf8;
}
.stat-box .lbl {
    font-size: 0.7rem;
    color: #4b6282;
    letter-spacing: 0.08em;
    text-transform: uppercase;
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


def scan_directory(folder: str, scan_subfolders: bool = True,
                   check_images: bool = True, check_names: bool = True,
                   image_threshold: int = 10):
    """
    Scan a directory for:
    1. Exact duplicates   → same MD5 hash
    2. Near-duplicate images → perceptual hash distance ≤ threshold
    3. Similar file names → same stem, different extension
    Returns a dict with results and statistics.
    """
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
                all_files.append({
                    "path": full,
                    "name": fname,
                    "stem": Path(fname).stem.lower(),
                    "ext": Path(fname).suffix.lower(),
                    "size": size,
                    "modified": datetime.fromtimestamp(os.path.getmtime(full)),
                    "is_image": Path(fname).suffix.lower() in IMAGE_EXTS,
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
                              text=f"🖼️ Comparing images… ({i+1}/{len(images)})")
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
    detect_exact  = st.checkbox("✅ Exact Duplicates (MD5 Hash)", value=True)
    detect_images = st.checkbox("🖼️ Near-Duplicate Images (AI)", value=True)
    detect_names  = st.checkbox("📝 Similar File Names",          value=True)

    if detect_images:
        img_threshold = st.slider(
            "Image Similarity Threshold",
            min_value=1, max_value=20, value=10,
            help="Lower = stricter match. 10 is a good default."
        )
    else:
        img_threshold = 10

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

    scan_btn = st.button("🚀 Start Scan", use_container_width=True)

    st.divider()
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:0.7rem;color:#334155;line-height:1.8'>
    🔒 All processing is <b>local</b>.<br>
    No files leave your machine.<br><br>
    💡 <b>Tip:</b> Always quarantine<br>before deleting permanently.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────
st.markdown('<div class="title-glow">DupeFinder AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">// SMART DUPLICATE FILE DETECTION & CLEANUP</div>', unsafe_allow_html=True)

# ── Welcome state ────────────────────────────
if not scan_btn:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size:2rem">🔍</div>
            <div class="val">MD5</div>
            <div class="lbl">Exact Duplicate Detection</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size:2rem">🧠</div>
            <div class="val">pHash</div>
            <div class="lbl">AI Image Similarity</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size:2rem">📝</div>
            <div class="val">Stem</div>
            <div class="lbl">Similar Name Grouping</div>
        </div>""", unsafe_allow_html=True)

    st.info("👈 Enter a folder path in the sidebar and click **Start Scan** to begin.")
    st.stop()

# ── Validate folder ──────────────────────────
if not folder_input or not os.path.isdir(folder_input):
    st.error("❌ Please enter a valid folder path in the sidebar.")
    st.stop()

# ── Run scan ─────────────────────────────────
with st.spinner("Scanning… this may take a moment for large folders."):
    results = scan_directory(
        folder=folder_input,
        scan_subfolders=scan_subfolders,
        check_images=detect_images,
        check_names=detect_names,
        image_threshold=img_threshold,
    )

if results is None:
    st.warning("No files found in the selected folder.")
    st.stop()

# ── Summary metrics ──────────────────────────
st.markdown("### 📊 Scan Summary")

eg = results["exact_groups"]
ig = results["image_groups"]
ng = results["name_groups"]
waste = results["exact_waste_bytes"]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total Files",        results["total_files"])
m2.metric("Exact Dup Groups",   len(eg))
m3.metric("Image Dup Groups",   len(ig))
m4.metric("Name-Similar Groups",len(ng))
m5.metric("Recoverable Space",  format_size(waste))

st.divider()

# ── Charts ────────────────────────────────────
if eg or ig or ng:
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

    st.divider()

# ─────────────────────────────────────────────
#  TABS — Results
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    f"📁 Exact Duplicates ({len(eg)})",
    f"🖼️ Image Near-Duplicates ({len(ig)})",
    f"📝 Similar Names ({len(ng)})",
])

# ── Tab 1: Exact Duplicates ───────────────────
with tab1:
    if not eg:
        st.success("✅ No exact duplicate files found!")
    else:
        st.markdown(f"Found **{len(eg)} groups** of exact duplicates. "
                    f"Cleaning them up would recover **{format_size(waste)}**.")

        files_to_remove = []

        for idx, (h, files) in enumerate(eg.items()):
            original = min(files, key=lambda f: f["modified"])  # oldest = original
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
                    if action == "Permanently Delete":
                        ok = safe_delete(fp)
                    else:
                        ok = move_to_quarantine(fp, quarantine_path)
                    if ok: success += 1
                    else:  fail += 1
                prog.empty()
                st.success(f"✅ Done! {success} files {'deleted' if action == 'Permanently Delete' else 'quarantined'}. {fail} failed.")


# ── Tab 2: Image Near-Duplicates ──────────────
with tab2:
    if not detect_images:
        st.info("Image detection was disabled. Enable it in the sidebar.")
    elif not ig:
        st.success("✅ No near-duplicate images found!")
    else:
        st.markdown(f"Found **{len(ig)} groups** of visually similar images.")
        for idx, group in enumerate(ig):
            with st.expander(f"Image Group {idx+1} — {len(group)} similar images"):
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

                st.markdown("Which file would you like to **keep**?")
                keep_choice = st.selectbox(
                    "Keep:", [f["path"] for f in group],
                    key=f"img_keep_{idx}"
                )
                if st.button(f"Apply for Group {idx+1}", key=f"img_act_{idx}"):
                    for f in group:
                        if f["path"] != keep_choice:
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
        st.success("✅ No similar-named files found!")
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
        st.dataframe(df_names, use_container_width=True, hide_index=True)


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