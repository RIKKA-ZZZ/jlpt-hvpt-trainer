from __future__ import annotations

import csv
import gzip
import html
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOCAB_DIR = ROOT / "tanos_vocab"
JMDICT_PATH = ROOT / "jmdict" / "JMdict_e.gz"
OUT_DIR = ROOT / "derived"


JP_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


DOMAIN_KEYWORDS = {
    "animal": {
        "animal",
        "dog",
        "cat",
        "bird",
        "fish",
        "horse",
        "cow",
        "pig",
        "mouse",
        "insect",
        "lion",
        "tiger",
        "rabbit",
    },
    "food_drink": {
        "food",
        "rice",
        "meal",
        "bread",
        "water",
        "tea",
        "coffee",
        "milk",
        "meat",
        "fish",
        "egg",
        "fruit",
        "vegetable",
        "soup",
        "beer",
        "wine",
        "cake",
        "sugar",
    },
    "person_family": {
        "person",
        "people",
        "man",
        "woman",
        "child",
        "boy",
        "girl",
        "student",
        "teacher",
        "doctor",
        "friend",
        "mother",
        "father",
        "brother",
        "sister",
        "wife",
        "husband",
        "family",
        "grandmother",
        "grandfather",
        "employee",
        "customer",
    },
    "place_building": {
        "place",
        "station",
        "school",
        "hospital",
        "office",
        "bank",
        "post office",
        "restaurant",
        "shop",
        "store",
        "park",
        "room",
        "kitchen",
        "house",
        "building",
        "hotel",
        "library",
        "airport",
        "factory",
        "street",
        "road",
    },
    "transport": {
        "car",
        "train",
        "bus",
        "taxi",
        "bicycle",
        "airplane",
        "ship",
        "vehicle",
        "subway",
    },
    "object_tool": {
        "book",
        "pen",
        "pencil",
        "paper",
        "letter",
        "postcard",
        "bag",
        "umbrella",
        "phone",
        "telephone",
        "camera",
        "computer",
        "desk",
        "chair",
        "table",
        "watch",
        "clock",
        "key",
        "ticket",
        "map",
        "money",
        "newspaper",
        "magazine",
        "vase",
        "fork",
        "spoon",
        "knife",
        "cup",
        "glass",
        "box",
        "machine",
    },
    "nature_weather": {
        "rain",
        "snow",
        "wind",
        "cloud",
        "sky",
        "sun",
        "moon",
        "star",
        "mountain",
        "river",
        "sea",
        "ocean",
        "tree",
        "flower",
        "grass",
        "weather",
        "earthquake",
        "fire",
    },
    "body_health": {
        "head",
        "face",
        "eye",
        "ear",
        "nose",
        "mouth",
        "hand",
        "foot",
        "leg",
        "body",
        "stomach",
        "tooth",
        "health",
        "illness",
        "medicine",
    },
    "clothing": {
        "clothes",
        "shirt",
        "coat",
        "shoes",
        "hat",
        "socks",
        "dress",
        "skirt",
        "jacket",
        "uniform",
    },
    "color_shape": {
        "black",
        "white",
        "red",
        "blue",
        "green",
        "yellow",
        "brown",
        "color",
        "circle",
        "square",
        "shape",
    },
}


SKIP_POS_KEYWORDS = {
    "particle",
    "auxiliary",
    "conjunction",
    "counter",
    "prefix",
    "suffix",
    "pronoun",
    "copula",
}

ABSTRACT_WORDS = {
    "case",
    "occasion",
    "situation",
    "circumstance",
    "reason",
    "purpose",
    "meaning",
    "idea",
    "opinion",
    "feeling",
    "thought",
    "way",
    "method",
    "matter",
    "thing",
    "time",
    "period",
    "number",
    "amount",
    "level",
    "degree",
    "condition",
    "relationship",
    "relation",
    "ability",
    "possibility",
    "chance",
    "result",
    "effect",
    "influence",
    "rule",
    "system",
    "society",
    "economy",
    "politics",
    "culture",
    "information",
    "news",
    "language",
    "grammar",
    "word",
    "sentence",
}

SCENE_VERBS = {
    "eat",
    "drink",
    "read",
    "write",
    "study",
    "learn",
    "teach",
    "run",
    "walk",
    "go",
    "come",
    "return",
    "sleep",
    "wake",
    "work",
    "buy",
    "sell",
    "cook",
    "wash",
    "clean",
    "open",
    "close",
    "sit",
    "stand",
    "wait",
    "meet",
    "speak",
    "talk",
    "listen",
    "hear",
    "watch",
    "see",
    "look",
    "play",
    "sing",
    "dance",
    "swim",
    "drive",
    "travel",
    "send",
    "receive",
    "carry",
    "wear",
    "put",
    "take",
    "make",
}

VISUAL_ADJECTIVES = {
    "big",
    "small",
    "large",
    "little",
    "long",
    "short",
    "new",
    "old",
    "hot",
    "cold",
    "warm",
    "cool",
    "bright",
    "dark",
    "high",
    "low",
    "wide",
    "narrow",
    "heavy",
    "light",
    "thick",
    "thin",
    "beautiful",
    "dirty",
    "clean",
    "quiet",
    "noisy",
    "busy",
    "empty",
    "full",
    "fast",
    "slow",
}


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub("", value)
    value = SPACE_RE.sub(" ", value)
    return value.strip()


def has_japanese(value: str) -> bool:
    return bool(JP_RE.search(value or ""))


def read_anki_cards(path: Path) -> dict[str, list[str]]:
    con = sqlite3.connect(path)
    cur = con.cursor()
    rows = cur.execute("select question, answer from cards").fetchall()
    result: dict[str, list[str]] = defaultdict(list)
    for question, answer in rows:
        question = clean_text(question)
        answer = clean_text(answer)
        if not question or not answer or not has_japanese(question):
            continue
        if answer not in result[question]:
            result[question].append(answer)
    con.close()
    return result


def read_tanos_vocab() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for level_num in range(1, 6):
        level = f"N{level_num}"
        eng_path = VOCAB_DIR / f"Tanos_{level}_vocab_kanji_eng.anki"
        reading_path = VOCAB_DIR / f"Tanos_{level}_vocab_kanji_hiragana.anki"
        meanings = read_anki_cards(eng_path)
        readings = read_anki_cards(reading_path)
        all_words = sorted(set(meanings) | set(readings))
        for word in all_words:
            key = (level, word)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "jlpt_level": level,
                    "word": word,
                    "reading": " / ".join(readings.get(word, [])),
                    "meaning": " | ".join(meanings.get(word, [])),
                    "source": "Tanos JLPT vocabulary",
                }
            )
    return records


def collect_jmdict_matches(targets: set[str]) -> dict[str, dict[str, object]]:
    matches: dict[str, dict[str, object]] = {}
    if not JMDICT_PATH.exists():
        return matches
    with gzip.open(JMDICT_PATH, "rb") as fh:
        for _event, elem in ET.iterparse(fh, events=("end",)):
            if elem.tag != "entry":
                continue
            kebs = [x.text or "" for x in elem.findall("k_ele/keb")]
            rebs = [x.text or "" for x in elem.findall("r_ele/reb")]
            terms = [t for t in [*kebs, *rebs] if t]
            relevant = [t for t in terms if t in targets]
            if relevant:
                poss: list[str] = []
                glosses: list[str] = []
                for sense in elem.findall("sense"):
                    for pos in sense.findall("pos"):
                        if pos.text and pos.text not in poss:
                            poss.append(pos.text)
                    for gloss in sense.findall("gloss"):
                        lang = gloss.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "eng")
                        if lang == "eng" and gloss.text and gloss.text not in glosses:
                            glosses.append(gloss.text)
                    if len(glosses) >= 8:
                        break
                data = {
                    "kanji_forms": kebs,
                    "readings": rebs,
                    "pos": poss,
                    "glosses": glosses,
                }
                for term in relevant:
                    matches.setdefault(term, data)
            elem.clear()
    return matches


def first_meaning(meaning: str, glosses: list[str]) -> str:
    raw = meaning or " | ".join(glosses[:3])
    raw = raw.split("|")[0]
    raw = raw.split(";")[0]
    raw = raw.split(",")[0]
    raw = re.sub(r"\([^)]*\)", "", raw)
    raw = raw.strip()
    raw = re.sub(r"^(a|an|the)\s+", "", raw, flags=re.I)
    return raw


def lower_words(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z'-]*", text.lower()))


def detect_domain(query: str) -> str:
    q = query.lower()
    words = lower_words(q)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in q:
                    return domain
            elif kw in words:
                return domain
    return "general"


def is_abstract(text: str) -> bool:
    words = lower_words(text)
    return bool(words & ABSTRACT_WORDS)


def verb_base(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"^to\s+", "", text)
    text = text.split(";")[0].split(",")[0].strip()
    return text


def gerund(verb: str) -> str:
    base = verb.split()[0] if verb else ""
    if not base:
        return verb
    if base.endswith("ie"):
        base = base[:-2] + "ying"
    elif base.endswith("e") and base not in {"be", "see"}:
        base = base[:-1] + "ing"
    elif len(base) >= 3 and base[-1] not in "aeiouy" and base[-2] in "aeiou" and base[-3] not in "aeiou":
        base = base + base[-1] + "ing"
    else:
        base = base + "ing"
    rest = " ".join(verb.split()[1:])
    return f"{base} {rest}".strip()


def classify(record: dict[str, str], jmdict: dict[str, object]) -> dict[str, object]:
    pos = [str(p).lower() for p in jmdict.get("pos", [])] if jmdict else []
    glosses = [str(g) for g in jmdict.get("glosses", [])] if jmdict else []
    meaning = record.get("meaning") or " | ".join(glosses[:3])
    query = first_meaning(meaning, glosses)
    words = lower_words(query)
    pos_text = " | ".join(pos)
    reason = []
    initial_domain = detect_domain(query)

    status = "review"
    image_type = "manual_review"
    score = 45

    if any(skip in pos_text for skip in SKIP_POS_KEYWORDS):
        status = "skip"
        image_type = "not_recommended"
        score = 10
        reason.append("function word or bound form")
    elif not query:
        status = "skip"
        image_type = "missing_meaning"
        score = 5
        reason.append("missing usable meaning")
    elif "noun" in pos_text and initial_domain != "general":
        status = "direct_image"
        image_type = "single_object_or_place"
        score = 84
        reason.append(f"concrete noun domain: {initial_domain}")
    elif "verb" in pos_text:
        base = verb_base(query)
        if lower_words(base) & SCENE_VERBS or query.lower().startswith("to "):
            status = "scene_image"
            image_type = "person_action_scene"
            score = 72
            query = f"person {gerund(base)}"
            reason.append("verb can be shown as an action scene")
        else:
            status = "review"
            image_type = "action_needs_review"
            score = 48
            query = f"person {gerund(base)}"
            reason.append("verb, but visual clarity may vary")
    elif "adjective" in pos_text or "adjectival" in pos_text:
        if words & VISUAL_ADJECTIVES or not is_abstract(query):
            status = "scene_image"
            image_type = "visual_state_scene"
            score = 68
            query = f"{query} scene"
            reason.append("adjective can be shown visually")
        else:
            status = "review"
            image_type = "abstract_state"
            score = 42
            reason.append("adjective is abstract or context-dependent")
    elif "noun" in pos_text:
        if is_abstract(query):
            status = "skip"
            image_type = "abstract_noun"
            score = 25
            reason.append("abstract noun")
        else:
            status = "review"
            image_type = "noun_needs_review"
            score = 55
            reason.append("noun, but concreteness is uncertain")
    elif "adverb" in pos_text:
        status = "skip"
        image_type = "adverb"
        score = 20
        reason.append("adverb is usually weak for picture choice")
    else:
        domain = detect_domain(query)
        if domain != "general":
            status = "direct_image"
            image_type = "single_object_or_place"
            score = 75
            reason.append(f"meaning suggests concrete domain: {domain}")
        elif is_abstract(query):
            status = "skip"
            image_type = "abstract"
            score = 20
            reason.append("abstract meaning")
        else:
            reason.append("insufficient POS signal")

    domain = detect_domain(query)
    if status == "scene_image":
        domain = "action_state"
    if status == "skip":
        domain = "skip"

    return {
        "image_status": status,
        "image_score": score,
        "image_type": image_type,
        "visual_domain": domain,
        "image_query_en": query,
        "image_query_ja": record["word"],
        "distractor_pool": domain if domain != "skip" else "",
        "classification_reason": "; ".join(reason),
    }


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = read_tanos_vocab()
    targets = {r["word"] for r in records}
    targets.update(r["reading"] for r in records if r.get("reading"))
    jmdict_matches = collect_jmdict_matches(targets)

    out_rows: list[dict[str, object]] = []
    for idx, rec in enumerate(records, start=1):
        jm = jmdict_matches.get(rec["word"], {})
        if not rec.get("reading") and jm:
            rec["reading"] = " / ".join(jm.get("readings", [])[:3])
        if not rec.get("meaning") and jm:
            rec["meaning"] = " | ".join(jm.get("glosses", [])[:3])
        classification = classify(rec, jm)
        row = {
            "id": f"{rec['jlpt_level'].lower()}_{idx:05d}",
            **rec,
            "jmdict_pos": " | ".join(jm.get("pos", [])) if jm else "",
            "jmdict_glosses": " | ".join(jm.get("glosses", [])[:5]) if jm else "",
            **classification,
        }
        out_rows.append(row)

    preferred_status = {"direct_image", "scene_image"}
    candidate_rows = [
        r
        for r in out_rows
        if r["image_status"] in preferred_status and int(r["image_score"]) >= 60
    ]
    review_rows = [
        r
        for r in out_rows
        if r["image_status"] == "review" or 40 <= int(r["image_score"]) < 60
    ]
    candidate_rows.sort(
        key=lambda r: (
            ["N5", "N4", "N3", "N2", "N1"].index(str(r["jlpt_level"])),
            -int(r["image_score"]),
            str(r["visual_domain"]),
            str(r["word"]),
        )
    )

    fields = [
        "id",
        "jlpt_level",
        "word",
        "reading",
        "meaning",
        "jmdict_pos",
        "jmdict_glosses",
        "image_status",
        "image_score",
        "image_type",
        "visual_domain",
        "image_query_en",
        "image_query_ja",
        "distractor_pool",
        "classification_reason",
        "source",
    ]

    write_csv(OUT_DIR / "jlpt_vocab_imageability_all.csv", out_rows, fields)
    write_csv(OUT_DIR / "jlpt_vocab_imageable_candidates.csv", candidate_rows, fields)
    write_csv(OUT_DIR / "jlpt_vocab_image_needs_review.csv", review_rows, fields)
    with (OUT_DIR / "jlpt_vocab_imageable_candidates.json").open("w", encoding="utf-8") as fh:
        json.dump(candidate_rows, fh, ensure_ascii=False, indent=2)

    summary = {
        "total_words": len(out_rows),
        "candidate_words": len(candidate_rows),
        "review_words": len(review_rows),
        "by_status": Counter(str(r["image_status"]) for r in out_rows),
        "candidates_by_level": Counter(str(r["jlpt_level"]) for r in candidate_rows),
        "candidates_by_domain": Counter(str(r["visual_domain"]) for r in candidate_rows),
        "sources": [
            "Tanos JLPT vocabulary Anki decks",
            "JMdict_e.gz for POS/gloss enrichment",
        ],
    }
    with (OUT_DIR / "imageable_vocab_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2, default=dict)

    print(json.dumps(summary, ensure_ascii=False, indent=2, default=dict))


if __name__ == "__main__":
    main()
