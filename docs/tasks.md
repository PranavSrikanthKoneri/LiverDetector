Person 1: imaging input (DICOM to liver boxes)

1. Unzip the upload and strip patient info (names, IDs) from the DICOM tags.
2. Find the in-phase and opposed-phase series using the DICOM tags (series description, echo time). No model needed.
3. Run TotalSegmentator --task total_mr --roi_subset liver.
4. Liver slices are the ones where the mask is not empty. Keep the 5 slices with the most liver.
5. Box for each slice: the mask's min/max coordinates plus 5 px margin.
6. Test on CHAOS T1-DUAL patients.

Deliverable: imaging/load.py

Person 2: MedSAM segmentation plus the math

1. Run MedSAM zero-shot on each box. No fine-tuning.
2. If MedSAM looks wrong on a slice, fall back to the TotalSegmentator mask.
3. Fat % = (IP − OP) / (2 × IP), computed inside the mask, shrunk about 3 px from the edge. Take the median and clip to 0–50%. More than 5% means steatosis is likely.
4. Texture: GLCM on liver pixels only, with 32 gray levels. Label it "exploratory."
5. Average the results across the kept slices.
6. Make illustrative stage images F0–F4 with OpenCV.

Deliverable: imaging/analyze.py

Person 3: tabular model plus projection

1. Download NHANES 2017–18: DEMO, BMX, DIQ, ALQ, LUX, and BIOPRO + CBC for the NFS baseline.
2. Make the label from liver stiffness (LSM): below 8.2 kPa is F0–1; 8.2 to 9.7 is F2; 9.7 to 13.6 is F3; 13.6 and above is F4.
3. Train XGBoost with 5-fold cross-validation. Report AUROC for ≥F2, not accuracy.
4. Compare against the NFS formula on the same people.
5. Write project() using 14.3 vs 7.1 years per stage (Singh 2015), and return a range.

Deliverables: tabular/predict.py, model.joblib, model_card.json

Person 4: frontend plus LLM summary

1. Screens: upload the zip, questionnaire, results (overlay, fat %, stage), 0–20 year slider, "slower-progression scenario" toggle, and a Recharts chart with a shaded range.
2. Build it all against mock JSON matching the contract.
3. LLM summary: send only the numbers. Its rules are:
   - use plain language
   - give general lifestyle tips
   - tell the user to see a doctor
   - never name medications
   - never diagnose
4. Put a "Not diagnostic" disclaimer on screen.

Integration (FastAPI, whoever finishes first)

POST /analyze runs, in order: load_and_locate, segment_and_measure, predict_stage, project, summarize, then returns the JSON.

Checkpoints

- Tonight: all four functions return mock data in the contract shape.
- Sunday 9 AM: the real pipeline works end to end on one CHAOS case.
- Sunday noon: feature freeze, then rehearse.
- Backup: have 3 pre-computed demo cases ready in case a live upload fails.