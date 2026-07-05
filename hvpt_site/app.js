const state = {
  imageLessons: [],
  listeningLessons: [],
  filtered: [],
  current: null,
  choices: [],
  answered: false,
  mode: "image",
  stats: {
    answered: 0,
    correct: 0,
    streak: 0,
    bestStreak: 0,
  },
  history: [],
  autoAdvance: false,
  autoAdvanceTimer: null,
  wrongWords: [],
  wrongCounts: {},
  lang: "zh",
  wrongWordsOnly: false,
  audioVoice: "random",
  currentAudioKey: "",
};

const AUDIO_VOICES = [
  { key: "random", zh: "随机角色", en: "Random voice", ja: "ランダム音声" },
  { key: "voicevox_2", zh: "四国めたん", en: "Shikoku Metan", ja: "四国めたん", credit: "VOICEVOX:四国めたん" },
  { key: "voicevox_16", zh: "九州そら", en: "Kyushu Sora", ja: "九州そら", credit: "VOICEVOX:九州そら" },
  { key: "voicevox_11", zh: "玄野武宏", en: "Kurono Takehiro", ja: "玄野武宏", credit: "VOICEVOX:玄野武宏(CV:ガロ)" },
  { key: "voicevox_3", zh: "ずんだもん", en: "Zundamon", ja: "ずんだもん", credit: "VOICEVOX:ずんだもん" },
];

const STRINGS = {
  zh: {
    title: "日语听辨与词汇联想训练",
    modeSection: "模式", modeImage: "看词选图", modeAudio: "听音选词", modeAudioW: "听音写词", modeMeaningW: "看义写词",
    filterSection: "筛选", filterLevel: "等级", filterDomain: "类别", filterKana: "写法",
    filterAll: "全部", filterHiragana: "平假名", filterKatakana: "片假名", filterKanjiMixed: "汉字/混合",
    statsSection: "本轮", statsAccuracy: "正确率", statsStreak: "连对", statsAnswered: "已答", statsBestStreak: "最佳连对",
    sourceSection: "来源", sourceMaterial: "素材", sourceLicense: "许可", sourceCreator: "作者/工具",
    sourcePageLink: "来源页面", sourceFullLink: "完整来源与许可",
    imageShelf: "素材角落", historySection: "最近", wrongWordsSection: "本轮错词", wrongWordsEmpty: "暂无",
    btnDark: "暗色", btnLight: "亮色", btnAuto: "自动", btnSpeak: "播放", btnNext: "下一题", btnConfirm: "确认",
    btnSummary: "总结", btnResetRound: "重置本轮", btnCloseSum: "继续",
    btnReviewWrong: "专练错词", btnReviewWrongOff: "返回全部",
    summaryTitle: "本轮总结", summaryWrongCount: "本轮错词", summaryNoneWrong: "太棒了，全部答对！",
    kbdSelect: "选择", kbdNext: "下一题", kbdListen: "重听",
    footerNote: "非官方 JLPT 学习项目。", footerSource: "来源与许可",
    promptAudio: "听音选单词", promptAudioW: "听音写词",
    writePlaceholder: "输入日语单词或读法…",
    answerCorrect: "正确：", answerWrong: "答案：",
    sentenceLabel: "例句",
    historyCorrect: "正确", historyRetry: "重练",
    emptyState: "没有题目", loadError: "数据读取失败",
    voiceSelect: "音频角色",
    sourceBrowser: "浏览器日语朗读", sourceVoicevox: "VOICEVOX 本地音频", sourceVoicevoxLicense: "VOICEVOX 软件规约与各角色音源规约；详见完整来源页", sourceLocal: "本地练习数据", sourceLocalImage: "本地图片", sourceVocab: "Tanos JLPT vocabulary",
    domains: {
      action_state: "动作", animal: "动物", body_health: "身体", clothing: "服饰",
      color_shape: "颜色", food_drink: "饮食", nature_weather: "自然", object_tool: "物品",
      person_family: "人物", place_building: "地点", transport: "交通", vocabulary: "词汇",
    },
  },
  en: {
    title: "JLPT Vocabulary Trainer",
    modeSection: "Mode", modeImage: "Word → Image", modeAudio: "Audio → Word", modeAudioW: "Audio → Type", modeMeaningW: "Meaning → Type",
    filterSection: "Filter", filterLevel: "Level", filterDomain: "Category", filterKana: "Script",
    filterAll: "All", filterHiragana: "Hiragana", filterKatakana: "Katakana", filterKanjiMixed: "Kanji / Mixed",
    statsSection: "This round", statsAccuracy: "Accuracy", statsStreak: "Streak", statsAnswered: "Answered", statsBestStreak: "Best streak",
    sourceSection: "Source", sourceMaterial: "Material", sourceLicense: "License", sourceCreator: "Author / Tool",
    sourcePageLink: "Source page", sourceFullLink: "Full sources & licenses",
    imageShelf: "Image shelf", historySection: "Recent", wrongWordsSection: "Mistakes", wrongWordsEmpty: "None yet",
    btnDark: "Dark", btnLight: "Light", btnAuto: "Auto", btnSpeak: "Play", btnNext: "Next", btnConfirm: "Submit",
    btnSummary: "Summary", btnResetRound: "Reset round", btnCloseSum: "Continue",
    btnReviewWrong: "Review mistakes", btnReviewWrongOff: "All words",
    summaryTitle: "Round summary", summaryWrongCount: "Mistakes", summaryNoneWrong: "Perfect round!",
    kbdSelect: "select", kbdNext: "next", kbdListen: "replay",
    footerNote: "Unofficial JLPT learning project.", footerSource: "Sources & licenses",
    promptAudio: "Listen and pick", promptAudioW: "Type what you hear",
    writePlaceholder: "Type the Japanese word or reading…",
    answerCorrect: "Correct: ", answerWrong: "Answer: ",
    sentenceLabel: "Example",
    historyCorrect: "correct", historyRetry: "retry",
    emptyState: "No items", loadError: "Failed to load data",
    voiceSelect: "Audio voice",
    sourceBrowser: "Browser speech synthesis", sourceVoicevox: "Local VOICEVOX audio", sourceVoicevoxLicense: "VOICEVOX software terms and each character voice-library terms; see full sources", sourceLocal: "Local training data", sourceLocalImage: "Local image", sourceVocab: "Tanos JLPT vocabulary",
    domains: {
      action_state: "Actions", animal: "Animals", body_health: "Body & Health", clothing: "Clothing",
      color_shape: "Colors & Shapes", food_drink: "Food & Drink", nature_weather: "Nature", object_tool: "Objects",
      person_family: "People & Family", place_building: "Places", transport: "Transport", vocabulary: "Vocabulary",
    },
  },
  ja: {
    title: "JLPT 単語トレーナー",
    modeSection: "モード", modeImage: "単語→画像", modeAudio: "聴解→選択", modeAudioW: "聴解→記入", modeMeaningW: "意味→記入",
    filterSection: "絞り込み", filterLevel: "レベル", filterDomain: "カテゴリ", filterKana: "文字種",
    filterAll: "すべて", filterHiragana: "ひらがな", filterKatakana: "カタカナ", filterKanjiMixed: "漢字・混合",
    statsSection: "今回", statsAccuracy: "正解率", statsStreak: "連続正解", statsAnswered: "回答数", statsBestStreak: "最長連続",
    sourceSection: "出典", sourceMaterial: "素材", sourceLicense: "ライセンス", sourceCreator: "作者・ツール",
    sourcePageLink: "出典ページ", sourceFullLink: "出典・ライセンス一覧",
    imageShelf: "画像コーナー", historySection: "履歴", wrongWordsSection: "ミスした単語", wrongWordsEmpty: "なし",
    btnDark: "ダーク", btnLight: "ライト", btnAuto: "自動", btnSpeak: "再生", btnNext: "次へ", btnConfirm: "確認",
    btnSummary: "集計", btnResetRound: "リセット", btnCloseSum: "続ける",
    btnReviewWrong: "ミスのみ", btnReviewWrongOff: "全体に戻る",
    summaryTitle: "ラウンド集計", summaryWrongCount: "ミス", summaryNoneWrong: "全問正解！",
    kbdSelect: "選択", kbdNext: "次へ", kbdListen: "再生",
    footerNote: "非公式 JLPT 学習サイト。", footerSource: "出典・ライセンス",
    promptAudio: "聴いて選ぶ", promptAudioW: "聴いて書く",
    writePlaceholder: "日本語の単語または読み方を入力…",
    answerCorrect: "正解：", answerWrong: "答え：",
    sentenceLabel: "例文",
    historyCorrect: "正解", historyRetry: "再挑戦",
    emptyState: "問題なし", loadError: "データ読み込み失敗",
    voiceSelect: "音声キャラクター",
    sourceBrowser: "ブラウザ音声合成", sourceVoicevox: "VOICEVOX ローカル音声", sourceVoicevoxLicense: "VOICEVOXソフトウェア規約と各キャラクター音源規約。詳細は出典ページへ", sourceLocal: "ローカル練習データ", sourceLocalImage: "ローカル画像", sourceVocab: "Tanos JLPT 語彙",
    domains: {
      action_state: "動作・状態", animal: "動物", body_health: "体・健康", clothing: "衣服",
      color_shape: "色・形", food_drink: "食べ物・飲み物", nature_weather: "自然・天気", object_tool: "物・道具",
      person_family: "人・家族", place_building: "場所・建物", transport: "交通", vocabulary: "語彙",
    },
  },
};

const els = {
  speakButton: document.querySelector("#speakButton"),
  nextButton: document.querySelector("#nextButton"),
  levelFilter: document.querySelector("#levelFilter"),
  domainFilter: document.querySelector("#domainFilter"),
  kanaFilter: document.querySelector("#kanaFilter"),
  choices: document.querySelector("#choices"),
  wordText: document.querySelector("#wordText"),
  readingText: document.querySelector("#readingText"),
  answerLine: document.querySelector("#answerLine"),
  sentenceLine: document.querySelector("#sentenceLine"),
  levelBadge: document.querySelector("#levelBadge"),
  domainBadge: document.querySelector("#domainBadge"),
  accuracyText: document.querySelector("#accuracyText"),
  streakText: document.querySelector("#streakText"),
  answeredText: document.querySelector("#answeredText"),
  historyList: document.querySelector("#historyList"),
  sourceProvider: document.querySelector("#sourceProvider"),
  licenseText: document.querySelector("#licenseText"),
  creatorText: document.querySelector("#creatorText"),
  sourceLink: document.querySelector("#sourceLink"),
  topGallery: document.querySelector("#topGallery"),
  imageShelf: document.querySelector("#imageShelf"),
  modeButtons: Array.from(document.querySelectorAll("[data-mode]")),
  darkModeButton: document.querySelector("#darkModeButton"),
  darkModeLabel: document.querySelector("#darkModeLabel"),
  autoAdvanceButton: document.querySelector("#autoAdvanceButton"),
  autoBar: document.querySelector("#autoBar"),
  autoBarFill: document.querySelector("#autoBarFill"),
  wrongWordsList: document.querySelector("#wrongWordsList"),
  wrongWordsCount: document.querySelector("#wrongWordsCount"),
  wrongWordsEmpty: document.querySelector("#wrongWordsEmpty"),
  writeForm: document.querySelector("#writeForm"),
  writeInput: document.querySelector("#writeInput"),
  langSelect: document.querySelector("#langSelect"),
  voiceSelect: document.querySelector("#voiceSelect"),
  wrongReviewButton: document.querySelector("#wrongReviewButton"),
  summaryOverlay: document.querySelector("#summaryOverlay"),
  summaryMetrics: document.querySelector("#summaryMetrics"),
  summaryWrong: document.querySelector("#summaryWrong"),
  summaryButton: document.querySelector("#summaryButton"),
  summaryResetButton: document.querySelector("#summaryResetButton"),
  summaryCloseButton: document.querySelector("#summaryCloseButton"),
};

const WRONG_KEY = "hvpt_wrong_counts";
const THEME_KEY = "hvpt_theme";
const SESSION_KEY = "hvpt_session";
const LANG_KEY = "hvpt_lang";
const AUDIO_VOICE_KEY = "hvpt_audio_voice";
const AUDIO_CACHE_LIMIT = 24;
const audioCache = new Map();

function assetUrl(path, options) {
  return window.hvptAssetUrl ? window.hvptAssetUrl(path, options) : path;
}

function audioAssetUrl(path, options) {
  return assetUrl(path, Object.assign({ cdn: false, version: null }, options || {}));
}

function optimizedImagePath(path) {
  if (!path || !/^assets\/images\/.+\.png$/i.test(path)) return path;
  return path.replace(/^assets\/images\//, "assets/images-webp/").replace(/\.png$/i, ".webp");
}

function setAssetImage(image, path) {
  const optimized = optimizedImagePath(path);
  const primary = assetUrl(optimized);
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

function loadWrongCounts() {
  try {
    const raw = localStorage.getItem(WRONG_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveWrongCounts() {
  try {
    localStorage.setItem(WRONG_KEY, JSON.stringify(state.wrongCounts));
  } catch {}
}

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data.date !== new Date().toDateString()) return;
    if (data.stats) state.stats = Object.assign({ bestStreak: 0 }, data.stats);
    if (data.history) state.history = data.history;
    if (data.wrongWords) state.wrongWords = data.wrongWords;
  } catch {}
}

function saveSession() {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
      date: new Date().toDateString(),
      stats: state.stats,
      history: state.history,
      wrongWords: state.wrongWords,
    }));
  } catch {}
}

function weightedPick(items) {
  if (!items.length) return null;
  const weights = items.map((item) => 1 + Math.min((state.wrongCounts[item.id] || 0) * 1.5, 4.5));
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < items.length; i++) {
    r -= weights[i];
    if (r <= 0) return items[i];
  }
  return items[items.length - 1];
}

function voiceLabel(key) {
  const voice = AUDIO_VOICES.find((item) => item.key === key);
  return voice ? voice[state.lang] || voice.zh : key;
}

function voiceCredit(key) {
  const voice = AUDIO_VOICES.find((item) => item.key === key);
  return voice?.credit || "";
}

function renderVoiceSelect() {
  if (!els.voiceSelect) return;
  const selected = state.audioVoice;
  els.voiceSelect.innerHTML = "";
  for (const voice of AUDIO_VOICES) {
    const option = document.createElement("option");
    option.value = voice.key;
    option.textContent = voiceLabel(voice.key);
    els.voiceSelect.append(option);
  }
  els.voiceSelect.value = selected;
  els.voiceSelect.title = t().voiceSelect;
  els.voiceSelect.setAttribute("aria-label", t().voiceSelect);
}

function audioVariantKeys(item) {
  return Object.keys(item?.audioVariants || {}).filter((key) => item.audioVariants[key]);
}

function pickAudioKey(item) {
  const keys = audioVariantKeys(item);
  if (!keys.length) return "";
  if (state.audioVoice !== "random" && keys.includes(state.audioVoice)) {
    return state.audioVoice;
  }
  if (state.audioVoice !== "random") {
    return keys[0];
  }
  return keys[Math.floor(Math.random() * keys.length)];
}

function prepareAudioForQuestion(item) {
  state.currentAudioKey = pickAudioKey(item);
}

function selectedAudioSource(item) {
  if (!item) return "";
  const variants = item.audioVariants || {};
  if (state.currentAudioKey && variants[state.currentAudioKey]) {
    return variants[state.currentAudioKey];
  }
  if (state.audioVoice !== "random" && variants[state.audioVoice]) {
    return variants[state.audioVoice];
  }
  return item.audio || "";
}

function selectedAudioPath(item) {
  const source = selectedAudioSource(item);
  return source ? audioAssetUrl(source) : "";
}

function cachedAudio(sourcePath) {
  if (!sourcePath) return null;
  const url = audioAssetUrl(sourcePath);
  const existing = audioCache.get(url);
  if (existing) {
    audioCache.delete(url);
    audioCache.set(url, existing);
    return existing;
  }

  const audio = new Audio(url);
  audio.preload = "auto";
  audio.load();
  audioCache.set(url, audio);
  while (audioCache.size > AUDIO_CACHE_LIMIT) {
    const oldest = audioCache.keys().next().value;
    audioCache.delete(oldest);
  }
  return audio;
}

function preloadAudioForItem(item) {
  const source = selectedAudioSource(item);
  if (source) cachedAudio(source);
}

function currentAudioLabel(item) {
  if (!selectedAudioPath(item)) return t().sourceBrowser;
  const key = state.currentAudioKey || (state.audioVoice !== "random" ? state.audioVoice : "");
  const label = key ? voiceLabel(key) : "";
  if (state.audioVoice === "random" && label) {
    return `${t().sourceVoicevox} / ${voiceLabel("random")}：${label}`;
  }
  return label ? `${t().sourceVoicevox} / ${label}` : t().sourceVoicevox;
}

function currentAudioCredit(item) {
  if (!selectedAudioPath(item)) return item?.source || t().sourceVocab;
  const key = state.currentAudioKey || (state.audioVoice !== "random" ? state.audioVoice : "");
  return voiceCredit(key) || item?.audioCreator || "VOICEVOX";
}

function applyLang(lang) {
  state.lang = lang;
  try { localStorage.setItem(LANG_KEY, lang); } catch {}
  document.documentElement.lang = lang === "ja" ? "ja" : lang === "en" ? "en" : "zh-CN";
  if (els.langSelect) els.langSelect.value = lang;
  renderVoiceSelect();

  const s = t();
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const key = el.dataset.i18n;
    if (s[key] !== undefined) el.textContent = s[key];
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    const key = el.dataset.i18nPlaceholder;
    if (s[key] !== undefined) el.placeholder = s[key];
  }

  const meaningWBtn = els.modeButtons.find(function(b) { return b.dataset.mode === "meaning-w"; });
  if (meaningWBtn) {
    const hide = lang === "ja";
    meaningWBtn.style.display = hide ? "none" : "";
    if (hide && state.mode === "meaning-w") {
      state.mode = "image";
      els.modeButtons.forEach(function(b) {
        b.classList.toggle("is-active", b.dataset.mode === "image");
      });
      updateFilters();
      showQuestion();
      return;
    }
  }

  updateFilters();
  refreshDisplay();
}

function refreshDisplay() {
  updateDarkModeButton();
  updateHistory();
  updateWrongWords();
  if (!state.current) return;

  if (!state.answered) {
    if (state.mode === "audio") els.wordText.textContent = t().promptAudio;
    else if (state.mode === "audio-w") els.wordText.textContent = t().promptAudioW;
    else if (state.mode === "meaning-w") els.wordText.textContent = meaningText(state.current);
  } else {
    const answer = meaningText(state.current);
    const isWrong = els.answerLine.classList.contains("is-wrong");
    els.answerLine.textContent = isWrong
      ? `${t().answerWrong}${answer}`
      : `${t().answerCorrect}${answer}`;
    showSentence(state.current);
  }
}

function toggleDarkMode() {
  const isDark = document.documentElement.dataset.theme === "dark";
  document.documentElement.dataset.theme = isDark ? "" : "dark";
  localStorage.setItem(THEME_KEY, isDark ? "light" : "dark");
  updateDarkModeButton();
}

function updateDarkModeButton() {
  if (!els.darkModeLabel) return;
  els.darkModeLabel.textContent = document.documentElement.dataset.theme === "dark" ? t().btnLight : t().btnDark;
}

function toggleAutoAdvance() {
  state.autoAdvance = !state.autoAdvance;
  if (els.autoAdvanceButton) {
    els.autoAdvanceButton.classList.toggle("is-active", state.autoAdvance);
  }
  if (!state.autoAdvance) cancelAutoAdvanceTimer();
}

function startAutoAdvanceTimer() {
  if (!state.autoAdvance) return;
  const delay = 2200;
  if (els.autoBar && els.autoBarFill) {
    els.autoBar.style.display = "block";
    els.autoBarFill.style.transition = "none";
    els.autoBarFill.style.width = "100%";
    void els.autoBarFill.offsetWidth;
    els.autoBarFill.style.transition = `width ${delay}ms linear`;
    els.autoBarFill.style.width = "0%";
  }
  state.autoAdvanceTimer = setTimeout(showQuestion, delay);
}

function cancelAutoAdvanceTimer() {
  if (state.autoAdvanceTimer !== null) {
    clearTimeout(state.autoAdvanceTimer);
    state.autoAdvanceTimer = null;
  }
  if (els.autoBar) els.autoBar.style.display = "none";
}

function updateWrongWords() {
  if (!els.wrongWordsList || !els.wrongWordsEmpty || !els.wrongWordsCount) return;
  const count = state.wrongWords.length;
  els.wrongWordsCount.textContent = String(count);
  els.wrongWordsCount.classList.toggle("has-items", count > 0);

  if (els.wrongReviewButton) {
    els.wrongReviewButton.disabled = count === 0 && !state.wrongWordsOnly;
    els.wrongReviewButton.classList.toggle("is-active", state.wrongWordsOnly);
    els.wrongReviewButton.textContent = state.wrongWordsOnly ? t().btnReviewWrongOff : t().btnReviewWrong;
  }

  els.wrongWordsList.innerHTML = "";
  if (!count) {
    els.wrongWordsEmpty.style.display = "";
    return;
  }
  els.wrongWordsEmpty.style.display = "none";
  for (const item of state.wrongWords) {
    const li = document.createElement("li");
    li.className = "history-item-wrong";
    const strong = document.createElement("strong");
    strong.textContent = item.word;
    li.append(strong, document.createTextNode(` ${item.meaning}`));
    els.wrongWordsList.append(li);
  }
}

function toHiragana(str) {
  // NFKC: half-width katakana → full-width (also merges voiced/semi-voiced combining marks)
  const full = str.normalize("NFKC");
  // Full-width katakana ァ–ヶ → hiragana
  return full.replace(/[ァ-ヶ]/g, function(c) {
    return String.fromCharCode(c.charCodeAt(0) - 0x60);
  });
}

function normalizeWord(str) {
  return (str || "").trim().replace(/[・\s　]/g, "");
}

function checkWriteAnswer(input, item) {
  const norm = normalizeWord(input);
  if (!norm) return false;
  const normH = toHiragana(norm);

  const candidates = [item.word, ...(item.reading || "").split("/")]
    .map(normalizeWord)
    .filter(Boolean);

  return candidates.some(function(c) {
    return norm === c || normH === toHiragana(c);
  });
}

function showWriteForm() {
  if (!els.writeForm) return;
  els.writeForm.style.display = "flex";
  if (els.writeInput) {
    els.writeInput.value = "";
    els.writeInput.disabled = false;
    setTimeout(() => els.writeInput.focus(), 80);
  }
}

function hideWriteForm() {
  if (els.writeForm) els.writeForm.style.display = "none";
}

function t() {
  return STRINGS[state.lang] || STRINGS.zh;
}

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function sample(items, count) {
  return shuffle(items).slice(0, count);
}

function optionLabel(index) {
  return String(index + 1);
}

function formatDomain(value) {
  return t().domains[value] || value || "";
}

function activeLessons() {
  if (state.mode === "audio" || state.mode === "audio-w") return state.listeningLessons;
  if (state.mode === "meaning-w") {
    const seen = new Set();
    const all = [...state.imageLessons, ...state.listeningLessons];
    return all.filter(function(item) {
      if (seen.has(item.id)) return false;
      seen.add(item.id);
      return true;
    });
  }
  return state.imageLessons;
}

function kanaGroup(item) {
  const text = item?.word || "";
  const hasHiragana = /[぀-ゟ]/u.test(text);
  const hasKatakana = /[゠-ヿｦ-ﾟ]/u.test(text);
  const hasKanji = /[㐀-鿿]/u.test(text);

  if (hasKatakana && !hasHiragana && !hasKanji) {
    return "katakana";
  }
  if (hasHiragana && !hasKatakana && !hasKanji) {
    return "hiragana";
  }
  return "kanji_mixed";
}

function resetRound() {
  state.stats = { answered: 0, correct: 0, streak: 0, bestStreak: 0 };
  state.history = [];
  state.wrongWords = [];
  state.wrongWordsOnly = false;
  saveSession();
  updateStats();
  updateHistory();
  updateWrongWords();
}

function updateFilters() {
  const selected = els.domainFilter.value;
  els.domainFilter.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = t().filterAll;
  els.domainFilter.append(allOption);

  const domains = [...new Set(activeLessons().map((item) => item.domain))]
    .filter(Boolean)
    .sort((a, b) => formatDomain(a).localeCompare(formatDomain(b)));

  for (const domain of domains) {
    const option = document.createElement("option");
    option.value = domain;
    option.textContent = formatDomain(domain);
    els.domainFilter.append(option);
  }

  const hasSelected = domains.includes(selected);
  els.domainFilter.value = hasSelected ? selected : "all";
}

function applyFilters() {
  const level = els.levelFilter.value;
  const domain = els.domainFilter.value;
  const kana = els.kanaFilter.value;
  const wrongIds = new Set(state.wrongWords.map(function(w) { return w.id; }));

  state.filtered = activeLessons().filter((item) => {
    if (state.wrongWordsOnly && !wrongIds.has(item.id)) return false;
    const levelOk = level === "all" || item.level === level;
    const domainOk = domain === "all" || item.domain === domain;
    const kanaOk = kana === "all" || kanaGroup(item) === kana;
    return levelOk && domainOk && kanaOk;
  });
}

function buildChoices(correct) {
  const lessons = activeLessons();
  const sameDomain = state.filtered.filter(
    (item) => item.domain === correct.domain && item.id !== correct.id,
  );
  const fallback = lessons.filter((item) => item.id !== correct.id);
  const distractorCount = state.mode === "audio" ? 3 : 2;
  const pool = sameDomain.length >= distractorCount ? sameDomain : fallback;
  const distractors = sample(pool, distractorCount);
  return shuffle([correct, ...distractors]);
}

function meaningText(item) {
  if (state.lang === "zh") return item?.meaningZh || item?.meaning || "";
  return item?.meaning || item?.meaningZh || "";
}

function showEmptyState() {
  state.current = null;
  state.currentAudioKey = "";
  state.choices = [];
  state.answered = false;
  els.levelBadge.textContent = els.levelFilter.value;
  els.domainBadge.textContent = formatDomain(els.domainFilter.value);
  els.wordText.textContent = t().emptyState;
  els.readingText.textContent = "";
  els.answerLine.textContent = " ";
  els.answerLine.classList.remove("is-wrong");
  els.choices.innerHTML = "";
  hideSentence();
  updateSource(null);
}

function showQuestion() {
  cancelAutoAdvanceTimer();
  applyFilters();
  if (!state.filtered.length) {
    showEmptyState();
    return;
  }

  state.current = weightedPick(state.filtered);
  prepareAudioForQuestion(state.current);
  preloadAudioForItem(state.current);
  state.choices = buildChoices(state.current);
  state.answered = false;

  els.levelBadge.textContent = state.current.level;
  els.domainBadge.textContent = formatDomain(state.current.domain);
  els.answerLine.textContent = " ";
  els.answerLine.classList.remove("is-wrong");
  hideSentence();
  updateSource(state.current);

  if (state.mode === "audio" || state.mode === "audio-w") {
    els.wordText.textContent = state.mode === "audio" ? t().promptAudio : t().promptAudioW;
    els.readingText.textContent = "";
  } else if (state.mode === "meaning-w") {
    els.wordText.textContent = meaningText(state.current);
    els.readingText.textContent = "";
  } else {
    els.wordText.textContent = state.current.word;
    els.readingText.textContent = state.current.reading;
  }

  renderChoices();

  if (state.mode === "audio" || state.mode === "audio-w") {
    setTimeout(() => speakCurrent(), 80);
  }
}

function renderChoices() {
  els.choices.innerHTML = "";

  if (state.mode === "audio-w" || state.mode === "meaning-w") {
    els.choices.classList.remove("is-audio");
    hideWriteForm();
    showWriteForm();
    return;
  }

  hideWriteForm();
  els.choices.classList.toggle("is-audio", state.mode === "audio");

  state.choices.forEach((choice, index) => {
    const button = state.mode === "audio"
      ? createWordChoice(choice, index)
      : createImageChoice(choice, index);
    button.addEventListener("click", () => choose(choice.id));
    els.choices.append(button);
  });
}

function createImageChoice(choice, index) {
  const button = document.createElement("button");
  button.className = "choice-card image-choice";
  button.type = "button";
  button.dataset.id = choice.id;
  button.setAttribute("aria-label", `${optionLabel(index)} option`);

  const image = document.createElement("img");
  setAssetImage(image, choice.image);
  image.alt = "";
  image.loading = "eager";

  const caption = document.createElement("div");
  caption.className = "choice-caption";

  const strong = document.createElement("strong");
  strong.textContent = optionLabel(index);

  const span = document.createElement("span");
  span.textContent = "";

  caption.append(strong, span);
  button.append(image, caption);
  return button;
}

function createWordChoice(choice, index) {
  const button = document.createElement("button");
  button.className = "choice-card word-choice";
  button.type = "button";
  button.dataset.id = choice.id;
  button.setAttribute("aria-label", `${optionLabel(index)} option`);

  const label = document.createElement("div");
  label.className = "option-label";
  label.textContent = optionLabel(index);

  const word = document.createElement("div");
  word.className = "option-word";
  word.textContent = choice.word;

  const reading = document.createElement("div");
  reading.className = "option-reading";
  reading.textContent = "";

  const meaning = document.createElement("div");
  meaning.className = "option-meaning";
  meaning.textContent = "";

  button.append(label, word, reading, meaning);
  return button;
}

function createDecorImage(item, className) {
  const wrapper = document.createElement("div");
  wrapper.className = className;
  wrapper.title = `${item.word}：${meaningText(item)}`;

  const image = document.createElement("img");
  setAssetImage(image, item.image);
  image.alt = "";
  image.loading = "lazy";

  wrapper.append(image);
  return wrapper;
}

function renderDecorImages() {
  const imageItems = state.imageLessons.filter((item) => item.image);
  const picks = sample(imageItems, Math.min(10, imageItems.length));

  if (els.topGallery) {
    els.topGallery.innerHTML = "";
    picks.slice(0, 5).forEach((item) => {
      els.topGallery.append(createDecorImage(item, "top-gallery-item"));
    });
  }

  if (els.imageShelf) {
    els.imageShelf.innerHTML = "";
    picks.slice(0, 8).forEach((item) => {
      els.imageShelf.append(createDecorImage(item, "shelf-thumb"));
    });
  }
}

function recordOutcome(isCorrect) {
  state.stats.answered += 1;
  if (isCorrect) {
    state.stats.correct += 1;
    state.stats.streak += 1;
    if (state.stats.streak > state.stats.bestStreak) {
      state.stats.bestStreak = state.stats.streak;
    }
    if (state.wrongCounts[state.current.id]) {
      state.wrongCounts[state.current.id] = Math.max(0, state.wrongCounts[state.current.id] - 1);
      if (state.wrongCounts[state.current.id] === 0) delete state.wrongCounts[state.current.id];
      saveWrongCounts();
    }
  } else {
    state.stats.streak = 0;
    state.wrongCounts[state.current.id] = (state.wrongCounts[state.current.id] || 0) + 1;
    saveWrongCounts();
    if (!state.wrongWords.find((w) => w.id === state.current.id)) {
      state.wrongWords.unshift({
        id: state.current.id,
        word: state.current.word,
        meaning: meaningText(state.current),
      });
    }
  }

  state.history.unshift({
    word: state.current.word,
    meaning: meaningText(state.current),
    correct: isCorrect,
  });
  state.history = state.history.slice(0, 15);

  els.wordText.textContent = state.current.word;
  els.readingText.textContent = state.current.reading;
  const answer = meaningText(state.current);
  els.answerLine.textContent = isCorrect ? `${t().answerCorrect}${answer}` : `${t().answerWrong}${answer}`;
  els.answerLine.classList.toggle("is-wrong", !isCorrect);
  showSentence(state.current);
  updateStats();
  updateHistory();
  updateWrongWords();
  saveSession();

  if (state.mode === "image") {
    speakAnswerFeedback(state.current);
  } else {
    setTimeout(() => speakAnswerFeedback(state.current), 300);
  }

  startAutoAdvanceTimer();
}

function choose(id) {
  if (!state.current || state.answered) return;
  state.answered = true;
  revealChoices(id);
  recordOutcome(id === state.current.id);
}

function submitWrite() {
  if (!state.current || state.answered) return;
  const input = els.writeInput ? els.writeInput.value : "";
  if (!input.trim()) return;
  state.answered = true;
  if (els.writeInput) els.writeInput.disabled = true;
  recordOutcome(checkWriteAnswer(input, state.current));
}

function revealChoices(selectedId) {
  for (const card of els.choices.querySelectorAll(".choice-card")) {
    const choice = state.choices.find((item) => item.id === card.dataset.id);
    if (!choice) {
      continue;
    }

    if (state.mode === "audio") {
      card.querySelector(".option-reading").textContent = choice.reading;
      card.querySelector(".option-meaning").textContent = meaningText(choice);
    } else {
      card.querySelector(".choice-caption span").textContent = meaningText(choice);
    }

    if (card.dataset.id === state.current.id) {
      card.classList.add("is-correct");
    } else if (card.dataset.id === selectedId) {
      card.classList.add("is-wrong");
    } else {
      card.classList.add("is-muted");
    }
  }
}

function updateStats() {
  const accuracy = state.stats.answered
    ? Math.round((state.stats.correct / state.stats.answered) * 100)
    : 0;
  els.accuracyText.textContent = `${accuracy}%`;
  els.streakText.textContent = String(state.stats.streak);
  els.answeredText.textContent = String(state.stats.answered);
}

function updateHistory() {
  els.historyList.innerHTML = "";
  for (const item of state.history) {
    const li = document.createElement("li");
    li.className = item.correct ? "history-item-correct" : "history-item-wrong";
    const strong = document.createElement("strong");
    strong.textContent = item.word;
    li.append(strong, document.createTextNode(` ${item.correct ? t().historyCorrect : t().historyRetry}`));
    els.historyList.append(li);
  }
}

function showSentence(item) {
  if (!els.sentenceLine || !item) return;
  const ja = item.sentenceJa || "";
  const zh = item.sentenceZh || "";
  const en = item.sentenceEn || "";
  const trans = state.lang === "en" ? en : state.lang === "ja" ? "" : zh;
  if (!ja && !trans) {
    els.sentenceLine.hidden = true;
    return;
  }
  els.sentenceLine.innerHTML = "";
  if (ja) {
    const spanJa = document.createElement("span");
    spanJa.className = "sentence-ja";
    spanJa.textContent = ja;
    els.sentenceLine.append(spanJa);
  }
  if (trans) {
    if (ja) els.sentenceLine.append(document.createElement("br"));
    const spanTrans = document.createElement("span");
    spanTrans.textContent = trans;
    els.sentenceLine.append(spanTrans);
  }
  els.sentenceLine.hidden = false;
}

function hideSentence() {
  if (els.sentenceLine) els.sentenceLine.hidden = true;
}

function isWebUrl(value) {
  if (!value) {
    return false;
  }
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function updateSource(item) {
  if (!item) {
    els.sourceProvider.textContent = "-";
    els.licenseText.textContent = "-";
    els.creatorText.textContent = "-";
    els.sourceLink.style.visibility = "hidden";
    return;
  }

  if (state.mode === "audio" || state.mode === "audio-w" || state.mode === "meaning-w") {
    els.sourceProvider.textContent = currentAudioLabel(item);
    els.licenseText.textContent = t().sourceVoicevoxLicense;
    els.creatorText.textContent = currentAudioCredit(item);
    els.sourceLink.style.visibility = "hidden";
    return;
  }

  els.sourceProvider.textContent = item.source || t().sourceLocalImage;
  els.licenseText.textContent = item.license || "-";
  els.creatorText.textContent = item.creator || "RIKKA";
  if (isWebUrl(item.source)) {
    els.sourceLink.href = item.source;
    els.sourceLink.style.visibility = "visible";
  } else {
    els.sourceLink.removeAttribute("href");
    els.sourceLink.style.visibility = "hidden";
  }
}

function voiceForLang(langPrefix) {
  if (!("speechSynthesis" in window)) {
    return null;
  }
  return window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.toLowerCase().startsWith(langPrefix));
}

function japaneseVoice() {
  return voiceForLang("ja");
}

function speakWithBrowserVoice(text) {
  if (!("speechSynthesis" in window) || !text) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ja-JP";
  utterance.rate = state.mode === "audio" ? 0.78 : 0.84;
  const voice = japaneseVoice();
  if (voice) {
    utterance.voice = voice;
  }
  window.speechSynthesis.speak(utterance);
}

function playAudioWithFallback(sourcePath, speechText) {
  const primary = audioAssetUrl(sourcePath);
  const fallback = assetUrl(sourcePath, { cdn: true, version: null });
  const audio = cachedAudio(sourcePath) || new Audio(primary);
  try {
    audio.pause();
    audio.currentTime = 0;
  } catch {}
  audio.play().catch(() => {
    if (primary !== fallback) {
      const fallbackAudio = new Audio(fallback);
      fallbackAudio.play().catch(() => speakWithBrowserVoice(speechText));
      return;
    }
    speakWithBrowserVoice(speechText);
  });
}

function speakAnswerFeedback(item) {
  if (!item) {
    return;
  }
  const japanese = item.spoken || item.reading || item.word;
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  const audioPath = selectedAudioSource(item);
  if (audioPath) {
    playAudioWithFallback(audioPath, japanese);
    return;
  }
  speakWithBrowserVoice(japanese);
}

function speakCurrent() {
  if (!state.current) {
    return;
  }

  const speechText = state.current.spoken || state.current.reading || state.current.word;
  const audioPath = selectedAudioSource(state.current);
  if (audioPath) {
    playAudioWithFallback(audioPath, speechText);
    return;
  }

  speakWithBrowserVoice(speechText);
}

function setMode(mode) {
  if (state.mode !== mode) {
    state.mode = mode;
    resetRound();
  }
  els.modeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.mode === mode);
  });
  updateFilters();
  showQuestion();
}

function toggleWrongWordsOnly() {
  state.wrongWordsOnly = !state.wrongWordsOnly;
  updateWrongWords();
  showQuestion();
}

function showSummary() {
  if (!els.summaryOverlay) return;
  const s = state.stats;
  const accuracy = s.answered ? Math.round((s.correct / s.answered) * 100) : 0;
  const str = t();

  if (els.summaryMetrics) {
    els.summaryMetrics.innerHTML = "";
    const metrics = [
      [str.statsAnswered, s.answered],
      [str.statsAccuracy, accuracy + "%"],
      [str.statsBestStreak, s.bestStreak],
      [str.summaryWrongCount, state.wrongWords.length],
    ];
    for (const [label, value] of metrics) {
      const dl = document.createElement("dl");
      dl.className = "summary-metric";
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = String(value);
      dl.append(dt, dd);
      els.summaryMetrics.append(dl);
    }
  }

  if (els.summaryWrong) {
    els.summaryWrong.innerHTML = "";
    if (state.wrongWords.length) {
      const title = document.createElement("p");
      title.className = "summary-wrong-title";
      title.textContent = str.wrongWordsSection;
      const ol = document.createElement("ol");
      ol.className = "summary-wrong-list";
      for (const w of state.wrongWords.slice(0, 20)) {
        const li = document.createElement("li");
        const strong = document.createElement("strong");
        strong.textContent = w.word;
        li.append(strong, document.createTextNode(" " + w.meaning));
        ol.append(li);
      }
      els.summaryWrong.append(title, ol);
    } else if (s.answered > 0) {
      const p = document.createElement("p");
      p.className = "summary-wrong-title";
      p.textContent = str.summaryNoneWrong;
      els.summaryWrong.append(p);
    }
  }

  els.summaryOverlay.hidden = false;
}

function closeSummary() {
  if (els.summaryOverlay) els.summaryOverlay.hidden = true;
}

function setAudioVoice(value) {
  const exists = AUDIO_VOICES.some((voice) => voice.key === value);
  state.audioVoice = exists ? value : "random";
  try { localStorage.setItem(AUDIO_VOICE_KEY, state.audioVoice); } catch {}
  if (els.voiceSelect) els.voiceSelect.value = state.audioVoice;
  if (state.current) {
    prepareAudioForQuestion(state.current);
    updateSource(state.current);
  }
}

const DATA_VERSION = "20260705-audio-local";

async function loadJson(path) {
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

async function init() {
  state.wrongCounts = loadWrongCounts();
  loadSession();
  const savedLang = localStorage.getItem(LANG_KEY);
  if (savedLang && STRINGS[savedLang]) state.lang = savedLang;
  const savedAudioVoice = localStorage.getItem(AUDIO_VOICE_KEY);
  if (savedAudioVoice && AUDIO_VOICES.some((voice) => voice.key === savedAudioVoice)) {
    state.audioVoice = savedAudioVoice;
  }

  const [imagePayload, listeningPayload] = await Promise.all([
    loadJson("data/image-lessons.json"),
    loadJson("data/listening-lessons.json"),
  ]);
  state.imageLessons = imagePayload.lessons || [];
  state.listeningLessons = listeningPayload.lessons || [];
  renderDecorImages();
  applyLang(state.lang);
  updateStats();
  updateWrongWords();
  showQuestion();
}

els.nextButton.addEventListener("click", showQuestion);
els.speakButton.addEventListener("click", speakCurrent);
els.levelFilter.addEventListener("change", showQuestion);
els.domainFilter.addEventListener("change", showQuestion);
els.kanaFilter.addEventListener("change", showQuestion);
els.modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});
if (els.darkModeButton) els.darkModeButton.addEventListener("click", toggleDarkMode);
if (els.autoAdvanceButton) els.autoAdvanceButton.addEventListener("click", toggleAutoAdvance);
if (els.langSelect) els.langSelect.addEventListener("change", () => applyLang(els.langSelect.value));
if (els.voiceSelect) els.voiceSelect.addEventListener("change", () => setAudioVoice(els.voiceSelect.value));
if (els.writeForm) {
  els.writeForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitWrite();
  });
}
if (els.wrongReviewButton) els.wrongReviewButton.addEventListener("click", toggleWrongWordsOnly);
if (els.summaryButton) els.summaryButton.addEventListener("click", showSummary);
if (els.summaryCloseButton) els.summaryCloseButton.addEventListener("click", closeSummary);
if (els.summaryResetButton) {
  els.summaryResetButton.addEventListener("click", function() {
    resetRound();
    closeSummary();
    showQuestion();
  });
}
if (els.summaryOverlay) {
  els.summaryOverlay.addEventListener("click", function(e) {
    if (e.target === els.summaryOverlay) closeSummary();
  });
}

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const active = document.activeElement;
  if (active && active.matches("select")) return;

  const key = e.key.toLowerCase();

  if (!state.answered && state.current && state.mode !== "audio-w" && state.mode !== "meaning-w") {
    const idx = ["1", "2", "3", "4"].indexOf(key);
    if (idx !== -1 && state.choices[idx]) {
      e.preventDefault();
      choose(state.choices[idx].id);
      return;
    }
  }

  if (key === "r") {
    e.preventDefault();
    speakCurrent();
    return;
  }

  if (key === "escape") {
    closeSummary();
    cancelAutoAdvanceTimer();
    return;
  }

  if (key === " " || key === "enter") {
    if (active && active.matches("input") && !active.disabled) return;
    if (!state.answered && active && active.matches("button, a")) return;
    e.preventDefault();
    if (state.answered || !state.current) showQuestion();
  }
});

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {};
}

init().catch((error) => {
  els.wordText.textContent = t().loadError;
  els.readingText.textContent = "";
  els.answerLine.textContent = error.message;
  els.answerLine.classList.add("is-wrong");
});
