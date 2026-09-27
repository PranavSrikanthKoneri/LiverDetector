import { useState } from "react";
import { ArrowRightIcon, ArrowLeftIcon } from "@radix-ui/react-icons";
import "./QuestionnairePage.css";

export default function QuestionnairePage({ onBack, onSubmit }) {
  const [form, setForm] = useState({
    age: "",
    male: "1",
    bmi: "",
    waist_cm: "",
    diabetes: "0",
    drinks_week: "",
  });

  const [errors, setErrors] = useState({});

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const copy = { ...prev };
        delete copy[field];
        return copy;
      });
    }
  }

  function validate() {
    const errs = {};
    if (!form.age || !Number.isInteger(+form.age) || +form.age < 18 || +form.age > 120)
      errs.age = "Enter a valid age (18–120)";
    if (!form.bmi || isNaN(form.bmi) || +form.bmi < 10 || +form.bmi > 80)
      errs.bmi = "Enter a valid BMI (10–80)";
    if (form.waist_cm !== "" && (isNaN(form.waist_cm) || +form.waist_cm < 40 || +form.waist_cm > 250))
      errs.waist_cm = "Enter a valid waist circumference (40–250 cm) or leave blank";
    if (form.drinks_week === "" || !Number.isFinite(+form.drinks_week) || +form.drinks_week < 0 || +form.drinks_week > 200)
      errs.drinks_week = "Enter weekly alcohol intake (0–200)";
    return errs;
  }

  function handleSubmit(e) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    onSubmit({
      age: parseInt(form.age, 10),
      male: Number(form.male),
      bmi: parseFloat(form.bmi),
      waist_cm: form.waist_cm === "" ? null : parseFloat(form.waist_cm),
      diabetes: Number(form.diabetes),
      drinks_week: parseFloat(form.drinks_week),
    });
  }

  return (
    <div className="page">
      <div className="container stack stack-xl">
        <div className="questionnaire-hero">
          <h2>Clinical Questionnaire</h2>
          <p className="text-secondary">
            Enter patient clinical parameters.
          </p>
        </div>

        <form
          className="questionnaire-form card"
          onSubmit={handleSubmit}
          id="clinical-questionnaire-form"
        >
          <div className="questionnaire-grid">
            <div className="input-group">
              <label className="input-label" htmlFor="q-age">Age (years)</label>
              <input
                id="q-age"
                className={`input-field ${errors.age ? "input-error" : ""}`}
                type="number"
                placeholder="e.g. 54"
                value={form.age}
                onChange={(e) => update("age", e.target.value)}
              />
              {errors.age && <span className="input-error-msg">{errors.age}</span>}
            </div>

            <div className="input-group">
              <label className="input-label" htmlFor="q-bmi">BMI (kg/m²)</label>
              <input
                id="q-bmi"
                className={`input-field ${errors.bmi ? "input-error" : ""}`}
                type="number"
                step="0.1"
                placeholder="e.g. 31.2"
                value={form.bmi}
                onChange={(e) => update("bmi", e.target.value)}
              />
              {errors.bmi && <span className="input-error-msg">{errors.bmi}</span>}
            </div>

            <div className="input-group">
              <label className="input-label" htmlFor="q-waist">Waist Circumference (cm, optional)</label>
              <input
                id="q-waist"
                className={`input-field ${errors.waist_cm ? "input-error" : ""}`}
                type="number"
                step="0.1"
                placeholder="e.g. 104"
                value={form.waist_cm}
                onChange={(e) => update("waist_cm", e.target.value)}
              />
              {errors.waist_cm && <span className="input-error-msg">{errors.waist_cm}</span>}
            </div>

            <div className="input-group">
              <label className="input-label" htmlFor="q-drinks">Weekly Alcohol Intake (drinks)</label>
              <input
                id="q-drinks"
                className={`input-field ${errors.drinks_week ? "input-error" : ""}`}
                type="number"
                step="0.1"
                placeholder="e.g. 3"
                value={form.drinks_week}
                onChange={(e) => update("drinks_week", e.target.value)}
              />
              {errors.drinks_week && <span className="input-error-msg">{errors.drinks_week}</span>}
            </div>

            <div className="input-group">
              <label className="input-label" htmlFor="q-gender">Biological Sex</label>
              <select
                id="q-gender"
                className="input-field"
                value={form.male}
                onChange={(e) => update("male", e.target.value)}
              >
                <option value="1">Male</option>
                <option value="0">Female</option>
              </select>
            </div>

            <div className="input-group">
              <label className="input-label" htmlFor="q-diabetes">Type 2 Diabetes</label>
              <select
                id="q-diabetes"
                className="input-field"
                value={form.diabetes}
                onChange={(e) => update("diabetes", e.target.value)}
              >
                <option value="0">No</option>
                <option value="1">Borderline</option>
                <option value="2">Yes</option>
              </select>
            </div>
          </div>

          <div className="questionnaire-actions">
            <button type="button" className="btn btn-secondary" onClick={onBack} id="questionnaire-back-btn">
              <ArrowLeftIcon width={16} height={16} />
              Back
            </button>
            <button type="submit" className="btn btn-primary btn-lg" id="questionnaire-submit-btn">
              Analyze
              <ArrowRightIcon width={18} height={18} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
