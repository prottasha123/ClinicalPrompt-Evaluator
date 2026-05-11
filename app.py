import streamlit as st
import json
import PyPDF2
import tempfile
import os
from datetime import datetime
from logic import (
    extract_with_gemini, 
    extract_with_github_model, 
    process_audio_interview, 
    generate_markdown_report,
    evaluate_json
)

st.set_page_config(page_title="ClinicalPrompt-Evaluator", page_icon="🩺", layout="wide")

# Initialize session state for reporting
if 'extracted_json' not in st.session_state:
    st.session_state.extracted_json = {}
if 'eval_stats' not in st.session_state:
    st.session_state.eval_stats = {}
if 'audio_results' not in st.session_state:
    st.session_state.audio_results = {}
if 'current_model' not in st.session_state:
    st.session_state.current_model = "Gemini 2.0 Flash"

st.title("🩺 ClinicalPrompt-Evaluator")
st.markdown("An AI Workbench for Clinical Data Extraction & Prompt Evaluation")

# Sidebar for Configuration
st.sidebar.header("Configuration")
model_choice = st.sidebar.selectbox("Select Model", ["Gemini 2.0 Flash", "GitHub AI (gpt-4o)"])
st.session_state.current_model = model_choice

tab1, tab2, tab3 = st.tabs(["📄 Document Extraction", "🎙️ Audio Insights", "📊 Final Report"])

with tab1:
    st.header("1. Document Upload")
    uploaded_files = st.file_uploader("Upload clinical documents (Batch support)", type=["txt", "pdf"], accept_multiple_files=True)

    batch_documents = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            doc_text = ""
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    doc_text += page.extract_text() + "\n"
            else:
                doc_text = uploaded_file.getvalue().decode("utf-8")
            batch_documents.append({"name": uploaded_file.name, "text": doc_text})
            
        with st.expander(f"View Uploaded Documents ({len(batch_documents)})"):
            for doc in batch_documents:
                st.text(f"--- {doc['name']} ---")
                st.text(doc['text'][:500] + "...")

    st.header("2. Define Extraction Task")
    col1, col2 = st.columns(2)

    with col1:
        schema_input = st.text_input("Fields to Extract (comma-separated)", "Patient Name, PESEL, Gender, Age, Material, Clinical Diagnosis, Tumor Size, Histological Type, Grade (NHG), pT Stage, pN Stage, Lymph Nodes (positive/total), ER Status, PR Status, HER2 Status, IHC Date, Histopathological Diagnosis, Examination Date")
        schema_fields = [f.strip() for f in schema_input.split(",")]

    with col2:
        prompt_input = st.text_area("Custom Prompt", "Extract the requested fields from the clinical document. If a field is not found, output 'null'. Ensure the output matches the requested fields exactly.")

    st.header("3. Ground Truth (Optional)")
    st.info("Note: Ground truth evaluation currently applies to the first document in the batch if multiple are uploaded.")
    gt_input = st.text_area("Paste Ground Truth JSON here to evaluate accuracy", placeholder='{"Patient Age": "45", "Diagnosis": "Breast Cancer"}')

    st.header("4. Run Batch Extraction & Evaluation")
    if st.button("Run Batch Workbench", type="primary"):
        if not batch_documents:
            st.error("Please upload at least one document first.")
        else:
            all_results = []
            progress_bar = st.progress(0)
            
            for i, doc in enumerate(batch_documents):
                with st.spinner(f"Processing {doc['name']}..."):
                    if "Gemini" in model_choice:
                        result = extract_with_gemini(doc['text'], prompt_input, schema_fields, model_name=model_choice)
                    else:
                        # Extract "gpt-4o" from "GitHub AI (gpt-4o)"
                        github_model = "gpt-4o"
                        if "(" in model_choice:
                            github_model = model_choice.split("(")[1].replace(")", "")
                        result = extract_with_github_model(doc['text'], prompt_input, schema_fields, model_name=github_model)
                    
                    try:
                        # Strip potential markdown backticks
                        clean_result = result.strip()
                        if clean_result.startswith("```json"):
                            clean_result = clean_result[7:-3].strip()
                        elif clean_result.startswith("```"):
                            clean_result = clean_result[3:-3].strip()
                            
                        extracted_json = json.loads(clean_result, strict=False)
                        all_results.append({"Filename": doc['name'], **extracted_json})
                    except json.JSONDecodeError:
                        all_results.append({"Filename": doc['name'], "error": "Invalid JSON output"})
                
                progress_bar.progress((i + 1) / len(batch_documents))
            
            # Save first result to session state for existing report/eval logic
            if all_results:
                st.session_state.extracted_json = all_results[0]
            
            st.success(f"Batch Processing Complete! Processed {len(all_results)} files.")
            
            # --- BATCH RESULTS TABLE ---
            st.subheader("Batch Summary Table")
            st.table(all_results)
            
            # --- EVALUATION DASHBOARD (On First Document) ---
            if gt_input and all_results:
                try:
                    gt_json = json.loads(gt_input, strict=False)
                    # We evaluate the first one for the dashboard demo
                    first_extracted = {k: v for k, v in all_results[0].items() if k != "Filename"}
                    st.session_state.eval_stats = evaluate_json(first_extracted, gt_json)
                    
                    st.divider()
                    st.header("📊 Evaluation Dashboard (First Document)")
                            
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Accuracy Score", f"{st.session_state.eval_stats['accuracy_score']:.1f}%")
                    m2.metric("Matches", len(st.session_state.eval_stats["matches"]))
                    m3.metric("Mismatches/Missing", len(st.session_state.eval_stats["mismatches"]) + len(st.session_state.eval_stats["missing"]))
                    
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        if st.session_state.eval_stats["mismatches"]:
                            st.subheader("❌ Mismatches")
                            for m in st.session_state.eval_stats["mismatches"]:
                                st.error(f"**{m['field']}**")
                                st.write(f"Expected: `{m['ground_truth']}` | Got: `{m['extracted']}`")
                        
                        if st.session_state.eval_stats["missing"]:
                            st.subheader("⚠️ Missing Fields")
                            for field in st.session_state.eval_stats["missing"]:
                                st.warning(f"Field `{field}` not found in extraction.")
                    
                    with c2:
                        if st.session_state.eval_stats["matches"]:
                            st.subheader("✅ Matches")
                            for field in st.session_state.eval_stats["matches"]:
                                st.success(f"Field `{field}` matches perfectly.")
                                
                        if st.session_state.eval_stats["extra"]:
                            st.subheader("💡 Extra Fields (Potential Hallucinations)")
                            for field in st.session_state.eval_stats["extra"]:
                                st.info(f"AI added extra field: `{field}`")
                                        
                except json.JSONDecodeError:
                    st.error("Ground Truth is not valid JSON. Skipping evaluation.")

with tab2:
    st.header("🎙️ Expert Interview Analysis")
    st.markdown("Upload audio of a clinical interview or expert discussion to generate transcription and actionable insights.")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        audio_file = st.file_uploader("Upload Audio Interview", type=["mp3", "wav", "m4a"])
    with col_a2:
        audio_prompt = st.text_area("Custom Audio Prompt", "Transcribe the interview and focus on identifying patient safety concerns and workflow bottlenecks.")
    
    if audio_file is not None:
        st.audio(audio_file)
        if st.button("Process Audio"):
            with st.spinner("Gemini is analyzing the audio..."):
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as tmp:
                    tmp.write(audio_file.getvalue())
                    tmp_path = tmp.name
                
                # Close the file before processing
                st.session_state.audio_results = process_audio_interview(tmp_path, custom_prompt=audio_prompt)
                
                # Cleanup temp file
                os.remove(tmp_path)
                
                if "error" in st.session_state.audio_results:
                    st.error(f"Audio Processing Error: {st.session_state.audio_results['error']}")
                else:
                    st.success("Audio analysis complete!")
                    
                    st.subheader("Transcription Snippet")
                    st.text(st.session_state.audio_results.get('transcription', '')[:1000] + "...")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("💡 Key Summary")
                        st.write(st.session_state.audio_results.get('summary', ''))
                    with c2:
                        st.subheader("🚀 Actionable Insights")
                        for item in st.session_state.audio_results.get('insights', []):
                            st.write(f"- {item}")

with tab3:
    st.header("📊 Final Operations Report")
    st.markdown("Generate and download a comprehensive report of your extraction and interview analysis.")
    
    if not st.session_state.extracted_json and not st.session_state.audio_results:
        st.warning("Please run a document extraction or audio analysis first.")
    else:
        # Prepare project data for report
        project_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "model": st.session_state.current_model,
            "accuracy": st.session_state.eval_stats.get('accuracy_score', 0),
            "match_count": len(st.session_state.eval_stats.get('matches', [])),
            "issue_count": len(st.session_state.eval_stats.get('mismatches', [])) + len(st.session_state.eval_stats.get('missing', [])),
            "extracted_json": st.session_state.extracted_json,
            "audio_results": st.session_state.audio_results
        }
        
        report_md = generate_markdown_report(project_data)
        
        st.markdown(report_md)
        
        st.download_button(
            label="Download Markdown Report",
            data=report_md,
            file_name=f"clinical_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown"
        )
