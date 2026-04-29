#!/usr/bin/env node
'use strict';

require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ---------------------------------------------------------------------------
// CLI args
// ---------------------------------------------------------------------------

function parseArgs() {
  const args = process.argv.slice(2);
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2);
      const val = args[i + 1];
      if (!val || val.startsWith('--')) {
        console.error(`Missing value for ${args[i]}`);
        process.exit(1);
      }
      result[key] = val;
      i++;
    }
  }
  return result;
}

function readFile(filePath) {
  const resolved = path.resolve(filePath);
  if (!fs.existsSync(resolved)) throw new Error(`File not found: ${filePath}`);
  return fs.readFileSync(resolved, 'utf-8').trim();
}

// ---------------------------------------------------------------------------
// Calibration helpers (shared with tests via scripts/lib/extract-lib.js)
// ---------------------------------------------------------------------------

const { countEntries, parseEntries, formatEntry } = require('./lib/extract-lib');

// ---------------------------------------------------------------------------
// Interactive prompt
// ---------------------------------------------------------------------------

function ask(rl, question) {
  return new Promise(resolve => rl.question(question, resolve));
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

let rl = null;

async function main() {
  const args = parseArgs();
  const voice = args['voice'];
  const aiDraftPath = args['ai-draft'];
  const preferredPath = args['preferred'];
  const nextDraftPath = args['next-draft'];

  if (!voice || !aiDraftPath || !preferredPath || !nextDraftPath) {
    console.error(
      'Usage: node scripts/extract-pairs.js \\\n' +
      '  --voice <name> \\\n' +
      '  --ai-draft <path> \\\n' +
      '  --preferred <path> \\\n' +
      '  --next-draft <path>'
    );
    process.exit(1);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error('Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.');
    process.exit(1);
  }

  const root = path.join(__dirname, '../..');
  const voiceDir = path.join(root, 'resources', 'context', 'voices', voice);
  const calibrationPath = path.join(voiceDir, 'calibration.md');
  const dnaPath = path.join(voiceDir, 'dna.md');

  if (!fs.existsSync(voiceDir)) {
    console.error(`Voice directory not found: resources/context/voices/${voice}`);
    process.exit(1);
  }

  const aiDraft = readFile(aiDraftPath);
  const preferred = readFile(preferredPath);
  const nextDraft = readFile(nextDraftPath);
  const dna = fs.existsSync(dnaPath) ? fs.readFileSync(dnaPath, 'utf-8').trim() : '';

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const outputDir = path.join(root, 'outputs', voice, timestamp);
  fs.mkdirSync(outputDir, { recursive: true });

  const client = new Anthropic();

  // -------------------------------------------------------------------------
  // Step 1: Extract
  // -------------------------------------------------------------------------

  console.log('\n=== Step 1: Extracting correction entries ===\n');

  const extractionResponse = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system:
      'You are a voice pattern extractor. You receive two versions of a LinkedIn post and extract calibration entries.',
    messages: [
      {
        role: 'user',
        content:
          `INPUT_A (AI draft — what was wrong):\n${aiDraft}\n\n` +
          `INPUT_B (corrected version — what was actually sent):\n${preferred}\n\n` +
          `For each substantive correction, extract one entry with exactly these four fields:\n\n` +
          `AI-ish: [copy the specific phrase or sentence from INPUT_A that was changed]\n` +
          `Preferred: [copy the corresponding phrase or sentence from INPUT_B that replaced it]\n` +
          `Why: [1 sentence explaining the voice judgment — be specific about WHY, not just WHAT]\n` +
          `Pattern: [1 reusable instruction in imperative form, testable against any sentence — no adjectives]\n\n` +
          `Rules:\n` +
          `- Extract 2-4 entries. Ignore typo fixes, punctuation-only changes, and word swaps with identical meaning.\n` +
          `- If fewer than 2 substantive corrections exist, output only: "Input pair too similar for meaningful extraction."\n` +
          `- Bad Pattern: "Write more naturally." (untestable adjective)\n` +
          `- Good Pattern: "Avoid sentence-final calls to action. End on a fact, number, or question instead."\n` +
          `- If you cannot write a testable Pattern for a correction, skip that entry.\n` +
          `- Separate entries with a blank line. Output only the entries. No preamble, no summary.`,
      },
    ],
  });

  const rawExtraction = extractionResponse.content[0].text.trim();
  console.log(rawExtraction);
  console.log();

  fs.writeFileSync(path.join(outputDir, 'proposed-entries.md'), rawExtraction);

  if (rawExtraction.toLowerCase().includes('too similar for meaningful extraction')) {
    console.log('No entries extracted — pair too similar. Exiting.');
    process.exit(0);
  }

  const entries = parseEntries(rawExtraction);
  if (entries.length === 0) {
    console.log('Could not parse entries. Check outputs/' + voice + '/' + timestamp + '/proposed-entries.md');
    process.exit(1);
  }

  // -------------------------------------------------------------------------
  // Step 2: Interactive review
  // -------------------------------------------------------------------------

  rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const approvedEntries = [];

  console.log(`=== Step 2: Review ${entries.length} proposed entries ===\n`);

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    console.log(`Entry ${i + 1} of ${entries.length}:`);
    console.log(`  AI-ish:    ${entry.aiIsh}`);
    console.log(`  Preferred: ${entry.preferred}`);
    console.log(`  Why:       ${entry.why}`);
    console.log(`  Pattern:   ${entry.pattern}`);
    console.log();

    const action = (await ask(rl, '  [a]ccept / [e]dit / [s]kip: ')).trim().toLowerCase();

    if (action === 'e') {
      const newWhy = (await ask(rl, `  Why (Enter to keep): `)).trim();
      const newPattern = (await ask(rl, `  Pattern (Enter to keep): `)).trim();
      entry.why = newWhy || entry.why;
      entry.pattern = newPattern || entry.pattern;
    }

    if (action === 'a' || action === 'e') {
      const title = (await ask(rl, '  Title (short, e.g. "Avoid slogan endings"): ')).trim() || 'Untitled';
      approvedEntries.push({ ...entry, title });
      console.log('  → Accepted.\n');
    } else {
      console.log('  → Skipped.\n');
    }
  }

  rl.close();

  if (approvedEntries.length === 0) {
    console.log('No entries approved. Exiting.');
    process.exit(0);
  }

  // -------------------------------------------------------------------------
  // Step 3: Append to calibration.md
  // -------------------------------------------------------------------------

  if (!fs.existsSync(calibrationPath)) {
    fs.writeFileSync(calibrationPath, `# Calibration: ${voice}\n`);
  }

  const startN = countEntries(calibrationPath) + 1;
  const toAppend = approvedEntries.map((e, i) => formatEntry(startN + i, e.title, e)).join('\n');
  fs.appendFileSync(calibrationPath, toAppend + '\n');

  fs.writeFileSync(path.join(outputDir, 'approved-entries.md'), toAppend.trim());
  console.log(`=== Step 3: Appended ${approvedEntries.length} entries to resources/context/voices/${voice}/calibration.md ===\n`);

  // -------------------------------------------------------------------------
  // Step 4: Rewrite next draft
  // -------------------------------------------------------------------------

  console.log('=== Step 4: Rewriting next draft ===\n');

  const calibrationContent = fs.readFileSync(calibrationPath, 'utf-8').trim();

  const rewriteResponse = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 2048,
    system:
      `You are a voice-accurate writing assistant.\n\n` +
      `Voice DNA:\n${dna}\n\n` +
      `Calibration rules:\n${calibrationContent}`,
    messages: [
      {
        role: 'user',
        content:
          `Rewrite the draft below applying the voice DNA and calibration rules above.\n` +
          `Output only the rewritten draft. No preamble, no explanation.\n\n` +
          `Draft:\n${nextDraft}`,
      },
    ],
  });

  const rewrittenDraft = rewriteResponse.content[0].text.trim();
  console.log(rewrittenDraft);
  console.log();

  fs.writeFileSync(path.join(outputDir, 'rewritten-draft.md'), rewrittenDraft);

  // -------------------------------------------------------------------------
  // Step 5: Metadata
  // -------------------------------------------------------------------------

  fs.writeFileSync(
    path.join(outputDir, 'run-metadata.json'),
    JSON.stringify(
      {
        voice,
        timestamp,
        model: 'claude-sonnet-4-6',
        entriesProposed: entries.length,
        entriesApproved: approvedEntries.length,
        inputs: { aiDraft: aiDraftPath, preferred: preferredPath, nextDraft: nextDraftPath },
        usage: {
          extraction: extractionResponse.usage,
          rewrite: rewriteResponse.usage,
        },
      },
      null,
      2
    )
  );

  console.log(`=== Done. Outputs: outputs/${voice}/${timestamp}/ ===`);
}

main().catch(err => {
  if (rl) rl.close();
  console.error('\nError:', err.message);
  process.exit(1);
});
