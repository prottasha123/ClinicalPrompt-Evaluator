import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.curdir))

from logic import evaluate_json

def test_semantic_evaluation():
    print("Running Semantic Evaluation Test...")
    
    extracted = {
        "Patient Age": "45 years old",
        "Diagnosis": "Stage II Breast Cancer",
        "Dosage": "50mg once daily",
        "Status": "Stable"
    }
    
    ground_truth = {
        "Patient Age": "45",
        "Diagnosis": "Breast Cancer Stage 2",
        "Dosage": "50 mg QD",
        "Status": "Improving" # Should be a mismatch
    }
    
    stats = evaluate_json(extracted, ground_truth)
    
    print("\nResults:")
    print(f"Accuracy Score: {stats['accuracy_score']}%")
    print(f"Matches: {stats['matches']}")
    print(f"Mismatches: {len(stats['mismatches'])}")
    
    for m in stats['mismatches']:
        print(f"  Field: {m['field']} | Extracted: {m['extracted']} | GT: {m['ground_truth']}")

    # Expected: Age, Diagnosis, Dosage should match semantically. Status should mismatch.
    # Accuracy should be 75%
    if stats['accuracy_score'] >= 75.0:
        print("\n✅ Test Passed: Semantic evaluation is working!")
    else:
        print("\n❌ Test Failed: Accuracy too low.")

if __name__ == "__main__":
    test_semantic_evaluation()
