import os
import json
import tempfile
import time
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- LLM CONFIGURATION ---

# Default configuration for clinical data extraction (High precision)
DEFAULT_CONFIG = {
    "temperature": 0.1,
    "top_p": 0.95,
    "max_output_tokens": 2048,
}

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure GitHub Models (OpenAI SDK)
github_token = os.environ.get("GITHUB_TOKEN")
github_client = None
if github_token:
    github_client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=github_token,
    )

# --- EXTRACTION LOGIC ---

def extract_with_gemini(document_text: str, prompt: str, schema_fields: list, model_name: str = "gemini-2.0-flash") -> str:
    """Extract data using Gemini API."""
    # Handle UI naming vs API naming
    api_model_name = "gemini-2.0-flash" if "2.0" in model_name else "gemini-2.5-flash"
    model = genai.GenerativeModel(api_model_name)
    
    full_prompt = f"""
    You are a clinical data extraction assistant.
    Your task is to extract information from the following clinical document based on the user's prompt.
    You MUST return the output as a valid JSON object.
    Do not include markdown blocks (like ```json), just the raw JSON string.
    
    Fields to extract: {', '.join(schema_fields)}
    
    User Prompt: {prompt}
    
    Document Text:
    {document_text}
    """
    
    try:
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=DEFAULT_CONFIG["temperature"],
                top_p=DEFAULT_CONFIG["top_p"],
                max_output_tokens=DEFAULT_CONFIG["max_output_tokens"]
            )
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return f'{{"error": "Model not found. Please check if gemini-2.5-flash is available. {error_msg}" }}'
        return f'{{"error": "{error_msg}" }}'

def extract_with_github_model(document_text: str, prompt: str, schema_fields: list, model_name: str = "gpt-4o") -> str:
    """Extract data using GitHub Models via OpenAI SDK."""
    if not github_client:
        return '{"error": "GITHUB_TOKEN not found in .env"}'
        
    full_prompt = f"""
    You are a clinical data extraction assistant.
    Your task is to extract information from the following clinical document based on the user's prompt.
    You MUST return the output as a valid JSON object.
    
    Fields to extract: {', '.join(schema_fields)}
    
    User Prompt: {prompt}
    """
    
    try:
        response = github_client.chat.completions.create(
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": document_text}
            ],
            model=model_name,
            response_format={ "type": "json_object" },
            temperature=DEFAULT_CONFIG["temperature"],
            max_tokens=DEFAULT_CONFIG["max_output_tokens"],
            top_p=1.0
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            return f'{{"error": "GitHub Model Unauthorized: Your GITHUB_TOKEN lacks permissions for GitHub Models. Please visit https://github.com/marketplace/models to enable access." }}'
        return f'{{"error": "{error_msg}" }}'

def process_audio_interview(audio_file_path: str, custom_prompt: str = None) -> dict:
    """Use Gemini Multimodal capabilities to transcribe and summarize an audio interview with robust JSON parsing."""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    def clean_json_response(text: str) -> str:
        """Clean the response text to extract valid JSON."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return text

    try:
        audio_file = genai.upload_file(path=audio_file_path)
        
        # Polling: Wait for the file to be ready
        while audio_file.state.name == "PROCESSING":
            time.sleep(1)
            audio_file = genai.get_file(audio_file.name)
            
        if audio_file.state.name == "FAILED":
            return {"error": "Audio file upload failed."}
            
        instruction = custom_prompt if custom_prompt else "Please transcribe this clinical/technical expert interview and provide a summary and actionable insights."
        
        full_prompt = f"""
        {instruction}
        
        CRITICAL: Your output MUST be a perfectly formatted JSON dictionary. 
        - Ensure all keys and values are in double quotes.
        - Ensure every key-value pair (except the last) is followed by a comma.
        - Ensure double quotes within strings are escaped with a backslash (\").
        
        Required Keys:
        1. 'transcription': The full text of the interview.
        2. 'summary': A concise clinical summary.
        3. 'insights': A list of actionable items.
        4. 'automation_opportunities': A list of manual tasks identified.
        
        Format the output as a valid JSON dictionary. Return ONLY the raw JSON string.
        """
        
        response = model.generate_content(
            [full_prompt, audio_file],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1 # Lower temperature for more stable JSON
            )
        )
        
        # Cleanup: Delete the file from Gemini storage after processing
        try:
            audio_file.delete()
        except:
            pass
            
        raw_text = clean_json_response(response.text)
        
        try:
            return json.loads(raw_text, strict=False)
        except json.JSONDecodeError:
            # Fallback: Try a second pass to "repair" the JSON if it's malformed
            repair_prompt = f"Fix the JSON syntax errors (missing commas, unescaped quotes) in the following text and return ONLY the valid JSON:\n\n{raw_text}"
            repair_response = model.generate_content(repair_prompt)
            repaired_text = clean_json_response(repair_response.text)
            return json.loads(repaired_text, strict=False)
            
    except Exception as e:
        return {"error": str(e)}

# --- EVALUATION & REPORTING LOGIC ---

def evaluate_json(extracted: dict, ground_truth: dict) -> dict:
    """Compare extracted JSON against ground truth JSON with semantic awareness."""
    stats = {"accuracy_score": 0.0, "matches": [], "mismatches": [], "missing": [], "extra": []}
    if not ground_truth: return stats
        
    gt_keys = set(ground_truth.keys()); extracted_keys = set(extracted.keys())
    stats["missing"] = list(gt_keys - extracted_keys)
    stats["extra"] = list(extracted_keys - gt_keys)
    
    common_keys = gt_keys & extracted_keys
    
    # Pass 1: Exact matches (case-insensitive, stripped)
    exact_matches = []
    needs_semantic_check = []
    
    for key in common_keys:
        ext_val = str(extracted[key]).strip().lower() if extracted[key] is not None else "null"
        gt_val = str(ground_truth[key]).strip().lower() if ground_truth[key] is not None else "null"
        if ext_val == gt_val:
            exact_matches.append(key)
        else:
            needs_semantic_check.append(key)
            
    # Pass 2: Semantic matches via LLM for potential mismatches
    semantic_matches = []
    final_mismatches = []
    
    if needs_semantic_check:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            # Fallback if no Gemini key: all remaining are mismatches
            for key in needs_semantic_check:
                final_mismatches.append({"field": key, "extracted": extracted[key], "ground_truth": ground_truth[key]})
        else:
            model = genai.GenerativeModel('gemini-2.0-flash')
            # Build a comparison table for the LLM
            comparison_list = []
            for key in needs_semantic_check:
                comparison_list.append({
                    "field": key,
                    "extracted": str(extracted[key]) if extracted[key] is not None else "null",
                    "ground_truth": str(ground_truth[key]) if ground_truth[key] is not None else "null"
                })
            
        prompt = f"""
        You are a clinical data auditor. Compare the 'extracted' values against the 'ground_truth' values for semantic equivalence.
        In the clinical context, paraphrasing is acceptable as long as the core medical meaning is identical.
        
        Example: "45 years old" is equivalent to "45".
        Example: "Stage II Breast Cancer" is NOT equivalent to "Stage III Breast Cancer".
        
        Data to compare:
        {json.dumps(comparison_list, indent=2)}
        
        Return a JSON object where keys are the field names and values are booleans (true if equivalent, false otherwise).
        Return ONLY the raw JSON string.
        """
        
        try:
            response = model.generate_content(
                prompt, 
                generation_config=genai.GenerationConfig(response_mime_type="application/json")
            )
            eval_results = json.loads(response.text, strict=False)
            
            for key in needs_semantic_check:
                # Use .get() and check if explicitly True
                if eval_results.get(key) is True:
                    semantic_matches.append(key)
                else:
                    final_mismatches.append({
                        "field": key, 
                        "extracted": extracted[key], 
                        "ground_truth": ground_truth[key]
                    })
        except Exception:
            # Fallback: if LLM fails, all semantic checks are considered mismatches
            for key in needs_semantic_check:
                final_mismatches.append({
                    "field": key, 
                    "extracted": extracted[key], 
                    "ground_truth": ground_truth[key]
                })
                
    stats["matches"] = exact_matches + semantic_matches
    stats["mismatches"] = final_mismatches
    
    if len(gt_keys) > 0:
        stats["accuracy_score"] = (len(stats["matches"]) / len(gt_keys)) * 100
    return stats

def generate_markdown_report(project_data: dict) -> str:
    """Generate a formatted Markdown report for the clinical project findings."""
    
    def format_list(data_list):
        """Safely convert a list (potentially containing non-string items) to a bulleted Markdown string."""
        if not data_list:
            return "N/A"
        if isinstance(data_list, list):
            # Ensure all items are strings and join them with bullets
            return "\n- " + "\n- ".join([str(item) for item in data_list])
        return str(data_list)

    insights = format_list(project_data.get('audio_results', {}).get('insights', []))
    automation = format_list(project_data.get('audio_results', {}).get('automation_opportunities', []))
    
    return f"""# Clinical AI Operations Report
    
## 🎯 Overview
**Generated on:** {project_data.get('date', 'N/A')}
**Model Used:** {project_data.get('model', 'N/A')}

## 📑 Clinical Extraction Results
### Extraction Metrics
- **Accuracy Score:** {project_data.get('accuracy', 'N/A')}%
- **Matches:** {project_data.get('match_count', 0)}
- **Issues:** {project_data.get('issue_count', 0)}

### Extracted Data
```json
{json.dumps(project_data.get('extracted_json', {}), indent=2)}
```

## 🎙️ Audio Insight Summary
**Transcription Snippet:**
{project_data.get('audio_results', {}).get('transcription', 'N/A')[:500]}...

### 💡 Key Summary
{project_data.get('audio_results', {}).get('summary', 'N/A')}

### 🚀 Actionable Items
{insights}

### 🤖 Automation Opportunities
{automation}

---
*Generated by ClinicalPrompt-Evaluator*
"""
