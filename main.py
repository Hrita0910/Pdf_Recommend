import os
import time
import re
import datetime
import unicodedata
import fitz
import nltk
import json
import nltk
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize

nltk.download('punkt_tab')

nltk.download('punkt', quiet=True)

# ==== Folder Setup ====
INPUT_FOLDER = "Input"
OUTPUT_FOLDER = "Output"
OUTPUT_JSON = os.path.join(OUTPUT_FOLDER, "Output.json")

# ==== Constants ====
N_TOP_SECTIONS = 5
CHUNK_SENT_WINDOW = 4
CHUNKS_PER_SECTION_LIMIT = 10
SECTION_CANDIDATE_LIMIT = 60

start_time = time.time()

# ==== Get User Input ====
print("Enter the required inputs")
persona = input("Enter persona : ").strip()
job = input("Enter the job to be done : ").strip()
query = f"{persona}. Task: {job}"

# ==== Load all PDFs from Input/ ====
doc_paths = [os.path.join(INPUT_FOLDER, f) for f in os.listdir(INPUT_FOLDER)
             if f.lower().endswith(".pdf")]
if not doc_paths:
    raise RuntimeError("No PDF files found in Input/ folder!")

print(f"Found {len(doc_paths)} PDFs to process.")

# ==== Utility Functions ====
def clean_text(text, max_length=600):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_length]

def remove_bullet_prefix(text):
    return re.sub(r'(?m)^(\s*[\u2022o\-\*\d\.\)\•°º(]+\s*)+', '', text).strip()

def smart_sentence_chunks(text, window=CHUNK_SENT_WINDOW):
    sents = [s.strip() for s in sent_tokenize(text) if len(s.strip()) > 20]
    if not sents: return []
    chunks = []
    for i in range(len(sents)):
        chunk = ' '.join(sents[i:i+window])
        if len(chunk) > 40:
            chunks.append(chunk)
        if i+window >= len(sents): break
    seen = set()
    uniq_chunks = []
    for c in chunks:
        if c not in seen and len(uniq_chunks) < CHUNKS_PER_SECTION_LIMIT:
            uniq_chunks.append(c)
            seen.add(c)
    return uniq_chunks

def extract_sections(pdf_path, max_pages=30):
    generic_keywords = {'instructions', 'ingredients', 'notes', 'preparation', 'method'}
    doc = fitz.open(pdf_path)
    sections = []
    current_section = None
    for page_idx, page in enumerate(doc):
        if page_idx >= max_pages: break
        blocks = page.get_text('dict')['blocks']
        for b in blocks:
            if b['type'] != 0: continue
            for line in b['lines']:
                this_line = ''.join([span['text'] for span in line['spans']])
                max_size = max([span['size'] for span in line['spans']]) if line['spans'] else 0
                is_bold = any('Bold' in span['font'] for span in line['spans'])
                norm_line = this_line.strip()
                norm_lower = norm_line.lower().strip().rstrip(':').strip()
                is_generic = norm_lower in generic_keywords
                if (len(norm_line) >= 7 and len(norm_line) < 100
                    and (is_bold or max_size > 12)
                    and re.match(r"^[A-Z0-9][\w\s\-:,()&']+$", norm_line)
                    and not norm_lower.startswith("figure")
                    and not is_generic):
                    if current_section:
                        current_section['end_page'] = page_idx + 1
                        sections.append(current_section)
                    current_section = {
                        'title': norm_line,
                        'page_number': page_idx + 1,
                        'section_text': "",
                    }
                    continue
                if current_section:
                    current_section['section_text'] += norm_line + ' '
    if current_section:
        current_section['end_page'] = current_section.get('page_number', 1)
        sections.append(current_section)
    doc.close()
    return [s for s in sections if len(s["section_text"]) > 70]

# ==== Load model ====
#print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")
query_embedding = model.encode([query], convert_to_tensor=True)
#print("Model loaded.")

# ==== Extract and embed candidate chunks ====
chunk_records = []
for doc_path in doc_paths:
    for sec in extract_sections(doc_path, max_pages=30):
        chunks = smart_sentence_chunks(sec['section_text'], window=CHUNK_SENT_WINDOW)
        for chunk in chunks:
            chunk_records.append({
                "document": os.path.basename(doc_path),
                "section_title": sec["title"],
                "page_number": sec["page_number"],
                "chunk_text": clean_text(chunk, 650),
            })
        if len(chunk_records) > SECTION_CANDIDATE_LIMIT * CHUNKS_PER_SECTION_LIMIT:
            break

print("Total candidate chunks for ranking:", len(chunk_records))
if not chunk_records:
    raise RuntimeError("No chunks extracted from the PDFs.")

batch_chunk_texts = [rec["chunk_text"] for rec in chunk_records]
chunk_embeddings = model.encode(batch_chunk_texts, convert_to_tensor=True)
#print("Embedding done.")

# ==== Compute similarity ====
sims = util.cos_sim(query_embedding, chunk_embeddings)[0].tolist()
for i, sim in enumerate(sims):
    chunk_records[i]["similarity"] = round(sim, 4)

# ==== Select top relevant chunks ====
best_per_section = {}
for rec in chunk_records:
    key = (rec["document"], rec["section_title"], rec["page_number"])
    if key not in best_per_section or rec["similarity"] > best_per_section[key]["similarity"]:
        best_per_section[key] = rec

top_sections = sorted(
    best_per_section.values(), key=lambda x: x["similarity"], reverse=True
)[:N_TOP_SECTIONS]

# ==== Build output ====
extracted_sections = []
subsection_analysis = []
for idx, s in enumerate(top_sections):
    cleaned_text = remove_bullet_prefix(s["chunk_text"])
    extracted_sections.append({
        "document": s["document"],
        "section_title": s["section_title"],
        "importance_rank": idx + 1,
        "page_number": s["page_number"],
        
    })
    subsection_analysis.append({
        "document": s["document"],
        "refined_text": cleaned_text,
        "page_number": s["page_number"],
        
    })

output_json = {
    "metadata": {
        "input_documents": [os.path.basename(p) for p in doc_paths],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.datetime.now().isoformat(),
    },
    "extracted_sections": extracted_sections,
    "subsection_analysis": subsection_analysis
}

# ==== Save Output ====
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output_json, f, ensure_ascii=False, indent=4)

#runtime = time.time() - start_time
print(f"Output written to {OUTPUT_JSON}.")