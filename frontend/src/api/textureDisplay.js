/** Always use the patient aggregate, never the currently displayed slice. */
export function describeTextureQuality(report) {
  const labels = {
    no_flags_detected: 'No flags detected',
    review_required: 'Review required',
    invalid: 'Not evaluable',
  };
  const quality = report?.quality;
  return {
    label: labels[quality?.status] ?? 'Unavailable',
    needsReview: ['review_required', 'invalid'].includes(quality?.status),
    flags: (quality?.flags ?? []).map(flag => flag.replaceAll('_', ' ')),
  };
}
