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


def parse_story_text(text: str) -> list[dict]:
    scenes = []

    current_background = None
    current_image_type = None
    current_dialogues = []

    def save_scene():
        if current_background is None and not current_dialogues:
            return

        scenes.append({
            "background": current_background or "UNKNOWN",
            "image_type": current_image_type,
            "dialogues": current_dialogues.copy()
        })

    for line in text.splitlines():
        scene_match = SCENE_PATTERN.match(line)

        if scene_match:
            attrs = scene_match.group("attrs")
            image_match = IMAGE_ATTR_PATTERN.search(attrs)

            if image_match:
                save_scene()

                current_background = image_match.group(1).strip()
                current_image_type = scene_match.group("type").lower()
                current_dialogues = []

            continue

        dialog_match = DIALOG_PATTERN.match(line)

        if dialog_match:
            speaker = dialog_match.group(1).strip()
            dialogue = dialog_match.group(2).strip()
            
            dialogue = re.sub(
                r'Dr\.\s*\{@nickname\}',
                'Doctor',
                dialogue,
                flags=re.IGNORECASE
            )

            if not dialogue:
                continue

            if (
                current_dialogues
                and current_dialogues[-1]["speaker"] == speaker
            ):
                current_dialogues[-1]["lines"].append(dialogue)

            else:
                current_dialogues.append({
                    "speaker": speaker,
                    "lines": [dialogue]
                })

    save_scene()

    return scenes