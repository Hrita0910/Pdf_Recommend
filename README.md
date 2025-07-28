# 📄 PDF Recommender (Task_1B)

This project analyzes PDF documents and extracts the most relevant sections based on a given persona and job-to-be-done input. It uses sentence embeddings and semantic similarity to prioritize relevant content for the target user role.

The entire system runs in a Docker container and requires no GPU.

## 🛠️ Prerequisites

- Docker Desktop installed on your system (Windows/Linux/macOS)
- Your input PDFs placed in an `Input/` folder
- Python script file named `main.py` ready in the root folder

### Folder Structure
```
Task_1B
├── main.py
├── Dockerfile
├── requirements.txt
├── Input/              (place your PDFs here)
├── Output/               
```

## ⚙️ Step-by-Step Guide & Instructions

### 1. 🧾 Clone the project

First clone the project in VS Code. Place all your PDF documents to be analyzed inside a folder named `Input` in the project root. 

**Example:**
```
/Input
├── doc1.pdf
└── doc2.pdf
```

### 2. 🧱 Build the Docker Image

From the root folder (where `Dockerfile` exists), run:

**Terminal / Windows PowerShell:**
```powershell
docker build -t persona-doc-intel .
```

### 3. 🚀 Run the Container

Run the system using the following command:

**Terminal / Windows PowerShell:**
```powershell
docker run -it --rm -v ${PWD}/Input:/app/Input -v ${PWD}/Output:/app/Output persona-doc-intel
```

### 4. ✍️ Provide Input When Prompted

You'll be prompted to enter the Persona and Job To Be Done.

**Example:**
```
Enter persona: Travel Planner 
Enter the job to be done: Plan a trip for 4 days for 4 college students
```

### 5. 📂 View the Output

Once processing is done, an `Output/Output.json` file will be generated, containing:

- Metadata (persona, job, input files)
- Top extracted section titles and page numbers
- Refined content chunks most relevant to the task


## 📋 Additional Notes

- Processing time depends on the size and number of PDF documents
- All dependencies are handled within the Docker container
- No GPU required - runs on CPU only
