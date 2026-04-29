import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const pluginEntryPath = new URL('./index.ts', import.meta.url);

test('plugin source declares expected lifecycle hooks, command, and service wiring', async () => {
  const text = await readFile(pluginEntryPath, 'utf8');

  assert.match(text, /id: "langgraph-orchestrator"/);
  assert.match(text, /api\.on\("before_agent_start"/);
  assert.match(text, /api\.on\("agent_end"/);
  assert.match(text, /api\.on\("before_compaction"/);
  assert.match(text, /api\.registerCommand\(/);
  assert.match(text, /name: "langgraph"/);
  assert.match(text, /api\.registerService\(/);
  assert.match(text, /id: "langgraph-orchestrator"/);
});

test('plugin source uses shared contracts, helpers, and runtime client modules', async () => {
  const text = await readFile(pluginEntryPath, 'utf8');

  assert.match(text, /from "\.\/contracts\.ts"/);
  assert.match(text, /from "\.\/runtime-helpers\.js"/);
  assert.match(text, /from "\.\/runtime-client\.js"/);
  assert.match(text, /withGracefulFailure/);
  assert.match(text, /buildRuntimeEnvelope/);
});
