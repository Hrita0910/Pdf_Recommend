## Approach Explanation – Persona-Driven Document Intelligence

### Objective
We aim to design a lightweight, CPU-efficient system that identifies and ranks the most relevant sections across multiple PDF documents based on a user-defined persona and their job-to-be-done.

---

### Core Workflow

1. **User Input**: The system takes as input:
   - A persona (e.g., “Investment Analyst”)
   - A job to be done (e.g., “Analyze revenue trends”)
   - A folder of 3–10 PDFs

2. **Section Extraction**:
   Using PyMuPDF (`fitz`), we parse up to the first 30 pages of each PDF. Section headers are identified based on:
   - Font size and boldness
   - Regex patterns (e.g., capitalized lines)
   - Ignored generic terms (e.g., “Notes”, “Instructions”)

3. **Semantic Chunking**:
   For each section, the content is split into 4-sentence overlapping chunks using NLTK’s tokenizer. These chunks are normalized and deduplicated to ensure quality and variety.

4. **Semantic Ranking**:
   We use `sentence-transformers/all-MiniLM-L12-v2` to encode:
   - The user query (`Persona + Job`)
   - All section chunks

   Cosine similarity is computed between the query and each chunk. We retain only the highest-ranked chunk from each section, and finally select the top 5 most relevant chunks overall.

5. **Output Generation**:
   The system outputs:
   - Section metadata (document, title, page, rank)
   - Refined content (cleaned from bullet points)
   - JSON metadata

---

### Design Constraints

- **No internet dependency**: All models and packages run offline.
- **Model under 1GB**: MiniLM (67M parameters) meets this requirement.
- **CPU only**: Efficient computation using sentence-transformers and `cos_sim`.
- **Fast**: <60 seconds processing time for 3–5 docs on standard CPU.

---

### Strengths & Generalization

This system is domain-agnostic — it works with research papers, textbooks, financial reports, etc. The only assumption is that documents have meaningful section headers and coherent text structure.

Through the combination of smart text segmentation and semantic retrieval, our system is able to “connect what matters” — surfacing the most actionable and relevant parts for each user need.
