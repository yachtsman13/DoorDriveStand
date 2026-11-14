const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--ignore-gpu-blocklist',
    ],
  });
  const outDir = path.resolve(__dirname, '..', 'out');
  fs.mkdirSync(outDir, { recursive: true });
  const views = {
    p1: ['pa', 't=0,0,15&dir=0.55,0.35,1&d=175&fov=28'],
    p2: ['pa', 't=0,0,8&dir=0.55,0.5,-0.9&d=175&fov=28'],
    p3: ['px', 't=0,0,28&dir=0.75,0.45,1&d=215&fov=28'],
    p4: ['pa', 't=0,20,22&dir=0.12,1,0.45&d=105&fov=28'],
  };
  const selected = (process.argv[2] || Object.keys(views).join(',')).split(',');
  const deviceScaleFactor = +(process.argv[3] || 1);

  for (const view of selected) {
    const [model, query] = views[view];
    const page = await browser.newPage({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor,
    });
    page.on('pageerror', error => console.log('ERR', error.message));
    const modelPath = model.endsWith('.glb') ? model : `../out/m7_${model}.glb`;
    await page.goto(
      'http://localhost:8765/src/r.html?m=' + encodeURIComponent(modelPath) + '&' + query,
    );
    await page.waitForFunction('window.__done===true', null, { timeout: 400000 });
    await page.screenshot({
      path: path.join(outDir, `w7_${view}.png`),
      timeout: 400000,
    });
    console.log('ok', view);
    await page.close();
  }
  await browser.close();
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
