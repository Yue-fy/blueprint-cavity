/* One deterministic checker used by the browser and the local CLI. No eval. */
(function (root) {
  'use strict';
  function gradeText(input) {
    const unknown = (msg) => ({status: 'unscored', cls: 'mid', msg: msg || 'Unscored. Use exactly one ANSWER: number or a recognized VERDICT line.'});
    if (typeof input !== 'string' || input.length > 100000) return unknown();
    const text = input.replace(/−/g, '-').replace(/[Ａ-Ｚａ-ｚ：]/g, c => c.normalize('NFKC'));
    const fields = text.split(/\r?\n/).filter(line => /^\s*(ANSWER|VERDICT)\s*:/i.test(line));
    if (fields.length !== 1 || (text.match(/\b(?:ANSWER|VERDICT)\s*:/gi) || []).length !== 1) return unknown('Unscored. Supply one unambiguous answer field.');
    const line = fields[0].trim();
    if (/^VERDICT\s*:/i.test(line)) {
      if (/^VERDICT\s*:\s*CORRECT\s*$/i.test(line)) return {status:'incorrect_verdict', cls:'bad', msg:'The supplied step is incorrect; this verdict accepts it.'};
      if (/^VERDICT\s*:\s*INCORRECT(?:\s*[—–-]\s*L\s*=\s*\S.*)?\s*$/i.test(line)) return {status:'manual_review', cls:'mid', msg:'Rejection recognized. Review the formula and reasoning manually; no proof score is assigned.'};
      return unknown('Unscored. The review verdict is unrecognized or ambiguous.');
    }
    let value = line.replace(/^ANSWER\s*:\s*/i, '');
    if (value.includes(';')) {
      const full = /^L\s*=\s*[^;]+;\s*L\(\s*0\.07\s*,\s*-0\.4\s*,\s*1\.7\s*\)\s*=\s*(.+)$/i.exec(value);
      if (!full) return unknown();
      value = full[1];
    }
    const supers = '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺', digits = '0123456789-+';
    value = value.replace(/([×x*]\s*10)([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s*$/, (_, base, exp) => base + '^' + [...exp].map(c => digits[supers.indexOf(c)]).join(''));
    const match = /^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))(?:(?:[eE]([-+]?\d+))|(?:\s*[×x*]\s*10\s*\^?\s*([-+]?\d+)))?\s*$/.exec(value);
    if (!match) return unknown('Unscored. The numeric field must contain only one finite number.');
    const answer = Number(match[1]) * 10 ** Number(match[2] || match[3] || 0);
    if (!Number.isFinite(answer)) return unknown();
    const right = .07 ** 2 / (2 * (1 - .07 * (-.4 + 2 * 1.7)) ** 2);
    const trap = .07 ** 2 / (2 * (1 - .07 * -.4) ** 2);
    const det = `Answer ${answer.toPrecision(7)} · reference ${right.toPrecision(7)} · fixed parameters (0.07, −0.4, 1.7). Numeric tolerance: relative error < 0.001. Reasoning is not scored.`;
    if (Math.abs(answer / right - 1) < 1e-3) return {status:'numeric_match', cls:'good', msg:'Numeric value matches the reference. The formula and proof still need review.', det};
    if (Math.abs(answer / trap - 1) < 1e-3) return {status:'historical_value', cls:'bad', msg:'Numeric value matches the reported historical error.', det};
    return {status:'numeric_mismatch', cls:'bad', msg:'Numeric value does not match the reference.', det};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = gradeText;
  else root.gradeText = gradeText;
})(typeof globalThis !== 'undefined' ? globalThis : this);
