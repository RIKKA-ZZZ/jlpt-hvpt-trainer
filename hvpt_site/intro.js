const savedTheme = localStorage.getItem("hvpt_theme");
if (savedTheme) document.documentElement.dataset.theme = savedTheme;

const LANG_KEY = "hvpt_lang";
const DATA_VERSION = "20260705-cdn";

function assetUrl(path, options) {
  return window.hvptAssetUrl ? window.hvptAssetUrl(path, options) : path;
}

function setAssetImage(image, path) {
  const primary = assetUrl(path);
  const fallback = assetUrl(path, { cdn: false });
  let triedFallback = false;
  image.decoding = "async";
  image.addEventListener("error", () => {
    if (!triedFallback && primary !== fallback) {
      triedFallback = true;
      image.src = fallback;
    }
  });
  image.src = primary;
}

async function loadDataJson(path) {
  const primary = assetUrl(path, { version: DATA_VERSION });
  const fallback = assetUrl(path, { cdn: false, version: DATA_VERSION });
  try {
    const response = await fetch(primary);
    if (response.ok) return response.json();
    throw new Error(`${path} ${response.status}`);
  } catch (error) {
    if (primary === fallback) throw error;
    const response = await fetch(fallback);
    if (!response.ok) throw new Error(`${path} ${response.status}`);
    return response.json();
  }
}

const STRINGS = {
  zh: {
    pageTitle: "JLPT HVPT Trainer",
    navSources: "来源与许可",
    navTrainer: "进入训练",
    heroEyebrow: "多声源音频 · AI 图像 · JLPT N5-N1",
    heroTitle: "用图片联想和多角色声音训练 JLPT 词汇",
    heroLede: "用 4 种 VOICEVOX 角色音色和 AI 生成图片练习 JLPT N5-N1 词汇。多声源输入帮助你在不同音色之间建立稳健的语音感知；图片联想模式和听音辨词模式搭配，每次选择后立即反馈，适合碎片时间高效刷词。",
    startTraining: "开始训练",
    viewSources: "查看来源与许可",
    imageQuestions: "图片题",
    listeningQuestions: "听音题",
    levels: "等级",
    methodEyebrow: "Method",
    methodTitle: "训练重点",
    featureOneTitle: "多样输入",
    featureOneText: "同一批词会以图片、文字和日语朗读出现，降低只靠单一记忆线索造成的混淆。",
    featureTwoTitle: "即时反馈",
    featureTwoText: "每次选择后马上显示正确答案，帮助你在刚听完、刚看完时修正判断。",
    featureThreeTitle: "可继续扩展",
    featureThreeText: "已覆盖 N5 / N4 / N3 / N2 / N1，使用 4 种 VOICEVOX 角色音色与 AI 生成图片，后续可继续扩充音色和题目类型。",
    licenseEyebrow: "Open and careful",
    licenseTitle: "来源与许可已经单独整理",
    licenseText: "词表、JMdict/EDICT 释义、Tatoeba 例句、AI 生成图片和 VOICEVOX 合成音频分别标注来源。这个项目不是 JLPT 官方项目，也不包含官方真题。",
    fullInfo: "完整说明",
    footerNote: "非官方 JLPT 学习项目。",
    footerSource: "来源与许可",
  },
  en: {
    pageTitle: "JLPT HVPT Trainer",
    navSources: "Sources & licenses",
    navTrainer: "Start training",
    heroEyebrow: "Multi-speaker audio · AI images · JLPT N5-N1",
    heroTitle: "Train JLPT vocabulary with images and multiple voices",
    heroLede: "Practice JLPT N5-N1 vocabulary with four VOICEVOX character voices and AI-generated images. Multi-speaker input helps build more stable listening perception across different voices, while image association and audio recognition modes give immediate feedback after every answer.",
    startTraining: "Start training",
    viewSources: "View sources & licenses",
    imageQuestions: "Image items",
    listeningQuestions: "Audio items",
    levels: "Levels",
    methodEyebrow: "Method",
    methodTitle: "Training Focus",
    featureOneTitle: "Varied input",
    featureOneText: "The same vocabulary appears through images, text, and Japanese audio, reducing confusion caused by relying on only one memory cue.",
    featureTwoTitle: "Immediate feedback",
    featureTwoText: "The correct answer appears right after each choice, so you can adjust your judgment while the sound or image is still fresh.",
    featureThreeTitle: "Ready to grow",
    featureThreeText: "The site already covers N5 / N4 / N3 / N2 / N1 with four VOICEVOX character voices and AI-generated images, and can keep expanding with more voices and exercise types.",
    licenseEyebrow: "Open and careful",
    licenseTitle: "Sources and licenses are organized separately",
    licenseText: "Vocabulary lists, JMdict/EDICT-derived meanings, Tatoeba example sentences, AI-generated images, and VOICEVOX audio are documented separately. This is not an official JLPT project and does not include official test questions.",
    fullInfo: "Full details",
    footerNote: "Unofficial JLPT learning project.",
    footerSource: "Sources & licenses",
  },
  ja: {
    pageTitle: "JLPT HVPT Trainer",
    navSources: "出典・ライセンス",
    navTrainer: "トレーニングへ",
    heroEyebrow: "複数話者の音声 · AI 画像 · JLPT N5-N1",
    heroTitle: "画像と複数音声で JLPT 語彙をすぐ練習",
    heroLede: "4 種類の VOICEVOX キャラクター音声と AI 生成画像で、JLPT N5-N1 の語彙を練習できます。複数の声で聞くことで音声知覚を安定させ、画像連想モードと聞き取りモードを組み合わせて、回答ごとにすぐフィードバックを確認できます。",
    startTraining: "練習を始める",
    viewSources: "出典・ライセンスを見る",
    imageQuestions: "画像問題",
    listeningQuestions: "聴解問題",
    levels: "レベル",
    methodEyebrow: "Method",
    methodTitle: "練習のポイント",
    featureOneTitle: "多様な入力",
    featureOneText: "同じ語彙を画像・文字・日本語音声で確認し、単一の記憶手がかりだけに頼る混乱を減らします。",
    featureTwoTitle: "即時フィードバック",
    featureTwoText: "選択後すぐに正解を表示するため、聞いた直後・見た直後の判断をその場で修正できます。",
    featureThreeTitle: "拡張しやすい構成",
    featureThreeText: "N5 / N4 / N3 / N2 / N1 に対応し、4 種類の VOICEVOX キャラクター音声と AI 生成画像を使用しています。今後も音声や問題形式を追加できます。",
    licenseEyebrow: "Open and careful",
    licenseTitle: "出典とライセンスを整理済み",
    licenseText: "語彙リスト、JMdict/EDICT 由来の意味、Tatoeba の例文、AI 生成画像、VOICEVOX 合成音声について、それぞれ出典を記載しています。このプロジェクトは JLPT 公式ではなく、公式問題も含みません。",
    fullInfo: "詳細を見る",
    footerNote: "非公式 JLPT 学習サイト。",
    footerSource: "出典・ライセンス",
  },
};

const orbit = document.querySelector("#introImageOrbit");
const imageCount = document.querySelector("#introImageCount");
const listeningCount = document.querySelector("#introListeningCount");
const levelCount = document.querySelector("#introLevelCount");
const langSelect = document.querySelector("#introLangSelect");
let topTileZ = 20;
let currentLang = normalizeLang(localStorage.getItem(LANG_KEY));
let introStats = null;

function normalizeLang(lang) {
  return ["zh", "en", "ja"].includes(lang) ? lang : "zh";
}

function localeForLang() {
  if (currentLang === "ja") return "ja-JP";
  if (currentLang === "en") return "en-US";
  return "zh-CN";
}

function applyLang(lang) {
  currentLang = normalizeLang(lang);
  const strings = STRINGS[currentLang] || STRINGS.zh;
  try { localStorage.setItem(LANG_KEY, currentLang); } catch {}
  document.documentElement.lang = currentLang === "ja" ? "ja" : currentLang === "en" ? "en" : "zh-CN";
  document.title = strings.pageTitle;
  if (langSelect) langSelect.value = currentLang;

  for (const el of document.querySelectorAll("[data-i18n]")) {
    const key = el.dataset.i18n;
    if (strings[key] !== undefined) el.textContent = strings[key];
  }
  for (const el of document.querySelectorAll("[data-i18n-html]")) {
    const key = el.dataset.i18nHtml;
    if (strings[key] !== undefined) el.innerHTML = strings[key];
  }
  renderIntroStats();
}

function sample(items, count) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, count);
}

async function loadIntroImages() {
  if (!orbit) {
    return;
  }
  try {
    const payload = await loadDataJson("data/image-lessons.json");
    const lessons = sample(payload.lessons || [], 10);
    orbit.innerHTML = "";

    lessons.forEach((lesson, index) => {
      const tile = document.createElement("div");
      tile.className = "intro-image-tile";
      tile.style.setProperty("--tile-delay", `${index * -0.65}s`);
      tile.style.zIndex = String(index + 1);

      const card = document.createElement("div");
      card.className = "intro-image-card";

      const image = document.createElement("img");
      setAssetImage(image, lesson.image);
      image.alt = "";
      image.loading = "eager";

      const label = document.createElement("span");
      label.textContent = lesson.word;

      card.append(image, label);
      tile.append(card);
      enableTileDrag(tile);
      enableTileHover(tile);
      orbit.append(tile);
    });
  } catch {
    orbit.classList.add("is-empty");
  }
}

function formatCount(value) {
  return new Intl.NumberFormat(localeForLang()).format(value);
}

function sortedLevels(lessons) {
  return [...new Set(lessons.map((lesson) => lesson.level).filter(Boolean))]
    .sort((a, b) => Number(b.slice(1)) - Number(a.slice(1)));
}

async function loadIntroStats() {
  if (!imageCount || !listeningCount || !levelCount) {
    return;
  }

  try {
    const [imagePayload, listeningPayload] = await Promise.all([
      loadDataJson("data/image-lessons.json"),
      loadDataJson("data/listening-lessons.json"),
    ]);
    const imageLessons = imagePayload.lessons || [];
    const listeningLessons = listeningPayload.lessons || [];
    introStats = {
      imageCount: imageLessons.length,
      listeningCount: listeningLessons.length,
      levels: sortedLevels([...imageLessons, ...listeningLessons]),
    };
    renderIntroStats();
  } catch {
    imageCount.textContent = "-";
    listeningCount.textContent = "-";
    levelCount.textContent = "-";
  }
}

function renderIntroStats() {
  if (!introStats || !imageCount || !listeningCount || !levelCount) {
    return;
  }
  imageCount.textContent = formatCount(introStats.imageCount);
  listeningCount.textContent = formatCount(introStats.listeningCount);
  if (introStats.levels.length) {
    levelCount.innerHTML = "";
    for (const level of introStats.levels) {
      const badge = document.createElement("span");
      badge.className = "intro-level-badge";
      badge.textContent = level;
      levelCount.append(badge);
    }
  } else {
    levelCount.textContent = "-";
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function pinTileToCurrentPosition(tile) {
  const orbitBox = orbit.getBoundingClientRect();
  const tileBox = tile.getBoundingClientRect();
  tile.style.left = `${tileBox.left - orbitBox.left}px`;
  tile.style.top = `${tileBox.top - orbitBox.top}px`;
  tile.style.right = "auto";
  tile.style.bottom = "auto";
}

function enableTileHover(tile) {
  const card = tile.querySelector(".intro-image-card");

  tile.addEventListener("mousemove", (e) => {
    if (tile.classList.contains("is-dragging")) return;
    const rect = tile.getBoundingClientRect();
    const dx = (e.clientX - rect.left - rect.width / 2) / (rect.width / 2);
    const dy = (e.clientY - rect.top  - rect.height / 2) / (rect.height / 2);
    tile.style.transition = "transform 0.08s ease";
    tile.style.transform = `perspective(560px) rotateY(${dx * 18}deg) rotateX(${-dy * 18}deg) scale(1.13)`;
    tile.style.zIndex = String(topTileZ + 1);
    if (card) {
      card.style.boxShadow = "0 28px 56px rgba(73, 90, 76, 0.32), 0 0 0 1px rgba(255,255,255,0.08)";
      card.style.filter = "brightness(1.06) saturate(1.12)";
    }
  });

  tile.addEventListener("mouseleave", () => {
    if (tile.classList.contains("is-dragging")) return;
    tile.style.transition = "transform 0.55s cubic-bezier(0.23, 1, 0.32, 1)";
    tile.style.transform = "";
    if (card) {
      card.style.boxShadow = "";
      card.style.filter = "";
    }
  });
}

function enableTileDrag(tile) {
  let startX = 0;
  let startY = 0;
  let originLeft = 0;
  let originTop = 0;

  tile.addEventListener("pointerdown", (event) => {
    if (!orbit) {
      return;
    }
    pinTileToCurrentPosition(tile);
    const orbitBox = orbit.getBoundingClientRect();
    const tileBox = tile.getBoundingClientRect();

    startX = event.clientX;
    startY = event.clientY;
    originLeft = tileBox.left - orbitBox.left;
    originTop = tileBox.top - orbitBox.top;

    tile.classList.add("is-dragging");
    tile.style.zIndex = String(++topTileZ);
    tile.setPointerCapture(event.pointerId);
  });

  tile.addEventListener("pointermove", (event) => {
    if (!tile.classList.contains("is-dragging")) {
      return;
    }
    const orbitBox = orbit.getBoundingClientRect();
    const tileBox = tile.getBoundingClientRect();
    const nextLeft = originLeft + event.clientX - startX;
    const nextTop = originTop + event.clientY - startY;

    tile.style.left = `${clamp(nextLeft, 0, orbitBox.width - tileBox.width)}px`;
    tile.style.top = `${clamp(nextTop, 0, orbitBox.height - tileBox.height)}px`;
  });

  function endDrag(event) {
    if (!tile.classList.contains("is-dragging")) {
      return;
    }
    tile.classList.remove("is-dragging");
    if (tile.hasPointerCapture(event.pointerId)) {
      tile.releasePointerCapture(event.pointerId);
    }
  }

  tile.addEventListener("pointerup", endDrag);
  tile.addEventListener("pointercancel", endDrag);
}

if (langSelect) {
  langSelect.addEventListener("change", () => applyLang(langSelect.value));
}

applyLang(currentLang);
loadIntroStats();
loadIntroImages();
