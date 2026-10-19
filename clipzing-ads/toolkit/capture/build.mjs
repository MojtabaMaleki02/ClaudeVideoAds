// Bundle the capture entries against the Clipzing frontend (the real components, not copies).
//   node build.mjs            (CLIPZING_FE defaults to ~/shorten/shortn-fe)
import fs from 'fs'
import os from 'os'
import path from 'path'
import { execFileSync } from 'child_process'
import { fileURLToPath } from 'url'

const HERE = path.dirname(fileURLToPath(import.meta.url))
export const FE = process.env.CLIPZING_FE || path.join(os.homedir(), 'shorten', 'shortn-fe')
if (!fs.existsSync(path.join(FE, 'components/mascot/Zing.tsx'))) {
  console.error(`Clipzing frontend not found at ${FE}. Set CLIPZING_FE to the shortn-fe folder.`); process.exit(2)
}
const { build } = await import(path.join(FE, 'node_modules/esbuild/lib/main.js'))
const entries = fs.readdirSync(path.join(HERE, 'src')).filter((f) => f.endsWith('.tsx')).map((f) => path.join(HERE, 'src', f))
await build({
  entryPoints: entries, bundle: true, outdir: path.join(HERE, 'dist'), format: 'iife', platform: 'browser', target: 'es2020',
  jsx: 'automatic', tsconfig: path.join(FE, 'tsconfig.json'), nodePaths: [path.join(FE, 'node_modules')],
  external: ['/caption-engine/*', '/icon.svg'], loader: { '.woff2': 'file', '.svg': 'dataurl', '.png': 'dataurl' },
  assetNames: '[name]', alias: { '@': FE }, define: { 'process.env.NODE_ENV': '"production"' }, logLevel: 'warning',
})
// Tailwind with the product's own config, scanning the components the entries render
const cfg = path.join(HERE, 'dist', 'tw.config.cjs')
fs.writeFileSync(cfg, `const base = require(${JSON.stringify(path.join(FE, 'tailwind.config.js'))});
module.exports = { ...base, content: [${JSON.stringify(path.join(FE, 'components/**/*.tsx'))}, ${JSON.stringify(path.join(HERE, 'src/*.tsx'))}] };`)
fs.writeFileSync(path.join(HERE, 'dist', 'tw.in.css'), '@tailwind base;\n@tailwind components;\n@tailwind utilities;\n')
execFileSync(path.join(FE, 'node_modules/.bin/tailwindcss'), ['-c', cfg, '-i', path.join(HERE, 'dist', 'tw.in.css'), '-o', path.join(HERE, 'dist', 'tw.css'), '--minify'], { stdio: 'ignore' })
console.log('built', entries.map((e) => path.basename(e, '.tsx')).join(', '))
