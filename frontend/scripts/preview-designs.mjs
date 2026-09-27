/** Local comparison launcher. No backend, data uploads, or external publishing. */
import { execFileSync, spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const records = execFileSync('git', ['worktree', 'list', '--porcelain'], { cwd: repo, encoding: 'utf8' }).trim().split(/\r?\n\r?\n/);
const locations = new Map(records.map(record => {
  const lines = record.split(/\r?\n/);
  return [lines.find(line => line.startsWith('branch '))?.slice('branch refs/heads/'.length), lines.find(line => line.startsWith('worktree '))?.slice(9)];
}));
const variants = [
  ['abstract-subtle', 'Schematic · subtle', 'A quiet introduction with a drawn liver outline.'],
  ['abstract-cinematic', 'Schematic · cinematic', 'The same illustration with greater depth and motion.'],
  ['mri-subtle', 'Research MRI · subtle', 'An actual anonymized research scan takes the lead.'],
  ['mri-cinematic', 'Research MRI · cinematic', 'The research image with a longer scrolling sequence.'],
  ['type-subtle', 'Typography · subtle', 'Words first, with a small interactive visual below.'],
  ['type-cinematic', 'Typography · cinematic', 'Large type, deeper reveals, and an evolving illustration.'],
].map(([name, label, description], index) => ({ name, label, description, port: 5181 + index, dir: locations.get(`frontend/${name}`) }));
for (const v of variants) {
  if (!v.dir || !existsSync(path.join(v.dir, 'frontend/node_modules/vite/bin/vite.js'))) {
    console.error(`Missing local worktree or dependencies for frontend/${v.name}. See frontend/DESIGN_PREVIEW.md.`);
    process.exit(1);
  }
}
const children = [];
let shuttingDown = false;
const server = createServer((request, response) => {
  if (request.url !== '/') { response.writeHead(404); response.end(); return; }
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>FibroLens design previews</title><style>
  *{box-sizing:border-box}body{background:#f7f7f2;color:#182a32;font:16px/1.6 system-ui,sans-serif;max-width:1100px;padding:48px 24px;margin:auto}h1{font-size:48px;line-height:1.1;letter-spacing:-.06em;font-weight:500}p{color:#53636a}main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:40px 0}article{background:white;border:1px solid #dce4dd;border-radius:16px;padding:28px}h2{font-size:22px;font-weight:500}a{color:#225e91;text-underline-offset:4px}nav{display:flex;gap:16px;flex-wrap:wrap}small{color:#53636a}@media(max-width:650px){main{grid-template-columns:1fr}h1{font-size:36px}}
  </style><h1>Six ways to see FibroLens.</h1><p>Three visual directions. Two motion treatments. All local, on separate branches.</p><main>${variants.map(v => `<article><small>frontend/${v.name}</small><h2>${v.label}</h2><p>${v.description}</p><nav><a href="http://127.0.0.1:${v.port}/" target="_blank" rel="noopener">Explore design ↗</a><a href="http://127.0.0.1:${v.port}/?preview=results" target="_blank" rel="noopener">Results layout ↗</a><a href="http://127.0.0.1:${v.port}/?preview=upload" target="_blank" rel="noopener">Upload</a><a href="http://127.0.0.1:${v.port}/?preview=questionnaire" target="_blank" rel="noopener">Questionnaire</a></nav></article>`).join('')}</main><p>Results previews contain labeled synthetic values. Real analysis still requires the GPU backend.</p><small>Keep the terminal open. Press Ctrl+C there to stop all six previews.</small></html>`);
});
function stop(code = 0) {
  if (shuttingDown) return;
  shuttingDown = true;
  children.forEach(child => child.kill());
  server.close();
  process.exitCode = code;
}
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
server.on('error', error => { console.error(error.message); stop(1); });
server.listen(5180, '127.0.0.1', () => {
  for (const v of variants) {
    const child = spawn(process.execPath, [path.join(v.dir, 'frontend/node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--port', String(v.port), '--strictPort'], { cwd: path.join(v.dir, 'frontend'), windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });
    children.push(child);
    child.stderr.on('data', data => process.stderr.write(`[${v.name}] ${data}`));
    child.on('error', error => { console.error(error.message); stop(1); });
    child.on('exit', code => { if (!shuttingDown) { console.error(`${v.name} stopped (${code}). Close any other preview using its port and retry.`); stop(1); } });
  }
  console.log('FibroLens comparison: http://127.0.0.1:5180/');
  console.log('Local only. Press Ctrl+C to stop all previews.');
});
