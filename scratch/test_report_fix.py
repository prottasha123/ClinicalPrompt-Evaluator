import json

def generate_markdown_report_fix(project_data: dict) -> str:
    def format_list(data_list):
        if not data_list:
            return "N/A"
        if isinstance(data_list, list):
            # Convert all items to string and join with newlines + bullets
            return "\n- " + "\n- ".join([str(item) for item in data_list])
        return str(data_list)

    insights = format_list(project_data.get('audio_results', {}).get('insights', []))
    automation = format_list(project_data.get('audio_results', {}).get('automation_opportunities', []))
    
    return f"""# Clinical AI Operations Report
    
## 🎯 Overview
**Generated on:** {project_data.get('date', 'N/A')}
**Model Used:** {project_data.get('model', 'N/A')}

## 🎙️ Audio Insight Summary
### 💡 Key Summary
{project_data.get('audio_results', {}).get('summary', 'N/A')}

### 🚀 Actionable Items
{insights}

### 🤖 Automation Opportunities
{automation}
"""

# Mock data causing the error (list of dicts)
mock_data = {
    "audio_results": {
        "insights": [{"task": "Review labs", "priority": "high"}, "Schedule follow-up"],
        "automation_opportunities": ["Auto-email patients"]
    }
}

try:
    report = generate_markdown_report_fix(mock_data)
    print("Report generated successfully!")
    print(report)
except Exception as e:
    print(f"Error: {e}")
