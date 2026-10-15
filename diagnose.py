import os
from docx import Document
from sentence_transformers import SentenceTransformer, util

TRANSCRIPT_DIR = r"C:\Users\Samsa\.vscode\coding\unicetra-neuro-adaptive\transcriptions"

THEMES = {
    "Baseline_Friction_Skepticism": "Frustration with AI hallucinations, lack of citations, manual text verification, doubt, and hesitation.",
    "Occo_Transparency_Shift": "Trust improvement, clarity on source provenance, confidence boost when interacting with the visual trust layer.",
    "Edge_Cases_Outliers": "Extreme skepticism, demand for external verification, unexpected user behavior or critiques."
}

def diagnose():
    print("Loading model for diagnostics...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    theme_desc = list(THEMES.values())
    theme_embeddings = model.encode(theme_desc, convert_to_tensor=True)
    theme_names = list(THEMES.keys())
    
    file_count = 0
    all_scores = {t: [] for t in theme_names}
    
    for filename in os.listdir(TRANSCRIPT_DIR):
        if filename.endswith(".docx"):
            file_count += 1
            filepath = os.path.join(TRANSCRIPT_DIR, filename)
            doc = Document(filepath)
            text = " ".join([para.text for para in doc.paragraphs if para.text.strip()])
            
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
            if not sentences:
                print(f"[-] Warning: {filename} yielded 0 sentences!")
                continue
                
            chunk_embeddings = model.encode(sentences, convert_to_tensor=True)
            cos_sim = util.cos_sim(chunk_embeddings, theme_embeddings)
            
            for idx, theme in enumerate(theme_names):
                scores = cos_sim[:, idx]
                max_score = scores.max().item()
                all_scores[theme].append(max_score)
                
    print(f"\n[DIAGNOSTIC SUMMARY]")
    print(f"Total .docx files processed: {file_count}")
    for theme in theme_names:
        scores = all_scores[theme]
        if scores:
            avg = sum(scores) / len(scores)
            highest = max(scores)
            print(f"  * {theme}: Mean Max Score = {avg:.2f}, Absolute Max Score = {highest:.2f}")
        else:
            print(f"  * {theme}: NO SCORES RECORDED")

if __name__ == "__main__":
    diagnose()