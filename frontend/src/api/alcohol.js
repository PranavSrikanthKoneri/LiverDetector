import policy from "../../../backend/demo/alcohol_policy.json" with { type: "json" };

/** Legacy API compatibility: derive this information only from submitted answers. */
export function alcoholFromAnswers(answers) {
  const drinks = answers?.drinks_week;
  const male = answers?.male;
  if (typeof drinks !== 'number' || !Number.isFinite(drinks) || drinks < 0 || drinks > policy.maximum_drinks || ![0, 1].includes(male)) return null;
  const elevatedFrom = policy.elevated_from[male === 1 ? 'men' : 'women'];
  const category = drinks >= policy.critical_from ? 'critical' : drinks >= elevatedFrom ? 'elevated' : 'low';
  return {
    category,
    label: policy.ranges.find(row => row.category === category).label,
    drinks_week: drinks,
    sex_label: male === 1 ? 'Men' : 'Women',
    model_independent: true,
    ranges: policy.ranges,
    range_note: policy.range_note,
    caveat: policy.caveat,
  };
}

/** Only elevated intake gets a visible message; lower intake has no section. */
export function alcoholWarning(result) {
  const template = policy.warning_messages[result?.category];
  const drinks = result?.drinks_week;
  if (!template || typeof drinks !== 'number' || !Number.isFinite(drinks) || drinks < 0 || drinks > policy.maximum_drinks) return null;
  return { severity: result.category, message: template.replace('{drinks}', String(drinks)) };
}
