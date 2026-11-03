# Quick Start: First 24 Hours

## Getting Started with Jira & Bug Tracking Datasets

If you only have 24 hours to get training data ready, follow this plan:

### Hour 0-1: Read & Decide
```
Read: DATASET_COMPARISON_MATRIX.md (focus on "Quick Decision Tree")
Decision: Which Tier are you using?
  → Tier 1 (Recommended): BugSwarm + Apache Jira + GitHub
  → Tier 2 (Full): Add Mozilla + Linux + GHArchive
  → Specialized: Security or performance focused
```

### Hour 1-2: Setup Environment
```bash
# Clone your framework
cd ~/final-year-project/ai-risk-prediction-framework

# Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests pandas numpy scikit-learn python-jira pygithub

# Set up credentials
export GITHUB_TOKEN="ghp_your_token_here"  # Optional but recommended
```

### Hour 2-8: Collect Data (In Parallel)
```bash
# Start all extractions in background
python data_extraction/apache_jira_extractor.py &
python data_extraction/github_issue_extractor.py &
python data_extraction/bugswarm_extractor.py &

# Monitor progress (should take ~6 hours total)
tail -f extraction.log
```

While extraction runs, read: `DATA_COLLECTION_GUIDE.md`

### Hour 8-10: Process Data
```bash
# Combine and normalize all datasets
python data_extraction/risk_prediction_prep.py

# Result files created:
# - risk_prediction_train.csv (80% for training)
# - risk_prediction_test.csv (20% for testing)
```

### Hour 10-20: Validate & Explore
```python
import pandas as pd

# Load your data
train = pd.read_csv("risk_prediction_train.csv")
test = pd.read_csv("risk_prediction_test.csv")

# Quick checks
print(f"Train size: {len(train)}, Test size: {len(test)}")
print(f"Risk distribution:\n{train['risk_category'].value_counts()}")
print(f"Missing values:\n{train.isnull().sum()}")

# Save statistics
print(f"Feature count: {len(train.columns)}")
print(f"Issues by source:\n{train['source_platform'].value_counts()}")
```

### Hour 20-24: Baseline Model
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pandas as pd

# Load data
train = pd.read_csv("risk_prediction_train.csv")
test = pd.read_csv("risk_prediction_test.csv")

# Prepare features (adjust based on your data)
feature_cols = [
    'title_length', 'description_length', 'priority_level',
    'time_open_days', 'has_assignee', 'num_labels', 'is_bug'
]

X_train = train[feature_cols].fillna(0)
y_train = (train['risk_category'] == 'High').astype(int)

X_test = test[feature_cols].fillna(0)
y_test = (test['risk_category'] == 'High').astype(int)

# Train baseline
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

y_pred = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.3f}")
print(f"Recall: {recall_score(y_test, y_pred, zero_division=0):.3f}")
print(f"F1-Score: {f1_score(y_test, y_pred, zero_division=0):.3f}")

# Feature importance
print("\nTop 5 Important Features:")
for feat, imp in sorted(zip(feature_cols, model.feature_importances_), 
                        key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {feat}: {imp:.3f}")

# Save model
import joblib
joblib.dump(model, "baseline_model.pkl")
print("\nModel saved to baseline_model.pkl")
```

---

## Expected Results After 24 Hours

✓ **Dataset**: 150,000+ issues collected and processed
✓ **Training Data**: Ready-to-use train/test split
✓ **Baseline Model**: Trained and evaluated
✓ **Performance**: Expected 70-75% baseline accuracy on binary classification
✓ **Features**: 15+ engineered features ready for ML
✓ **Documentation**: Complete data lineage recorded

---

## What To Do Next (Hours 24+)

1. **Improve Model** (4-8 hours)
   - Add more features (NLP, embeddings)
   - Try different algorithms (XGBoost, LightGBM)
   - Hyperparameter tuning
   - Cross-validation

2. **Add More Data** (8-16 hours)
   - Include Tier 2 datasets (Mozilla, Linux)
   - Increase Apache Jira projects
   - Add GHArchive data

3. **Deploy** (4-8 hours)
   - Create inference API
   - Containerize with Docker
   - Set up monitoring

---

## Files You'll Have After 24 Hours

```
project_root/
├── risk_prediction_train.csv      (80k issues)
├── risk_prediction_test.csv       (20k issues)
├── baseline_model.pkl             (trained model)
├── data_quality_report.json       (statistics)
└── baseline_performance.txt       (metrics)
```

---

## Quick Troubleshooting

**Problem**: GitHub rate limit hit
**Solution**: 
```bash
export GITHUB_TOKEN="ghp_your_token"  # Get from https://github.com/settings/tokens
```

**Problem**: Jira API timeout
**Solution**: Reduce batch_size in apache_jira_extractor.py from 50 to 25

**Problem**: Out of memory during processing
**Solution**: Process in chunks (modify risk_prediction_prep.py to use dask)

**Problem**: No issues collected
**Solution**: Check internet connection, verify API URLs, check credentials

---

## Commands Cheat Sheet

```bash
# Activate environment
source venv/bin/activate

# Run extraction
python data_extraction/apache_jira_extractor.py
python data_extraction/github_issue_extractor.py
python data_extraction/bugswarm_extractor.py

# Process data
python data_extraction/risk_prediction_prep.py

# Quick analysis
python -c "import pandas as pd; df=pd.read_csv('risk_prediction_train.csv'); print(f'Size: {len(df)}'); print(df['risk_category'].value_counts())"

# Train baseline
python << 'EOF'
# ... baseline model code above ...
EOF
```

---

## Success Criteria

After 24 hours, you should have:

- [ ] At least 100,000 issues collected
- [ ] Train/test CSV files created
- [ ] < 20% missing values in key fields
- [ ] Baseline model trained
- [ ] Accuracy > 70% on test set
- [ ] Data lineage documented
- [ ] Model saved and tested

---

**Total Effort**: 24 hours  
**Result**: Production-ready training dataset + baseline model  
**Next Steps**: Model improvement and deployment
