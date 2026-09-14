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
    story_id: str,
    model: str = MODEL
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
        model=model,

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
OPERATOR_BASE_TRANSLATION_INSTRUCTIONS = """
You are translating Arknights operator material from English to European Spanish (es-ES).

This translation belongs to a single operator. The requests in this session are chained.
Use previous requests and previous translations in the same session as context so that terminology,
character interpretation, names, relationships and tone remain consistent across the whole operator.

TRANSLATION RULES

- Produce a natural, literary and faithful Spanish translation.
- Do not translate mechanically word by word.
- Preserve meaning, tone, emotion, subtext and character personality.
- Never add information that is not present in the source.
- Preserve intentional ambiguity.
- Translate idioms naturally according to their meaning and context.
- Translate medical and military terminology naturally and accurately.
- Do not censor insults, threats or violence.
- Preserve formal, military, casual and emotional registers.
- Use European Spanish.
- Prefer natural Spanish phrasing over literal English sentence structures.

TERMINOLOGY RULES

- "Doctor" must always remain "Doctor".
- Character names and codenames must remain unchanged.
- Proper names must remain unchanged unless their translation is clearly descriptive and established by context.
- Generic speaker roles should be translated naturally into Spanish.
- "???" must remain exactly "???".
- An empty speaker must remain empty.
- Preserve game variables and placeholders exactly if any remain.
- Keep terminology consistent with all previous turns in this operator translation session.

STRUCTURE RULES

- Preserve every numeric id exactly.
- Do not add or remove entries.
- Translate descriptive section, module, record and chapter titles naturally.
- Do not translate internal ids.
"""


OPERATOR_FILES_SCHEMA = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["id", "title", "text"],
                "additionalProperties": False
            }
        }
    },
    "required": ["sections"],
    "additionalProperties": False
}


OPERATOR_MODULES_SCHEMA = {
    "type": "object",
    "properties": {
        "modules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["id", "name", "description"],
                "additionalProperties": False
            }
        }
    },
    "required": ["modules"],
    "additionalProperties": False
}


OPERATOR_RECORDS_SCHEMA = {
    "type": "object",
    "properties": {
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "chapters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "blocks": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "speaker": {"type": "string"},
                                            "lines": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "text": {"type": "string"}
                                                    },
                                                    "required": ["id", "text"],
                                                    "additionalProperties": False
                                                }
                                            }
                                        },
                                        "required": ["id", "speaker", "lines"],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            "required": ["id", "title", "blocks"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["id", "title", "chapters"],
                "additionalProperties": False
            }
        }
    },
    "required": ["stories"],
    "additionalProperties": False
}


class OperatorTranslationSession:
    def __init__(
        self,
        operator_name: str,
        model: str = MODEL
    ):
        self.operator_name = operator_name
        self.model = model
        self.previous_response_id = None

    def _request(
        self,
        payload: dict,
        schema_name: str,
        schema: dict,
        step_instructions: str
    ) -> dict:
        instructions = f"""
{OPERATOR_BASE_TRANSLATION_INSTRUCTIONS}

CURRENT OPERATOR

{self.operator_name}

CURRENT STEP

{step_instructions}
"""

        request = {
            "model": self.model,
            "reasoning": {
                "effort": "none"
            },
            "instructions": instructions,
            "input": json.dumps(
                payload,
                ensure_ascii=False
            ),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True
                }
            },
            "store": True
        }

        if self.previous_response_id:
            request[
                "previous_response_id"
            ] = self.previous_response_id

        response = client.responses.create(
            **request
        )

        self.previous_response_id = (
            response.id
        )

        return json.loads(
            response.output_text
        )

    def translate_files(
        self,
        files: list[dict]
    ) -> list[dict]:
        if not files:
            return []

        payload = {
            "operator": self.operator_name,
            "sections": [
                {
                    "id": index,
                    "title": section.get(
                        "title",
                        ""
                    ),
                    "text": section.get(
                        "text",
                        ""
                    )
                }
                for index, section in enumerate(
                    files
                )
            ]
        }

        result = self._request(
            payload=payload,
            schema_name=(
                "operator_files_translation"
            ),
            schema=OPERATOR_FILES_SCHEMA,
            step_instructions="""
Translate all operator file sections supplied in this request.
Treat the entire file as one coherent character dossier.
Use all sections together to understand the operator before translating them.
"""
        )

        translated_sections = {
            section["id"]: section
            for section in result[
                "sections"
            ]
        }

        expected_ids = set(
            range(len(files))
        )

        if set(translated_sections) != expected_ids:
            raise ValueError(
                "La traducción de la ficha del operador "
                "no contiene los mismos IDs de sección"
            )

        translated_files = deepcopy(
            files
        )

        for index in range(len(files)):
            translated = (
                translated_sections[index]
            )

            translated_files[index][
                "title"
            ] = translated["title"]

            translated_files[index][
                "text"
            ] = translated["text"]

        return translated_files

    def translate_modules(
        self,
        modules: list[dict]
    ) -> list[dict]:
        if not modules:
            return []

        payload = {
            "operator": self.operator_name,
            "modules": [
                {
                    "id": index,
                    "module_id": module.get(
                        "id",
                        ""
                    ),
                    "name": module.get(
                        "name",
                        ""
                    ),
                    "description": module.get(
                        "description",
                        ""
                    )
                }
                for index, module in enumerate(
                    modules
                )
            ]
        }

        result = self._request(
            payload=payload,
            schema_name=(
                "operator_modules_translation"
            ),
            schema=OPERATOR_MODULES_SCHEMA,
            step_instructions="""
Translate all real modules supplied in this request.
The previous operator dossier and its translation are part of your context.
Keep terminology, names, relationships and character interpretation consistent with them.
"""
        )

        translated_modules_by_id = {
            module["id"]: module
            for module in result[
                "modules"
            ]
        }

        expected_ids = set(
            range(len(modules))
        )

        if (
            set(translated_modules_by_id)
            != expected_ids
        ):
            raise ValueError(
                "La traducción de módulos del operador "
                "no contiene los mismos IDs"
            )

        translated_modules = deepcopy(
            modules
        )

        for index in range(len(modules)):
            translated = (
                translated_modules_by_id[
                    index
                ]
            )

            translated_modules[index][
                "name"
            ] = translated["name"]

            translated_modules[index][
                "description"
            ] = translated[
                "description"
            ]

        return translated_modules

    def translate_records(
        self,
        stories: list[dict]
    ) -> list[dict]:
        if not stories:
            return []

        payload_stories = []

        for story_index, story in enumerate(
            stories
        ):
            payload_chapters = []

            for chapter_index, chapter in enumerate(
                story.get(
                    "chapters",
                    []
                )
            ):
                blocks = []
                block_id = 0

                for scene in chapter.get(
                    "scenes",
                    []
                ):
                    for dialogue in scene.get(
                        "dialogues",
                        []
                    ):
                        blocks.append({
                            "id": block_id,
                            "speaker": dialogue.get(
                                "speaker",
                                ""
                            ),
                            "lines": [
                                {
                                    "id": line_id,
                                    "text": line
                                }
                                for line_id, line in enumerate(
                                    dialogue.get(
                                        "lines",
                                        []
                                    )
                                )
                            ]
                        })

                        block_id += 1

                payload_chapters.append({
                    "id": chapter_index,
                    "title": chapter.get(
                        "name",
                        ""
                    ),
                    "blocks": blocks
                })

            payload_stories.append({
                "id": story_index,
                "title": story.get(
                    "name",
                    ""
                ),
                "chapters": payload_chapters
            })

        result = self._request(
            payload={
                "operator": self.operator_name,
                "stories": payload_stories
            },
            schema_name=(
                "operator_records_translation"
            ),
            schema=OPERATOR_RECORDS_SCHEMA,
            step_instructions="""
Translate all Operator Records supplied in this request.
The previous dossier and module translations are part of your context.
Use that information only to understand references and keep terminology consistent.
Do not add lore or explanations that are not present in the Record itself.
Preserve every story, chapter, dialogue block and line id exactly.
"""
        )

        translated_story_map = {
            story["id"]: story
            for story in result[
                "stories"
            ]
        }

        expected_story_ids = set(
            range(len(stories))
        )

        if (
            set(translated_story_map)
            != expected_story_ids
        ):
            raise ValueError(
                "La traducción de Operator Records "
                "no contiene los mismos IDs de historia"
            )

        translated_stories = deepcopy(
            stories
        )

        for story_index, original_story in enumerate(
            stories
        ):
            translated_story = (
                translated_story_map[
                    story_index
                ]
            )

            translated_stories[
                story_index
            ]["name"] = translated_story[
                "title"
            ]

            original_chapters = (
                original_story.get(
                    "chapters",
                    []
                )
            )

            translated_chapter_map = {
                chapter["id"]: chapter
                for chapter in translated_story[
                    "chapters"
                ]
            }

            expected_chapter_ids = set(
                range(len(original_chapters))
            )

            if (
                set(translated_chapter_map)
                != expected_chapter_ids
            ):
                raise ValueError(
                    f"El Operator Record {story_index} "
                    "no contiene los mismos IDs de capítulo"
                )

            for chapter_index, original_chapter in enumerate(
                original_chapters
            ):
                translated_chapter = (
                    translated_chapter_map[
                        chapter_index
                    ]
                )

                translated_stories[
                    story_index
                ]["chapters"][
                    chapter_index
                ]["name"] = (
                    translated_chapter[
                        "title"
                    ]
                )

                original_blocks = []
                block_locations = []
                block_id = 0

                for scene_index, scene in enumerate(
                    original_chapter.get(
                        "scenes",
                        []
                    )
                ):
                    for dialogue_index, dialogue in enumerate(
                        scene.get(
                            "dialogues",
                            []
                        )
                    ):
                        original_blocks.append({
                            "id": block_id,
                            "speaker": dialogue.get(
                                "speaker",
                                ""
                            ),
                            "lines": [
                                {
                                    "id": line_id,
                                    "text": line
                                }
                                for line_id, line in enumerate(
                                    dialogue.get(
                                        "lines",
                                        []
                                    )
                                )
                            ]
                        })

                        block_locations.append(
                            (
                                scene_index,
                                dialogue_index
                            )
                        )

                        block_id += 1

                translated_block_map = {
                    block["id"]: block
                    for block in translated_chapter[
                        "blocks"
                    ]
                }

                expected_block_ids = {
                    block["id"]
                    for block in original_blocks
                }

                if (
                    set(translated_block_map)
                    != expected_block_ids
                ):
                    raise ValueError(
                        f"El Operator Record {story_index}, "
                        f"capítulo {chapter_index}, no contiene "
                        "los mismos IDs de bloque"
                    )

                for original_block, location in zip(
                    original_blocks,
                    block_locations
                ):
                    translated_block = (
                        translated_block_map[
                            original_block["id"]
                        ]
                    )

                    translated_lines_by_id = {
                        line["id"]: line[
                            "text"
                        ]
                        for line in translated_block[
                            "lines"
                        ]
                    }

                    expected_line_ids = {
                        line["id"]
                        for line in original_block[
                            "lines"
                        ]
                    }

                    if (
                        set(translated_lines_by_id)
                        != expected_line_ids
                    ):
                        raise ValueError(
                            f"El bloque {original_block['id']} "
                            f"del Operator Record {story_index}, "
                            f"capítulo {chapter_index}, no contiene "
                            "los mismos IDs de línea"
                        )

                    scene_index, dialogue_index = (
                        location
                    )

                    speaker = translated_block[
                        "speaker"
                    ]

                    if original_block[
                        "speaker"
                    ] == "":
                        speaker = ""

                    translated_dialogue = (
                        translated_stories[
                            story_index
                        ]["chapters"][
                            chapter_index
                        ]["scenes"][
                            scene_index
                        ]["dialogues"][
                            dialogue_index
                        ]
                    )

                    translated_dialogue[
                        "speaker"
                    ] = speaker

                    translated_dialogue[
                        "lines"
                    ] = [
                        translated_lines_by_id[
                            line["id"]
                        ]
                        for line in original_block[
                            "lines"
                        ]
                    ]

        return translated_stories


def translate_operator_data(
    operator_data: dict,
    model: str = MODEL
) -> dict:
    translated_operator = deepcopy(
        operator_data
    )

    session = OperatorTranslationSession(
        operator_name=operator_data.get(
            "name",
            operator_data.get(
                "id",
                "Operator"
            )
        ),
        model=model
    )

    translated_operator[
        "files"
    ] = session.translate_files(
        operator_data.get(
            "files",
            []
        )
    )

    translated_operator[
        "modules"
    ] = session.translate_modules(
        operator_data.get(
            "modules",
            []
        )
    )

    translated_operator[
        "stories"
    ] = session.translate_records(
        operator_data.get(
            "stories",
            []
        )
    )

    return translated_operator
