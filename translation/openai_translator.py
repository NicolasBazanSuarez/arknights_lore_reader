import json
from copy import deepcopy

from openai import OpenAI

from translation.context_builder import load_story_context

MODEL = "gpt-5.6-luna"

client = OpenAI()


BASE_TRANSLATION_INSTRUCTIONS = """
You are translating the story of the video game Arknights
from English to European Spanish (es-ES).

TRANSLATION RULES

- Produce a natural, literary and faithful Spanish translation.
- Do not translate mechanically word by word.
- Preserve meaning, tone, emotion, subtext and character personality.
- Never add information that is not present in the source.
- External lore is contextual assistance only.
- Never use lore to reveal information hidden by the current story.
- Preserve intentional ambiguity.
- Preserve pauses, hesitation, repetitions and interrupted sentences when meaningful.
- Translate idioms naturally according to their meaning and context.
- Translate medical and military terminology naturally and accurately.
- Do not censor insults, threats or violence.
- Preserve formal, military, casual and emotional registers.
- Use European Spanish.
- Prefer natural Spanish phrasing over literal English sentence structures.

TERMINOLOGY RULES

- "Doctor" must always remain "Doctor".
- Character names and codenames must remain unchanged.
- Proper names must remain unchanged unless the story context explicitly
  establishes a translated form.
- Generic speaker roles should be translated naturally into Spanish.
- "???" must remain exactly "???".
- An empty speaker must remain empty.
- Preserve game variables and placeholders exactly if any remain.

STRUCTURE RULES

You will receive JSON containing:
- the chapter title
- ordered dialogue blocks
- a numeric id for every dialogue block
- the speaker
- the dialogue lines

Translate the chapter title into Spanish while preserving numerical stage codes.

For every dialogue block:
- preserve its id exactly
- Every dialogue line has its own numeric id.
- Translate every line independently.
- Preserve every line id exactly.
- Return exactly one translated line for every input line.
- Never merge two line ids into one line.
- Never split one line id into multiple lines.
- Never omit a line, even if it contains only punctuation such as "...".
- do not add blocks
- do not remove blocks

The supplied story context is reference material only.
Global translation rules take priority over suggestions contained in that context.
"""


TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string"
        },
        "blocks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "speaker": {
                        "type": "string"
                    },
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer"
                                },
                                "text": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "id",
                                "text"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": [
                    "id",
                    "speaker",
                    "lines"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "title",
        "blocks"
    ],
    "additionalProperties": False
}


def translate_chapter(
    scenes: list[dict],
    chapter_title: str,
    story_id: str
) -> tuple[list[dict], str]:

    story_context = load_story_context(story_id)

    blocks = []
    block_locations = []

    block_id = 0

    for scene_index, scene in enumerate(scenes):
        for dialogue_index, dialogue in enumerate(scene["dialogues"]):

            blocks.append({
                "id": block_id,
                "speaker": dialogue["speaker"],
                "lines": [
                    {
                        "id": line_id,
                        "text": line
                    }
                    for line_id, line in enumerate(
                        dialogue["lines"]
                    )
                ]
            })

            block_locations.append(
                (scene_index, dialogue_index)
            )

            block_id += 1

    payload = {
        "chapter_title": chapter_title,
        "blocks": blocks
    }

    instructions = f"""
{BASE_TRANSLATION_INSTRUCTIONS}

STORY-SPECIFIC TRANSLATION CONTEXT

Use the following information only when it is relevant to correctly
understanding or translating the supplied dialogue.

Do not introduce information from this context into the translation.

{json.dumps(
    story_context,
    ensure_ascii=False,
    indent=2
)}
"""

    response = client.responses.create(
        model=MODEL,

        reasoning={
            "effort": "none"
        },

        instructions=instructions,

        input=json.dumps(
            payload,
            ensure_ascii=False
        ),

        text={
            "format": {
                "type": "json_schema",
                "name": "chapter_translation",
                "schema": TRANSLATION_SCHEMA,
                "strict": True
            }
        }
    )

    result = json.loads(
        response.output_text
    )

    translated_blocks = result["blocks"]

    if len(translated_blocks) != len(blocks):
        raise ValueError(
            "OpenAI ha devuelto un número distinto de bloques"
        )

    translated_by_id = {
        block["id"]: block
        for block in translated_blocks
    }

    translated_scenes = deepcopy(scenes)

    for original_block, location in zip(
        blocks,
        block_locations
    ):
        current_id = original_block["id"]

        if current_id not in translated_by_id:
            raise ValueError(
                f"Falta el bloque traducido {current_id}"
            )

        translated_block = translated_by_id[current_id]

        original_lines = original_block["lines"]
        translated_lines = translated_block["lines"]

        translated_lines_by_id = {
            line["id"]: line["text"]
            for line in translated_lines
        }

        expected_ids = {
            line["id"]
            for line in original_lines
        }

        received_ids = set(
            translated_lines_by_id.keys()
        )

        if received_ids != expected_ids:
            raise ValueError(
                f"El bloque {current_id} no contiene "
                f"los mismos IDs de línea. "
                f"Esperados: {sorted(expected_ids)}, "
                f"recibidos: {sorted(received_ids)}"
            )

        scene_index, dialogue_index = location

        speaker = translated_block["speaker"]

        if original_block["speaker"] == "":
            speaker = ""

        translated_scenes[
            scene_index
        ]["dialogues"][
            dialogue_index
        ]["speaker"] = speaker

        translated_scenes[
            scene_index
        ]["dialogues"][
            dialogue_index
        ]["lines"] = [
            translated_lines_by_id[
                line["id"]
            ]
            for line in original_lines
        ]

    return (
        translated_scenes,
        result["title"]
    )