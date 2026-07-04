const savedTheme = localStorage.getItem("hvpt_theme");
if (savedTheme) document.documentElement.dataset.theme = savedTheme;

const orbit = document.querySelector("#introImageOrbit");
const imageCount = document.querySelector("#introImageCount");
const listeningCount = document.querySelector("#introListeningCount");
const levelCount = document.querySelector("#introLevelCount");
let topTileZ = 20;

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
    const response = await fetch(`data/image-lessons.json?v=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Could not load image lessons: ${response.status}`);
    }
    const payload = await response.json();
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
      image.src = lesson.image;
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
  return new Intl.NumberFormat("zh-CN").format(value);
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
    const [imageResponse, listeningResponse] = await Promise.all([
      fetch(`data/image-lessons.json?v=${Date.now()}`, { cache: "no-store" }),
      fetch(`data/listening-lessons.json?v=${Date.now()}`, { cache: "no-store" }),
    ]);
    if (!imageResponse.ok || !listeningResponse.ok) {
      throw new Error("Could not load lesson stats.");
    }

    const [imagePayload, listeningPayload] = await Promise.all([
      imageResponse.json(),
      listeningResponse.json(),
    ]);
    const imageLessons = imagePayload.lessons || [];
    const listeningLessons = listeningPayload.lessons || [];
    const levels = sortedLevels([...imageLessons, ...listeningLessons]);

    imageCount.textContent = formatCount(imageLessons.length);
    listeningCount.textContent = formatCount(listeningLessons.length);
    if (levels.length) {
      levelCount.innerHTML = "";
      for (const level of levels) {
        const badge = document.createElement("span");
        badge.className = "intro-level-badge";
        badge.textContent = level;
        levelCount.append(badge);
      }
    } else {
      levelCount.textContent = "-";
    }
  } catch {
    imageCount.textContent = "-";
    listeningCount.textContent = "-";
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

loadIntroStats();
loadIntroImages();
