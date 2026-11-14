const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const V={ s1:['a','t=750,160,-150&dir=0.28,0.36,1&d=2050&fov=26'],
 s2:['a','t=1125,135,15&dir=-0.3,0.35,1&d=460&fov=28'],
 s3:['o','t=1125,135,25&dir=-0.3,0.4,1&d=520&fov=28'],
 s4:['r','t=1165,150,20&dir=0.4,0.45,1&d=340&fov=28'],
 s5:['a','t=1150,125,8&dir=0.2,0.3,1&d=400&fov=28&hide=REMEN,KARETKA'],
 s6:['a','t=1340,150,25&dir=0.45,0.35,1&d=210&fov=28'],
 s7:['r','t=1172,150,18&dir=0.04,1,0.3&d=300&fov=28'],
 s8:['a','t=600,172,25&dir=0.35,0.45,1&d=230&fov=28'] };
const views=(process.argv[2]||Object.keys(V).join(',')).split(','), dsf=+(process.argv[3]||1);
for(const v of views){const [m,q]=V[v]; const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:dsf}); p.on('pageerror',e=>console.log('ERR',e.message));
await p.goto('http://localhost:8765/stand/r.html?m='+(m.endsWith('.glb')?m:'m7_'+m+'.glb')+'&'+q); await p.waitForFunction('window.__done===true',null,{timeout:400000});
await p.screenshot({path:`/home/claude/stand/out/w7_${v}.png`,timeout:400000}); console.log('ok',v); await p.close();}
await b.close();})();
