# 🩺 ClinicalPrompt-Evaluator

**An AI Workbench for Clinical Data Extraction & Prompt Evaluation**

This project is a high-end portfolio piece specifically designed for the **AI Engineering MasterClass**, AI Prompt Engineering at Endpoint Clinical. It demonstrates the ability to integrate state-of-the-art LLMs into complex clinical operations, knowledge management, and automation workflows.

## 🎯 The Concept
ClinicalPrompt-Evaluator is a web-based internal tool designed for "Clinical Data Operations" teams. It allows users to systematically test, evaluate, and automate the extraction of structured data   from unstructured clinical documents and expert interview transcripts.

## 🔑 Key Features

### 📄 1. Batch Clinical Data Extraction
*   **Multi-Format Support**: Upload multiple `.pdf` or `.txt` clinical documents (e.g., pathology reports, trial protocols).
*   **Batch Processing**: Automatically iterates through all uploaded documents, extracting structured fields (e.g., Trial Eligibility, Diagnosis, Dosage).
*   **Summary Dashboard**: Provides a unified table view of extraction results across the entire document batch.

### 📊 2. Prompt Evaluation Engine
*   **Accuracy Scoring**: Compare AI-generated JSON outputs against a "Ground Truth" dataset to calculate an exact Accuracy Score (0-100%).
*   **Visual Debugging**: A dedicated dashboard highlights **Mismatches**, **Missing Fields**, and **Extra Fields (Hallucinations)** to help refine prompts.

### 🎙️ 3. Multimodal Audio Insights
*   **Interview Transcription**: Uses **Gemini 2.5 Flash** multimodal capabilities to transcribe clinical expert interviews or trial coordinator meetings.
*   **Custom Prompting**: Users can define specific goals for audio analysis (e.g., "Identify patient safety concerns" or "Find workflow bottlenecks").
*   **Actionable Summaries**: Automatically generates concise summaries and bulleted lists of next steps.

### 📋 4. Operations Reporting
*   **Markdown Export**: Consolidates extraction metrics, data results, and audio insights into a professional, Notion-ready project report.
*   **Persistent State**: The application maintains analysis results across different feature tabs for a seamless reporting workflow.

## 🛠️ Tech Stack
*   **Frontend**: Streamlit
*   **Logic Core**: Python 3.12+
*   **AI Models**: 
    *   **Primary**: Google Gemini 2.5 Flash (Multimodal)
    *   **Fallback**: GitHub AI Models (GPT-4o)
*   **Utilities**: Pydantic (JSON validation), PyPDF2 (PDF extraction), python-dotenv.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- A Google Gemini API Key (saved in `.env`)
- (Optional) A GitHub Token for GPT-4o fallback.

### 2. Installation
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the App
```powershell
streamlit run app.py
```

---
*Created for the Endpoint Clinical Innovation Team.*
