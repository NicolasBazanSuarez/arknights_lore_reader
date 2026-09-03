import re

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

    # Estado de las decisiones.
    selected_decision_value = None
    predicate_active = True

    def save_scene():
        if (
            current_background is None
            and not current_dialogues
        ):
            return

        scenes.append({
            "background": (
                current_background
                or "UNKNOWN"
            ),
            "image_type": current_image_type,
            "dialogues": current_dialogues.copy()
        })

    def add_dialogue(
        speaker: str,
        dialogue: str
    ):
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
                save_scene()

                current_background = (
                    image_match
                    .group(1)
                    .strip()
                )

                current_image_type = (
                    scene_match
                    .group("type")
                    .lower()
                )

                current_dialogues = []

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