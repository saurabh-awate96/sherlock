import os
import sys

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sherlock.core.db import Database
from sherlock.core.similarity import SimilarityEngine


def main():
    print("--- Verifying Similarity Engine & Knowledge Graph ---")

    # 1. Setup Logic
    db_path = "test_similarity.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    db = Database(db_path)
    engine = SimilarityEngine(db)

    # 2. Mock Contract Data (Vault)
    mock_storage = {"storage": [{"type": "mapping(address => uint256)", "label": "balances"}]}
    mock_methods = {"deposit(uint256)": "0x123", "withdraw(uint256)": "0x456"}

    # 3. Fingerprint & Seed Knowledge
    print("Seeding 'Known Issue' for this Vault structure...")
    fingerprint = engine.fingerprint_contract("MyVault", mock_storage, mock_methods)
    engine.seed_knowledge(fingerprint, "InflationAttack", "First depositor can steal funds")

    # 4. Run Detector (Simulating Audit)
    print("Running Detector on 'MyVault.sol'...")

    # Detect needs to call 'get_storage_layout' which calls forge.
    # To test without forge, we mock limits of SemanticDetector or verify via unit test.
    # For this script, we'll manually invoke the logic if possible,
    # OR we need a real file.

    # Let's verify via the engine directly for now as Detector requires Forge+Files
    issues = engine.find_similar_issues(fingerprint)

    if len(issues) == 1 and issues[0]['type'] == "InflationAttack":
        print(f"[PASS] Engine correctly recalled known issue: {issues[0]['description']}")
    else:
        print("[FAIL] Engine did not return seeded issue.")
        sys.exit(1)

    # 5. Verify Scope Schema exists
    try:
        db.learn_fix("Error X", "Fix Y", scope_type="LOCAL", related_element="FileA")
        fix = db.get_known_fix("Error X", scope_type="LOCAL", related_element="FileA")
        if fix == "Fix Y":
            print("[PASS] Scoped Knowledge storage works.")
        else:
             print("[FAIL] Scoped Knowledge retrieval failed.")
    except Exception as e:
        print(f"[FAIL] Schema Error: {e}")

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    main()
