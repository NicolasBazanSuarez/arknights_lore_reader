import json
from pathlib import Path

from openai import OpenAI

CONTEXT_MODEL = "gpt-5.6-terra"

CONTEXT_FOLDER = Path("translation/context")

client = OpenAI()

CONTEXT_INSTRUCTIONS = """
You are building translation context for an English-to-Spanish translation
of the video game Arknights.

The supplied text contains the chapters belonging to one Arknights story.

Your job is NOT to translate it.

Analyze the supplied story text and research the relevant Arknights lore
using the available web search tool.

Use external lore only to understand:
- characters
- character personalities and speech styles
- factions and organizations
- locations
- races/species when linguistically relevant
- relationships relevant to dialogue
- terminology specific to Arknights
- concepts that could be mistranslated without lore knowledge
- proper names that must remain untranslated

Focus only on information useful for translation.

IMPORTANT:
- Do not spoil or resolve mysteries that the supplied story has not revealed.
- Do not identify speakers written as "???".
- Do not resolve intentionally ambiguous identities.
- Do not use later lore to alter the meaning of earlier dialogue.
- External lore is contextual assistance only.
- Never invent facts.
- Prefer terminology actually used by Arknights.
- The final translation will use European Spanish (es-ES).
- Include only information that could materially affect translation.
- Do not include general biography, dates, trivia or background facts unless
  they are necessary to understand or translate something in the supplied story.
- Prefer concise translation notes over lore summaries.
- Do not include facts merely because they are available in the wiki.
- If external lore is not useful for translating the supplied text, omit it.

Return JSON only.

Use this structure:

{
    "story_summary": "...",
    "characters": [
        {
            "name": "...",
            "translation_notes": "...",
            "speech_style": "..."
        }
    ],
    "factions": [
        {
            "name": "...",
            "translation_notes": "..."
        }
    ],
    "locations": [
        {
            "name": "...",
            "translation_notes": "..."
        }
    ],
    "terminology": [
        {
            "english": "...",
            "spanish": "...",
            "notes": "..."
        }
    ],
    "other_notes": [
        "..."
    ]
}
"""

def extract_story_text(
    chapters: list[dict]
) -> str:

    parts = []

    for chapter in chapters:
        if not chapter.get("scenes"):
            continue

        chapter_lines = []

        for scene in chapter["scenes"]:
            for dialogue in scene["dialogues"]:
                speaker = dialogue["speaker"]

                for line in dialogue["lines"]:
                    if speaker:
                        chapter_lines.append(
                            f"{speaker}: {line}"
                        )
                    else:
                        chapter_lines.append(line)

        parts.append(
            f"""
CHAPTER: {chapter["title"]}

DIALOGUE:
{chr(10).join(chapter_lines)}
"""
        )

    return "\n".join(parts)


def build_story_context(
    story_id: str,
    story_title: str,
    chapters: list[dict],
    model: str = CONTEXT_MODEL,
    force: bool = False
) -> dict:
    
    CONTEXT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    destination = CONTEXT_FOLDER / f"{story_id}.json"

    if destination.exists() and not force:
        print(
            f"Contexto existente: {destination}"
        )

        return json.loads(
            destination.read_text(
                encoding="utf-8"
            )
        )

    story_text = extract_story_text(chapters)

    log(f"Generando contexto para: {story_title}")

    response = client.responses.create(
        model=model,

        reasoning={
            "effort": "low"
        },

        tools=[
            {
                "type": "web_search",
                "filters": {
                    "allowed_domains": [
                        "arknights.wiki.gg"
                    ]
                },
                "search_context_size": "medium"
            }
        ],

        tool_choice="required",

        instructions=CONTEXT_INSTRUCTIONS,

        input=f"""
STORY:
{story_title}

SOURCE CHAPTERS:

{story_text}
""",
    )
    
    raw_output = response.output_text.strip()

    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]

    if raw_output.startswith("```"):
        raw_output = raw_output[3:]

    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]

    context = json.loads(raw_output.strip())

    destination.write_text(
        json.dumps(
            context,
            ensure_ascii=False,
            indent=4
        ),
        encoding="utf-8"
    )

    log(f"Contexto generado: {destination}")

    return context

def load_story_context(story_id: str) -> dict:
    context_path = CONTEXT_FOLDER / f"{story_id}.json"

    if not context_path.exists():
        raise FileNotFoundError(
            f"No existe contexto para la historia: {story_id}"
        )

    return json.loads(
        context_path.read_text(encoding="utf-8")
    )
    
def story_context_exists(
    story_id: str
) -> bool:
    return (
        CONTEXT_FOLDER / f"{story_id}.json"
    ).exists()