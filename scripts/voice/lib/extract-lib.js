'use strict';

const fs = require('fs');

function countEntries(calibrationPath) {
  if (!fs.existsSync(calibrationPath)) return 0;
  const matches = fs.readFileSync(calibrationPath, 'utf-8').match(/^## Entry \d+/gm);
  return matches ? matches.length : 0;
}

// Parse the raw LLM output into an array of entry objects.
// Each entry block is separated by a blank line and contains four labeled fields.
// Handles multi-line field values (continuation lines joined with space) and
// ignores embedded field labels within a field's continuation lines.
function parseEntries(text) {
  const LABEL_RE = /^(AI-ish|Preferred|Why|Pattern):[ \t]*(.*)/i;
  const FIELD_MAP = { 'ai-ish': 'aiIsh', 'preferred': 'preferred', 'why': 'why', 'pattern': 'pattern' };
  const blocks = text.split(/\n\s*\n/).filter(b => /AI-ish:/i.test(b));

  return blocks.map(block => {
    const values = {};
    let cur = null;
    for (const line of block.split('\n')) {
      const m = line.match(LABEL_RE);
      if (m) {
        cur = FIELD_MAP[m[1].toLowerCase()];
        if (cur) values[cur] = m[2].trim();
      } else if (cur && line.trim()) {
        values[cur] += ' ' + line.trim();
      }
    }
    const entry = { aiIsh: values.aiIsh, preferred: values.preferred, why: values.why, pattern: values.pattern };
    return (entry.aiIsh && entry.preferred && entry.why && entry.pattern) ? entry : null;
  }).filter(Boolean);
}

function formatEntry(n, title, entry) {
  return `\n## Entry ${n}: ${title}\nAI-ish: ${entry.aiIsh}\nPreferred: ${entry.preferred}\nWhy: ${entry.why}\nPattern: ${entry.pattern}`;
}

module.exports = { countEntries, parseEntries, formatEntry };
