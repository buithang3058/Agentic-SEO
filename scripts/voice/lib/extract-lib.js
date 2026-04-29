'use strict';

const fs = require('fs');

function countEntries(calibrationPath) {
  if (!fs.existsSync(calibrationPath)) return 0;
  const matches = fs.readFileSync(calibrationPath, 'utf-8').match(/^## Entry \d+/gm);
  return matches ? matches.length : 0;
}

// Parse the raw LLM output into an array of entry objects.
// Each entry block is separated by a blank line and contains four labeled fields.
function parseEntries(text) {
  const blocks = text.split(/\n\s*\n/).filter(b => /AI-ish:/i.test(b));
  return blocks.map(block => {
    const get = (field) => block.match(new RegExp(`^${field}:\\s*(.+)`, 'im'))?.[1]?.trim();
    const entry = {
      aiIsh: get('AI-ish'),
      preferred: get('Preferred'),
      why: get('Why'),
      pattern: get('Pattern'),
    };
    return (entry.aiIsh && entry.preferred && entry.why && entry.pattern) ? entry : null;
  }).filter(Boolean);
}

function formatEntry(n, title, entry) {
  return `\n## Entry ${n}: ${title}\nAI-ish: ${entry.aiIsh}\nPreferred: ${entry.preferred}\nWhy: ${entry.why}\nPattern: ${entry.pattern}`;
}

module.exports = { countEntries, parseEntries, formatEntry };
