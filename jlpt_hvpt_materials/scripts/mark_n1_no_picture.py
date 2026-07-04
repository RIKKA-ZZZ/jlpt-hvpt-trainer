from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "jlpt_hvpt_materials" / "derived"
DEFAULT_INPUT = DERIVED / "jlpt_vocab_imageable_candidates.csv"

NO_PICTURE = "NO PICTURE"

EXTRA_NO_PICTURE_IDS = {
    "n1_02445",  # animal husbandry is an industry, not one stable object
    "n1_01487",  # face / public stance is usually figurative
    "n1_00670",  # health / soundness / wholesome has no stable object
    "n1_03389",  # face / honour / reputation is figurative
    "n1_03428",  # leaders / brains, not a literal head
    "n1_03459",  # accounting surplus, not a black object
    "n1_02603",  # ear/head of a plant is easily confused with human body parts
    "n1_03320",  # shut mouth is an action/state, not a stable object
    "n1_01458",  # square metre / square is too abstract as a vocabulary image
    "n1_00810",  # able man / tumour has conflicting meanings
    "n1_00502",  # people / public is broad and not a stable subject
    "n1_02222",  # height above sea level is relational
    "n1_03333",  # fire prevention is a concept/event
    "n1_01966",  # book review relies on text
    "n1_02212",  # circulation/distribution is abstract
    "n1_02330",  # wasting money is an action/concept
    "n1_02840",  # English letters rely on text, bad for no-text image cards
    "n1_00556",  # suspension from school is a status
    "n1_00726",  # winning a prize is an event/result
    "n1_02087",  # bridge building / mediation is easily misread
    "n1_03186",  # dropping out of school is an event/status
}

VISUAL_STATE_TYPES = {"visual_state_scene"}

CONCRETE_ACTION_PATTERNS = [
    r"\bto (answer|ask|bathe|borrow|bring|build|buy|call|carry|catch|clean|climb|close|cook|copy|cut|dance|drink|drive|eat|enter|erase|fall|fly|give|go|hang|hear|hold|invite|jump|lend|listen|make|meet|open|paint|photograph|pick|play|practice|pull|push|put|read|receive|repair|return|ride|run|sell|send|shop|show|sing|sit|sleep|speak|stand|study|swim|take|teach|throw|tie|turn|use|visit|wait|walk|wash|wear|write)\b",
    r"\bto (adhere|attach|attack|bite|boil|bury|carve|chew|collide|cool|dry|exchange|freeze|harden|hit|imitate|insert|knock|lean|mince|mix|overflow|peel|pierce|print|refrigerate|scorch|shave|shine|shout|sniff|spill|squat|stab|straddle|strike|stumble|suck|taste|threaten|trick|unfasten|whisper|wrap|yell)\b",
    r"\bto (branch off|cut up|get down|go up|pass by|peel off|set out|tear off)\b",
    r"\bto get wet\b",
    r"\bto have a meal\b",
    r"\bphoto\b",
    r"\brecord a film\b",
    r"\bplay an instrument\b",
    r"\b(construction work|flower arrangement|horse racing|rice planting|sea bathing)\b",
    r"\b(play wind instruments|playing wind instruments|tea ceremony)\b",
    r"\bto (apologize|arrange|bend|bind|burn|chase|collapse|collect|decorate|dig|draw|fasten|float|fold|gather|grasp|kneel|leak|lift|light|line up|mend|pack|plant|point|press|scatter|scrape|shake|slide|soak|split|sprinkle|squeeze|stretch|sweep|tremble|weave)\b",
]

ABSTRACT_ACTION_PATTERNS = [
    r"\bperson (failing|being used|taking the place|urging|keeping|being one-sided)\b",
    r"\bperson (holding|outdoing|being zealous|being accepted|inheritting|blaming|plotting)\b",
    r"\bperson (bearing|going out of use|undertaking|looking anxiously|sinking in)\b",
    r"\bperson (falling in love|blessing|concluding|making progress|granting|publishing|participating)\b",
    r"\bperson (touching lightly|being engulfed|taking charge|presenting|accepting)\b",
]

ABSTRACT_OR_UNCLEAR_PATTERNS = [
    r"\bto be\b",
    r"\bto become\b",
    r"\bto be able\b",
    r"\bto need\b",
    r"\bto know\b",
    r"\bto understand\b",
    r"\bto decide\b",
    r"\bto think\b",
    r"\bto feel\b",
    r"\bto seem\b",
    r"\bto differ\b",
    r"\bto mean\b",
    r"\bto cost\b",
    r"\bto take time\b",
    r"\bto have\b",
    r"\bto exist\b",
    r"\bto live\b",
    r"\bimportant\b",
    r"\bnecessary\b",
    r"\bconvenient\b",
    r"\buseful\b",
    r"\bcorrect\b",
    r"\bwrong\b",
    r"\beasy\b",
    r"\bdifficult\b",
    r"\bpossible\b",
    r"\bimpossible\b",
    r"\binteresting\b",
    r"\bboring\b",
    r"\bkind\b",
    r"\bfamous\b",
    r"\bhealthy\b",
    r"\bquiet\b",
    r"\bbusy\b",
    r"\benough\b",
    r"\breason\b",
    r"\bcase\b",
    r"\bway\b",
    r"\bidea\b",
    r"\bplan\b",
    r"\bschedule\b",
    r"\bfeeling\b",
    r"\bmeaning\b",
    r"\bexperience\b",
    r"\bapplicable\b",
    r"\baffect\b",
    r"\bcategory\b",
    r"\bconcern\b",
    r"\bendure\b",
    r"\bforemost\b",
    r"\bfulfill\b",
    r"\binfluence\b",
    r"\bintellect\b",
    r"\bpreservation\b",
    r"\bsuitable\b",
    r"\bstatus\b",
    r"\battitude\b",
    r"\breputation\b",
    r"\bprestige\b",
    r"\bdignity\b",
    r"\bcredit\b",
    r"\bsoundness\b",
    r"\bwholesome\b",
    r"\bscope\b",
    r"\bmargin\b",
    r"\bdistribution\b",
    r"\bcirculation\b",
    r"\bcustoms\b",
    r"\bgeneration\b",
    r"\bpublic\b",
    r"\beverybody\b",
]

DIRECT_ABSTRACT_PATTERNS = [
    r"\bshape\b",
    r"\bform\b",
    r"\bhead .* section\b",
    r"\bhead .* department\b",
    r"\bdepartment head\b",
    r"\breason\b",
    r"\bcase\b",
    r"\bway\b",
    r"\bidea\b",
    r"\bplan\b",
    r"\bschedule\b",
    r"\bmeaning\b",
    r"\bexperience\b",
    r"\baddress\b",
    r"\bapplicable\b",
    r"\bbeginning\b",
    r"\bdeep blue\b",
    r"\bevery place\b",
    r"\bforemost\b",
    r"\bghastly pale\b",
    r"\bhealth preservation\b",
    r"\bhygiene\b",
    r"\bin school\b",
    r"\bintellect\b",
    r"\bleaving hospital\b",
    r"\blead\b",
    r"\bnecessities of life\b",
    r"\bpitch black\b",
    r"\bplace name\b",
    r"\bsanitation\b",
    r"\btaking a train\b",
    r"\bvarious places\b",
    r"\bvanguard\b",
    r"\bwater outage\b",
    r"\byear in school\b",
    r"\banimal husbandry\b",
    r"\bcomplete recovery\b",
    r"\bin good health\b",
    r"\bofficial stance\b",
    r"\bpublic position\b",
    r"\bon hand\b",
    r"\bat hand\b",
    r"\btone color\b",
    r"\btone quality\b",
    r"\btimbre\b",
    r"\bsynthesizer patch\b",
    r"\bbalance .* black\b",
    r"\bheight above sea level\b",
    r"\bsea route\b",
    r"\bfire prevention\b",
    r"\bfire proof\b",
    r"\bbook review\b",
    r"\bcirculation of money\b",
    r"\bwaste money\b",
    r"\benglish letter\b",
    r"\ball people\b",
    r"\beverybody\b",
    r"\bman of talent\b",
    r"\bprevious age\b",
    r"\bprevious generation\b",
    r"\bold friendship\b",
    r"\bracial customs\b",
    r"\bfolk customs\b",
    r"\btemporary absence from school\b",
    r"\bsuspension\b",
    r"\bsituation\b",
    r"\bposition\b",
    r"\bmargin\b",
    r"\bscope\b",
    r"\bwinning a prize\b",
    r"\bmediation\b",
    r"\bactual place\b",
    r"\bdropping out of school\b",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def matches_any(value: str, patterns: list[str]) -> bool:
    text = normalize(value)
    return any(re.search(pattern, text) for pattern in patterns)


def is_concrete_action(row: dict[str, str]) -> bool:
    meaning = row.get("meaning", "")
    query = row.get("image_query_en", "")
    text = " | ".join([meaning, query])
    return matches_any(text, CONCRETE_ACTION_PATTERNS)


def is_abstract_action(row: dict[str, str]) -> bool:
    meaning = row.get("meaning", "")
    query = row.get("image_query_en", "")
    first_gloss = re.split(r"[;|]", meaning, maxsplit=1)[0]
    text = " | ".join([first_gloss, query])
    return matches_any(text, ABSTRACT_ACTION_PATTERNS)


def is_abstract_or_unclear(row: dict[str, str]) -> bool:
    meaning = row.get("meaning", "")
    glosses = row.get("jmdict_glosses", "")
    query = row.get("image_query_en", "")
    text = " | ".join([meaning, glosses, query])
    return matches_any(text, ABSTRACT_OR_UNCLEAR_PATTERNS)


def is_direct_abstract(row: dict[str, str]) -> bool:
    meaning = row.get("meaning", "")
    query = row.get("image_query_en", "")
    text = " | ".join([meaning, query])
    return matches_any(text, DIRECT_ABSTRACT_PATTERNS)


def no_picture_reason(row: dict[str, str]) -> str:
    if row.get("id") in EXTRA_NO_PICTURE_IDS:
        return "N1 manual filter: abstract, relational, or easily misread"

    if row.get("image_type") in VISUAL_STATE_TYPES:
        return "visual state or adjective scene has no stable concrete object"

    if row.get("visual_domain") == "action_state":
        if is_abstract_action(row):
            return "abstract or unclear action/state"
        if is_concrete_action(row):
            return ""
        return "abstract or unclear action/state"

    if row.get("image_type") == "single_object_or_place" and is_direct_abstract(row):
        return "meaning is abstract, relational, or easily misread"

    return ""


def backup_input(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}.before_n1_no_picture_{stamp}{path.suffix}")
    shutil.copy2(path, backup)
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mark N1 words that should not be sent to image generation as NO PICTURE."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Allow replacing existing N1 review markers. By default, OK/NO/NO PICTURE are preserved.",
    )
    args = parser.parse_args()

    rows = read_csv(args.input)
    if not rows:
        raise SystemExit("No rows found.")

    fields = list(rows[0].keys())
    marked: list[dict[str, str]] = []
    candidates: list[dict[str, str]] = []
    preserved = 0

    for row in rows:
        if row.get("jlpt_level") != "N1":
            continue

        current_review = (row.get("image_review") or "").strip()
        reason = no_picture_reason(row)
        if current_review and not args.overwrite_existing:
            preserved += 1
        elif reason:
            row["image_review"] = NO_PICTURE
            marked.append(
                {
                    "id": row.get("id", ""),
                    "word": row.get("word", ""),
                    "reading": row.get("reading", ""),
                    "meaning": row.get("meaning", ""),
                    "meaningZh": row.get("meaning_zh", ""),
                    "image_type": row.get("image_type", ""),
                    "visual_domain": row.get("visual_domain", ""),
                    "image_query_en": row.get("image_query_en", ""),
                    "reason": reason,
                }
            )

        if row.get("jlpt_level") == "N1" and row.get("image_review", "").strip() != NO_PICTURE:
            candidates.append(
                {
                    "id": row.get("id", ""),
                    "word": row.get("word", ""),
                    "reading": row.get("reading", ""),
                    "meaning": row.get("meaning", ""),
                    "meaningZh": row.get("meaning_zh", ""),
                    "image_type": row.get("image_type", ""),
                    "visual_domain": row.get("visual_domain", ""),
                    "image_query_en": row.get("image_query_en", ""),
                    "review": row.get("image_review", ""),
                }
            )

    summary = {
        "input": str(args.input),
        "dry_run": args.dry_run,
        "n1_total": sum(1 for row in rows if row.get("jlpt_level") == "N1"),
        "preserved_existing_review": preserved,
        "new_no_picture_marks": len(marked),
        "n1_generation_candidates": len(candidates),
    }

    DERIVED.mkdir(parents=True, exist_ok=True)
    write_csv(
        DERIVED / "n1_no_picture_marked_rows.csv",
        marked,
        ["id", "word", "reading", "meaning", "meaningZh", "image_type", "visual_domain", "image_query_en", "reason"],
    )
    write_csv(
        DERIVED / "n1_image_generation_candidates.csv",
        candidates,
        ["id", "word", "reading", "meaning", "meaningZh", "image_type", "visual_domain", "image_query_en", "review"],
    )
    (DERIVED / "n1_no_picture_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if not marked:
        summary["updated_input"] = False
        summary["backup"] = ""
        (DERIVED / "n1_no_picture_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    backup = backup_input(args.input)
    write_csv(args.input, rows, fields)
    summary["updated_input"] = True
    summary["backup"] = str(backup)
    (DERIVED / "n1_no_picture_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


