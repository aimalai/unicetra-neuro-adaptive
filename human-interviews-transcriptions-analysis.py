import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from docx import Document
from sentence_transformers import SentenceTransformer, util

TRANSCRIPT_DIR = r"C:\Users\Samsa\.vscode\coding\unicetra-neuro-adaptive\transcriptions"
OUTPUT_DIR = r"C:\Users\Samsa\.vscode\coding\unicetra-neuro-adaptive"

THEMES = {
    "Baseline_Friction_Skepticism": "Frustration with AI hallucinations, lack of citations, manual text verification, doubt, and hesitation.",
    "Occo_Transparency_Shift": "Trust improvement, clarity on source provenance, confidence boost when interacting with the visual trust layer.",
    "Edge_Cases_Outliers": "Extreme skepticism, demand for external verification, unexpected user behavior or critiques."
}

def load_transcripts(directory):
    transcript_data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".docx"):
            filepath = os.path.join(directory, filename)
            doc = Document(filepath)
            full_text = " ".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            clean_name = filename.lower().replace(".docx", "")
            
            if "baseline" in clean_name or "baselin" in clean_name:
                condition = "baseline"
            elif "occo" in clean_name:
                condition = "occo"
            else:
                continue
                
            pid = clean_name.split("-")[0].upper()
            
            if pid not in transcript_data:
                transcript_data[pid] = {}
            transcript_data[pid][condition] = full_text
            
    return transcript_data

def chunk_text(text, max_sent=3):
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    chunks = []
    for i in range(0, len(sentences), max_sent):
        chunk = ". ".join(sentences[i:i+max_sent]) + "."
        chunks.append(chunk)
    return chunks

def main():
    print("Loading Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Ingesting transcripts from: {TRANSCRIPT_DIR}")
    data = load_transcripts(TRANSCRIPT_DIR)
    print(f"Successfully loaded paired data for {len(data)} participants.")
    
    theme_names = list(THEMES.keys())
    theme_desc = list(THEMES.values())
    theme_embeddings = model.encode(theme_desc, convert_to_tensor=True)
    
    results = {theme: [] for theme in theme_names}
    condition_theme_scores = {"baseline": {t: [] for t in theme_names}, "occo": {t: [] for t in theme_names}}
    
    for pid, conditions in data.items():
        for condition, text in conditions.items():
            chunks = chunk_text(text)
            if not chunks:
                continue
            chunk_embeddings = model.encode(chunks, convert_to_tensor=True)
            cos_sim = util.cos_sim(chunk_embeddings, theme_embeddings)
            
            for idx, theme in enumerate(theme_names):
                scores = cos_sim[:, idx]
                best_idx = scores.argmax().item()
                best_score = scores[best_idx].item()
                
                condition_theme_scores[condition][theme].append(best_score)
                
                # Calibrated threshold based on diagnostic means (~0.30)
                if best_score > 0.30:
                    results[theme].append({
                        "participant": pid,
                        "condition": condition,
                        "score": best_score,
                        "quote": chunks[best_idx]
                    })

    # 1. Generate Markdown Report for Thesis
    md_path = os.path.join(OUTPUT_DIR, "thesis_qualitative_results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Automated Qualitative Analysis: Baseline vs. Occo Framework\n\n")
        for theme, matches in results.items():
            f.write(f"## Theme: {theme}\n\n")
            sorted_matches = sorted(matches, key=lambda x: x['score'], reverse=True)[:3]
            for m in sorted_matches:
                f.write(f"> \"{m['quote']}\"\n")
                f.write(f"> \n> *— Participant {m['participant']} ({m['condition'].capitalize()}), Confidence/Relevance Score: {m['score']:.2f}*\n\n")
    print(f"\n[+] Saved thesis markdown report to: {md_path}")

    # 2. Generate Comparative Visualization Chart
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    plot_data = []
    for cond in ["baseline", "occo"]:
        for theme in theme_names:
            scores = condition_theme_scores[cond][theme]
            avg_score = sum(scores) / len(scores) if scores else 0
            plot_data.append({"Condition": cond.capitalize(), "Theme": theme.replace("_", " "), "Score": avg_score})
            
    df_plot = pd.DataFrame(plot_data)
    
    ax = sns.barplot(data=df_plot, x="Theme", y="Score", hue="Condition", palette="muted")
    plt.title("Semantic Alignment Across Evaluation Themes (Baseline vs. Occo)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Qualitative Theme", fontsize=12)
    plt.ylabel("Mean Cosine Similarity Score", fontsize=12)
    plt.ylim(0, 0.6)  # Scaled to clearly highlight the distributional differences
    plt.legend(title="Condition")
    plt.tight_layout()
    
    chart_path = os.path.join(OUTPUT_DIR, "occo_qualitative_analysis_chart.png")
    plt.savefig(chart_path, dpi=300)
    print(f"[+] Saved comparative chart to: {chart_path}")
    plt.show()

if __name__ == "__main__":
    main()