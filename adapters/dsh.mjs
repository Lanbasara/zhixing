import { readFileSync, lstatSync, realpathSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const name = 'zhixing-skills';
export const inject = ['skills'];
const root = realpathSync(join(dirname(fileURLToPath(import.meta.url)), '..'));

function resource(parts) {
  let path = root;
  for (const part of parts) {
    if (!/^[a-zA-Z0-9_.-]+$/.test(part) || part === '..') throw new Error('Invalid resource path');
    path = join(path, part);
    if (lstatSync(path).isSymbolicLink()) throw new Error('Linked skill resources are not supported');
  }
  const info = lstatSync(path);
  if (!info.isFile() || info.size > 262144) throw new Error('Invalid skill resource');
  return { path, text: readFileSync(path, 'utf8') };
}

export function apply(ctx) {
  const catalog = JSON.parse(resource(['host', 'catalog.json']).text);
  if (!Array.isArray(catalog) || !catalog.length || catalog.length > 64) throw new Error('Invalid catalog');
  const seen = new Set();
  const skills = catalog.map(entry => {
    if (!entry || typeof entry.name !== 'string' || !/^[a-z][a-z0-9-]{0,47}$/.test(entry.name)
        || entry.name.startsWith('zhixing-') || seen.has(entry.name)
        || typeof entry.description !== 'string' || !entry.description.trim() || entry.description.length > 4096
        || typeof entry.invocation?.modelInvocable !== 'boolean' || entry.invocation?.userInvocable !== true) {
      throw new Error('Invalid skill catalog entry');
    }
    seen.add(entry.name);
    const { path, text } = resource(['skills', entry.name, 'SKILL.md']);
    const match = text.match(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)([\s\S]*)$/);
    if (!match || !match[1].trim()) throw new Error('Missing skill body');
    return {
      name: 'zhixing-' + entry.name,
      description: entry.description,
      invocation: { ...entry.invocation },
      source: 'bundled',
      content: match[1].trim(),
      path,
      resourceBase: { kind: 'directory', path: dirname(path) },
    };
  });
  for (const skill of skills) ctx.skills.register(skill);
}
