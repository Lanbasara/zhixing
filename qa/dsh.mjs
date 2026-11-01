import assert from 'node:assert/strict';
import { readFileSync, realpathSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = realpathSync(resolve(process.argv[2]));
const explicit = new Set(['setup', 'align', 'specify', 'plan', 'implement', 'evolve']);
const automatic = ['research', 'model', 'constrain', 'verify', 'review', 'debug', 'prototype', 'explain', 'report'];
const expected = [...explicit, ...automatic].sort();
const adapter = await import(pathToFileURL(resolve(root, 'host/dsh.mjs')).href);
const registered = [];
assert.deepEqual(adapter.inject, ['skills']);
adapter.apply({ skills: { register(value) { registered.push(value); } } });
assert.deepEqual(registered.map(skill => skill.name), expected.map(name => 'zhixing-' + name));
for (const skill of registered) {
  const shortName = skill.name.slice('zhixing-'.length);
  const original = readFileSync(resolve(root, 'skills', shortName, 'SKILL.md'), 'utf8');
  assert.equal(skill.path, resolve(root, 'skills', shortName, 'SKILL.md'));
  assert.equal(skill.content, original.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '').trim());
  assert.deepEqual(skill.resourceBase, { kind: 'directory', path: dirname(skill.path) });
  assert.deepEqual(skill.invocation, { modelInvocable: !explicit.has(shortName), userInvocable: true });
}
console.log('PASS: 15 DSH registrations, one prefix, 6 manual entries, original bodies and resource roots');
