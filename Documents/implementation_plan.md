# ClinicalPrompt-Evaluator Implementation Plan

This plan outlines the development of the ClinicalPrompt-Evaluator, an AI workbench for evaluating LLM prompts on clinical documents. This project will serve as a portfolio piece for the Endpoint Clinical AI & Prompt Engineering Internship.

## User Review Required
> [!IMPORTANT]
> Please review the proposed tech stack (Streamlit + Google Gemini) and the phased approach below. 
> Let me know if you approve this plan, or if you would prefer to use a different framework (like Gradio) or a different LLM provider (like OpenAI or Anthropic).

## Proposed Changes

### Phase 1: Core Foundation & Basic Extraction
- Initialize a Python virtual environment and set up `requirements.txt` (`streamlit`, `google-generativeai`, `pydantic`).
- Build the main Streamlit interface (`app.py`).
- Implement the document upload functionality (for `.txt` files initially, to leverage your existing TCGA pipeline output).
- Integrate the Google Gemini API to extract structured JSON data from the text based on a user-defined Pydantic schema.

### Phase 2: Evaluation Engine (The "Prompt Testing" Module)
- Add functionality for the user to input a "Ground Truth" JSON.
- Build the comparison engine to score the LLM's extracted JSON against the ground truth (calculating Exact Match percentage, identifying hallucinations, and flagging missing fields).
- Create a visual dashboard in Streamlit to display these accuracy metrics.

### Phase 3: Audio Transcription & Workflow Export
- Integrate the Whisper model for processing mock clinical interview audio files into text.
- Add an "Export Report" button that saves the prompt, extraction results, and evaluation metrics into a Notion-ready Markdown document (`.md` file).

## Verification Plan

### Automated Tests
- For the initial prototype, we will rely on manual visual testing in the browser rather than writing unit tests.

### Manual Verification
1. Run the Streamlit application locally using `streamlit run app.py`.
2. Upload a sample unstructured clinical text (like a pathology report).
3. Define target fields (e.g., Diagnosis, Stage) and an extraction prompt.
4. Verify that the application successfully calls the Gemini API and renders the structured JSON output on the screen.
5. Verify the evaluation engine correctly scores the output against a mock ground truth dataset.
