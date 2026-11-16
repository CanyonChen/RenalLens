const assert = require('node:assert/strict');
const {test} = require('node:test');
let math;
try { math = require('../scripts/views/explorer-math.js'); } catch { math = {}; }

test('ties receive average ranks in Spearman correlations', () => {
  assert.equal(typeof math.correlation, 'function', 'Implement explorer correlations');
  const points = [[1,10],[2,10],[3,30],[4,40]];
  assert.ok(Math.abs(math.correlation(points,'spearman')-0.9486832980505138)<1e-12);
  assert.equal(math.correlation([[1,2],[1,3]],'pearson'),null);
});
test('eligibility uses required fields and leaves source measurements intact', () => {
  assert.equal(typeof math.retained, 'function', 'Implement explorer eligibility');
  const p={missing:['rbc'],observed:{sc:1,bgr:204},imputed:{sc:1,bgr:204}};
  assert.equal(math.retained(p,'all24',['sc','bgr'],['sc']),false);
  assert.equal(math.retained(p,'core5',['sc','bgr'],['sc']),true);
  assert.equal(math.retained(p,'current',['sc','bgr'],['rbc']),false);
  assert.equal(p.observed.bgr,204);
});
test('quartiles use linear interpolation and account for every reading',()=>{
  assert.equal(typeof math.quantile,'function','Implement distribution summaries');
  assert.equal(math.quantile([1,2,3,4],.25),1.75);
  assert.equal(math.quantile([1,2,3,4],.5),2.5);
  assert.equal(math.quantile([],.5),null);
});
