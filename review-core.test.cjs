'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { metadataFor, validateDocument, escapeHtml, toPlainText, findOverlap } = require('./review-core.js');

const META = metadataFor('version-b', 'yushi-b-2026-10-09');
const blocks = [
  { id: 'hero-title', text: '先看清你卡在哪。', label: '第一屏標題' },
  { id: 'faq-1', text: '這是一場推銷嗎？', label: '常見問題' }
];
function comment(overrides = {}) {
  return {
    id: 'edit-1', blockId: 'hero-title', start: 0, end: 3,
    original: '先看清', replacement: '先弄清', note: '',
    updatedAt: '2026-10-09T10:00:00.000Z', ...overrides
  };
}
function document(comments = [comment()], overrides = {}) {
  return { ...META, comments, ...overrides };
}

test('metadata 需要頁面與版本', () => {
  assert.deepEqual(META, { schema: 'yushi-copy-review', version: 1, page: 'version-b', revision: 'yushi-b-2026-10-09' });
  assert.throws(() => metadataFor('', 'r'), /不完整/);
  assert.throws(() => metadataFor('version-a'), /不完整/);
});

test('接受有效與空修改單，僅輸出白名單欄位且不修改輸入', () => {
  const input = document([comment({ previewLabel: '供預覽使用' })]);
  const before = JSON.stringify(input);
  assert.deepEqual(validateDocument(input, blocks, META), [comment()]);
  assert.equal(JSON.stringify(input), before);
  assert.deepEqual(validateDocument(document([]), blocks, META), []);
});

test('拒絕非整數、非數字、超界與空範圍', () => {
  for (const range of [
    { start: -1 }, { start: '0' }, { start: 0.5 }, { end: Infinity },
    { end: '3' }, { end: 99 }, { end: 0 }, { start: 3, end: 2 }
  ]) {
    assert.throws(() => validateDocument(document([comment(range)]), blocks, META), /文字範圍/);
  }
});

test('拒絕重複識別碼與同區塊重疊範圍', () => {
  assert.throws(() => validateDocument(document([comment(), comment()]), blocks, META), /識別碼/);
  const overlapping = comment({ id: 'edit-2', start: 2, end: 5, original: '清你卡' });
  assert.throws(() => validateDocument(document([comment(), overlapping]), blocks, META), /重疊/);
});

test('相鄰範圍與不同區塊的同一位置可並存', () => {
  const adjacent = comment({ id: 'edit-2', start: 3, end: 5, original: '你卡' });
  const anotherBlock = comment({ id: 'edit-3', blockId: 'faq-1', original: '這是一' });
  const comments = [comment(), adjacent, anotherBlock];
  assert.deepEqual(validateDocument(document(comments), blocks, META), comments);
});

test('拒絕與頁面不符的原文，以及別一版或別一次改稿的修改單', () => {
  assert.throws(() => validateDocument(document([comment({ original: '原本標題' })]), blocks, META), /原文與目前頁面不符/);
  for (const override of [
    { revision: 'older-revision' }, { page: 'version-a' },
    { version: '1' }, { schema: 'vstory-copy-review' }
  ]) {
    assert.throws(() => validateDocument(document([comment()], override), blocks, META), /版本不符/);
  }
  const metaA = metadataFor('version-a', 'yushi-a-2026-10-09');
  assert.throws(() => validateDocument(document([comment()]), blocks, metaA), /版本不符/);
});

test('拒絕空白文案、過長文字、缺少區塊與無效更新時間', () => {
  for (const field of ['original', 'replacement']) {
    assert.throws(() => validateDocument(document([comment({ [field]: '  ' })]), blocks, META), /不可空白/);
  }
  for (const field of ['original', 'replacement', 'note']) {
    assert.throws(() => validateDocument(document([comment({ [field]: '文'.repeat(5001) })]), blocks, META), /5000/);
    assert.throws(() => validateDocument(document([comment({ [field]: 12 })]), blocks, META), /必須是文字/);
  }
  assert.throws(() => validateDocument(document([comment({ blockId: 'missing' })]), blocks, META), /區塊不存在/);
  assert.throws(() => validateDocument(document([comment({ updatedAt: '日期待確認' })]), blocks, META), /更新時間/);
  assert.throws(() => validateDocument(document(Array.from({ length: 201 }, () => comment())), blocks, META), /200/);
});

test('尋找第一個重疊項目，並支援排除自己', () => {
  const first = comment();
  const second = comment({ id: 'edit-2', start: 4, end: 7, original: '卡在哪' });
  const comments = [first, second];
  assert.equal(findOverlap(comments, 'hero-title', 2, 5), first);
  assert.equal(findOverlap(comments, 'hero-title', 2, 5, first.id), second);
  assert.equal(findOverlap(comments, 'hero-title', 3, 4), null);
  assert.equal(findOverlap(comments, 'faq-1', 0, 3), null);
});

test('HTML 轉義保留繁中文意並處理一般文字符號', () => {
  assert.equal(escapeHtml('申論 & 計畫 <分數> "上榜" \'節奏\''),
    '申論 &amp; 計畫 &lt;分數&gt; &quot;上榜&quot; &#39;節奏&#39;');
  assert.equal(escapeHtml('把內容寫成分數'), '把內容寫成分數');
});

test('純文字修改單包括頁面名稱、區塊、原文、改為與補充說明', () => {
  assert.equal(toPlainText([comment({ note: '語氣再直接一點。' })], blocks, '羽試 B版'),
    '羽試 B版｜文案修改單\n共 1 筆修改\n\n【1】第一屏標題\n原文：\n先看清\n改為：\n先弄清\n補充說明：\n語氣再直接一點。\n');
  assert.equal(toPlainText([], blocks, '羽試 B版'), '羽試 B版｜文案修改單\n共 0 筆修改\n');
});
