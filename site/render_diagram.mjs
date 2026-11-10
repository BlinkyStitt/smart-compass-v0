// Build-only SVG rendering. The page receives a bounded bitmap, never the CAD mesh.
import {readFileSync} from 'node:fs';
import {Resvg} from '@resvg/resvg-js';

const svg = readFileSync(0);
const image = new Resvg(svg, {fitTo: {mode: 'width', value: 1600}}).render();
process.stdout.write(image.asPng());
