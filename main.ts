import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(process.env.MAKEFUN_OUTPUT_DIR ?? '.');
mkdirSync(outputDir, { recursive: true });
copyFileSync(join(here, 'entry.png'), join(outputDir, 'entry.png'));
