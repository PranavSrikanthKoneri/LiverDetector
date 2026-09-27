# LLD-MMRI review

Reviewed the [dataset repository](https://github.com/LMMMEng/LLD-MMRI-Dataset),
its linked [Hugging Face release](https://huggingface.co/datasets/wanglab/LLD-MMRI-MedSAM2),
and the official [preprocessing and classification code](https://github.com/LMMMEng/LLD-MMRI2023/tree/main/main).

The dataset card reports 498 unique patients, eight MRI sequences per lesion,
and 3,984 annotated sequence cases. These are not 3,984 independent patients.
Sequences include noncontrast, arterial, venous, delayed, T2, DWI, T1 in-phase
and out-of-phase. The MedSAM2 extension provides lesion masks produced with
human involvement. The linked dataset totals about 18.7 GB.

Useful future roles:

- Evaluate or fine-tune lesion segmentation with the lesion masks.
- Train a lesion classification branch using seven categories (HCC,
  cholangiocarcinoma, metastasis, cyst, hemangioma, FNH and abscess), or the
  supplied benign/malignant grouping.
- Test texture extraction on lesion regions separately from surrounding liver.
- Investigate lesion exclusion from whole-liver texture ROIs. This requires
  detection of lesions first; whole-liver MedSAM masks alone do not provide it.

It is not a labelled whole-liver texture-quality dataset and supplies no verified
quantitative fat ground truth for our current estimator. It should not be pooled
with CHAOS to create a healthy/diseased texture classifier without controlling
for source and acquisition differences.

The main repository contains a dataset README; the linked implementation supplies
lesion-centered crop preparation, a multi-phase 3D UniFormer baseline, and training
and prediction scripts. Its documented baseline expects eight input sequences;
it cannot be dropped into our two-echo pipeline unchanged. The annotations include
true spacing and lesion boxes. Inspect these when converting NIfTI data instead
of assuming our DICOM loader or native spacing conventions apply. Some challenge
labels are -1 (withheld), which must not become a disease class. Split and evaluate
at patient level across all phases and lesions.

The dataset repository states noncommercial research use and additional limits
on redistribution. Its stated license is CC BY-NC 4.0; consult the complete
agreement on the repository before sharing copies. No LLD data, external code,
weights or dependencies were downloaded or integrated during this review.

Recommendation: retain as a candidate for a separate lesion-analysis project.
Use the implemented CHAOS-based numerical QC for the current texture task.
