# Risk Prediction Model Improvements

## Summary
This project improved the risk prediction pipeline by addressing class imbalance, adding text-derived features, and engineering additional signals to strengthen model performance.

## Improvements Applied
1. **SMOTE Resampling**: Balanced class distribution for Medium/High classes during training.
2. **TF-IDF Text Features**: Extracted 150 features from issue Summary/Description fields.
3. **Derived Features**: Added story size, description length, and comment interaction signals.
4. **Real Jira Data**: Added a fetch pipeline for production Jira snapshots (heuristic labels).

## Results (Latest Baseline)
| Metric | Value |
|--------|-------|
| **Accuracy** | 0.456 |
| **Macro F1** | 0.429 |

## Real Jira Snapshot Validation
- **Dataset:** 5 real Jira issues (demo project)
- **Accuracy:** 0.600
- **Macro F1:** 0.375
- **Note:** All 5 issues were labeled Low, so Medium/High metrics are zero-support.

## Key Findings
- **Class imbalance was a primary driver** of poor Medium/High recall until SMOTE was applied.
- **Text features carry risk signal** and should remain part of the feature space (TF-IDF 150).
- **Derived features help interpretability** and support scenario analysis in demos.
- **Real Jira snapshots** are now supported through a dedicated fetch script.

## Next Steps
1. Add expert labels for a subset of Jira issues to validate model quality on real data.
2. Re-run ablations on real data to re-confirm the best configuration.
3. Update SHAP explainability artifacts with the new derived feature columns.
