import re
from collections import OrderedDict

SCENE_PATTERN = re.compile(
    r'^\s*\[(?P<type>Background|Image)\((?P<attrs>[^]]*)\)\]',
    re.IGNORECASE
)

IMAGE_ATTR_PATTERN = re.compile(
    r'\bimage\s*=\s*"([^"]+)"',
    re.IGNORECASE
)

DIALOG_PATTERN = re.compile(
    r'^\s*\[name\s*=\s*"([^"]*)"\]\s*(.*)$',
    re.IGNORECASE
)

DECISION_PATTERN = re.compile(
    r'^\s*\[Decision\((?P<attrs>[^]]*)\)\]',
    re.IGNORECASE
)

PREDICATE_PATTERN = re.compile(
    r'^\s*\[Predicate\((?P<attrs>[^]]*)\)\]',
    re.IGNORECASE
)

OPTIONS_ATTR_PATTERN = re.compile(
    r'\boptions\s*=\s*"([^"]*)"',
    re.IGNORECASE
)

VALUES_ATTR_PATTERN = re.compile(
    r'\bvalues\s*=\s*"([^"]*)"',
    re.IGNORECASE
)

REFERENCES_ATTR_PATTERN = re.compile(
    r'\breferences\s*=\s*"([^"]*)"',
    re.IGNORECASE
)

CHARACTER_TAG_PATTERN = re.compile(
    r'^\s*\[Character(?:\((?P<params>[^\]]*)\))?\]\s*$',
    re.IGNORECASE
)

CHARACTER_NAME_PATTERN = re.compile(
    r'\bname\d*\s*=\s*"?(?P<name>[^",)\s]+)"?',
    re.IGNORECASE
)

def extract_character_base_name(
    raw_name: str
) -> str:
    raw_name = raw_name.strip()

    if "#" in raw_name:
        return raw_name.split(
            "#",
            1
        )[0]

    return raw_name

def parse_story_text(
    text: str,
    speaker_names: dict[str, str] | None = None
) -> list[dict]:
    
    if speaker_names is None:
        speaker_names = {}
    
    scenes = []

    current_background = None
    current_image_type = None
    current_dialogues = []
    current_scene_characters = OrderedDict()
    character_display_names = {
    character_id.lower(): name

    for character_id, name
        in speaker_names.items()
    }

    pending_character_id = None

    # Estado de las decisiones.
    selected_decision_value = None
    predicate_active = True

    def save_scene():
        nonlocal current_background
        nonlocal current_image_type
        nonlocal current_dialogues
        nonlocal current_scene_characters
        nonlocal pending_character_id

        if current_dialogues:
            scenes.append({
                "background": (
                    current_background
                    or "UNKNOWN"
                ),
                "image_type": (
                    current_image_type
                    or "background"
                ),
                "dialogues": current_dialogues,
                "characters": list(
                    current_scene_characters.values()
                )
            })

        current_dialogues = []
        current_scene_characters = OrderedDict()
        pending_character_id = None
    

    def add_dialogue(
        speaker: str,
        dialogue: str
    ):
        nonlocal pending_character_id

        if (
            speaker
            and pending_character_id
        ):
            character_key = (
                pending_character_id.lower()
            )

            # No sobreescribimos nombres que ya
            # conocemos por el catálogo.
            if character_key not in character_display_names:
                character_display_names[
                    character_key
                ] = speaker

            character = current_scene_characters.get(
                pending_character_id
            )

            if character:
                character[
                    "display_name"
                ] = character_display_names.get(
                    character_key,
                    speaker
                )

            pending_character_id = None

        if (
            current_dialogues
            and current_dialogues[-1]["speaker"]
            == speaker
        ):
            current_dialogues[-1][
                "lines"
            ].append(dialogue)

        else:
            current_dialogues.append({
                "speaker": speaker,
                "lines": [dialogue]
            })

    for line in text.splitlines():

        # -------------------------------------------------
        # Fin / punto de unión de una ramificación
        # -------------------------------------------------

        if re.match(
            r'^\s*\[SkipToThis',
            line,
            re.IGNORECASE
        ):
            selected_decision_value = None
            predicate_active = True
            continue

        # -------------------------------------------------
        # Predicate
        # -------------------------------------------------

        predicate_match = re.match(
            r'^\s*\[Predicate\((?P<attrs>[^]]*)\)\]',
            line,
            re.IGNORECASE
        )

        if predicate_match:
            attrs = predicate_match.group(
                "attrs"
            )

            references_match = re.search(
                r'\breferences\s*=\s*"([^"]*)"',
                attrs,
                re.IGNORECASE
            )

            if references_match:
                references = [
                    value.strip()
                    for value
                    in references_match.group(1).split(";")
                ]

                if selected_decision_value is None:
                    predicate_active = True

                else:
                    predicate_active = (
                        selected_decision_value
                        in references
                    )

            else:
                predicate_active = True

            continue

        # Si estamos dentro de una rama que no
        # corresponde a la opción seleccionada,
        # ignoramos completamente su contenido.
        if not predicate_active:
            continue

        # -------------------------------------------------
        # Decision
        # -------------------------------------------------

        decision_match = re.match(
            r'^\s*\[Decision\((?P<attrs>[^]]*)\)\]',
            line,
            re.IGNORECASE
        )

        if decision_match:
            attrs = decision_match.group(
                "attrs"
            )

            options_match = re.search(
                r'\boptions\s*=\s*"([^"]*)"',
                attrs,
                re.IGNORECASE
            )

            values_match = re.search(
                r'\bvalues\s*=\s*"([^"]*)"',
                attrs,
                re.IGNORECASE
            )

            if not options_match:
                continue

            options = [
                option.strip()
                for option
                in options_match.group(1).split(";")
            ]

            if not options:
                continue

            # Siempre seleccionamos la primera opción.
            first_option = options[0]

            if values_match:
                values = [
                    value.strip()
                    for value
                    in values_match.group(1).split(";")
                ]

            else:
                values = []

            # El value asociado a la primera opción.
            selected_decision_value = (
                values[0]
                if values
                else "1"
            )

            predicate_active = True

            # Las decisiones son diálogos del Doctor.
            if first_option:
                add_dialogue(
                    "Doctor",
                    first_option
                )

            continue

        # -------------------------------------------------
        # Cambio de escena
        # -------------------------------------------------

        scene_match = SCENE_PATTERN.match(
            line
        )

        if scene_match:
            attrs = scene_match.group(
                "attrs"
            )

            image_match = (
                IMAGE_ATTR_PATTERN.search(
                    attrs
                )
            )

            if image_match:

                background_name = (
                    image_match
                    .group(1)
                    .strip()
                )

                # bg_black se utiliza como transición visual
                # en los scripts, pero no aporta información
                # útil al recopilatorio.
                #
                # Lo ignoramos completamente para que tampoco
                # divida artificialmente los diálogos.
                if background_name.lower() == "bg_black":
                    continue

                save_scene()

                current_background = background_name

                current_image_type = (
                    scene_match
                    .group("type")
                    .lower()
                )

                current_dialogues = []

            continue
        
        character_match = CHARACTER_TAG_PATTERN.match(
            line
        )

        if character_match:
            params = (
                character_match.group(
                    "params"
                )
                or ""
            )

            character_ids = []

            for name_match in CHARACTER_NAME_PATTERN.finditer(
                params
            ):
                raw_character_name = (
                    name_match
                    .group("name")
                    .strip()
                )

                if not raw_character_name:
                    continue

                character_id = extract_character_base_name(
                    raw_character_name
                )

                character_ids.append(
                    character_id
                )

                character_key = (
                    character_id.lower()
                )

                display_name = (
                    character_display_names.get(
                        character_key,
                        character_id
                    )
                )

                if (
                    character_id
                    not in current_scene_characters
                ):
                    current_scene_characters[
                        character_id
                    ] = {
                        "asset_id": character_id
                    }

                else:
                    current_scene_characters[
                        character_id
                    ][
                        "display_name"
                    ] = display_name

            # Si aparece un único personaje podemos
            # aprender su nombre con el diálogo siguiente.
            if len(character_ids) == 1:
                pending_character_id = (
                    character_ids[0]
                )
            else:
                pending_character_id = None

            continue
        
        head_dialog_match = re.match(
            r'^\s*\[Dialog\((?P<attrs>[^\]]*)\)\]\s*(?P<text>.*)$',
            line,
            re.IGNORECASE
        )

        if head_dialog_match:

            attrs = head_dialog_match.group(
                "attrs"
            )

            dialogue = head_dialog_match.group(
                "text"
            ).strip()

            head_match = re.search(
                r'\bhead\s*=\s*"([^"]+)"',
                attrs,
                re.IGNORECASE
            )

            if head_match and dialogue:

                char_id = (
                    head_match
                    .group(1)
                    .strip()
                    .lower()
                )

                speaker = speaker_names.get(
                    char_id,
                    char_id
                )

                add_dialogue(
                    speaker,
                    dialogue
                )

            continue

        # -------------------------------------------------
        # Diálogo normal
        # -------------------------------------------------

        dialog_match = DIALOG_PATTERN.match(
            line
        )

        if dialog_match:
            speaker = (
                dialog_match
                .group(1)
                .strip()
            )

            dialogue = (
                dialog_match
                .group(2)
                .strip()
            )

            dialogue = re.sub(
                r'Dr\.\s*\{@nickname\}',
                'Doctor',
                dialogue,
                flags=re.IGNORECASE
            )

            if not dialogue:
                continue

            add_dialogue(
                speaker,
                dialogue
            )
        
        stripped_line = line.strip()

        if (
            stripped_line
            and not stripped_line.startswith("[")
            and not stripped_line.startswith("//")
        ):
            add_dialogue(
                "",
                stripped_line
            )

    save_scene()

    return scenes