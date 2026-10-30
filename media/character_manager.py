from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw

ALPHA_THRESHOLD = 24

TOP_DENSITY_RATIO = 0.18
SIDE_DENSITY_RATIO = 0.22

HEAD_SCAN_HEIGHT_RATIO = 0.22
SMOOTH_WINDOW = 7

CROP_MARGIN_RATIO = 1.28
TOP_PADDING_RATIO = 0.10

MIN_CROP_RATIO = 0.26
MAX_CROP_RATIO = 0.52

_CHARACTER_CROP_CACHE = {}

CHARACTER_BASE_URL = (
    "https://arknights.timo.beer/"
    "game/en/avg/characters"
)

ASSETS_DIR = Path("assets")

CHARACTERS_DIR = (
    Path("assets")
    / "scene_images"
    / "characters"
)

SPEAKER_PORTRAITS_DIR = (
    ASSETS_DIR
    / "scene_images"
    / "speaker_portraits"
)


def parse_character_asset_name(
    raw_name: str
) -> tuple[str, int, int]:
    raw_name = raw_name.strip()

    if "#" not in raw_name or "$" not in raw_name:
        return (
            raw_name,
            1,
            1
        )

    base_name, variant_part = raw_name.split(
        "#",
        1
    )

    expression, subvariant = variant_part.split(
        "$",
        1
    )

    return (
        base_name,
        int(expression),
        int(subvariant)
    )


def build_character_filename(
    base_name: str,
    expression: int = 1,
    subvariant: int = 1
) -> str:
    return (
        f"{base_name}"
        f"#{expression}"
        f"${subvariant}.webp"
    )


def get_scene_character_image(
    base_name: str
) -> Path:
    CHARACTERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_base_name = base_name.lower()

    filename = build_character_filename(
        base_name=normalized_base_name,
        expression=1,
        subvariant=1
    )

    local_filename = (
        f"{normalized_base_name}__1_1.webp"
    )

    destination = (
        CHARACTERS_DIR
        / local_filename
    )

    if destination.exists():
        return destination

    encoded_filename = quote(
        filename,
        safe=""
    )

    url = (
        f"{CHARACTER_BASE_URL}/"
        f"{encoded_filename}"
    )

    response = requests.get(
        url,
        timeout=30
    )
    response.raise_for_status()

    destination.write_bytes(
        response.content
    )

    return destination

def get_speaker_portrait(
    base_name: str,
    size: int = 192
) -> Path:
    SPEAKER_PORTRAITS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_id = (
        normalize_character_variant(
            base_name
        )
    )

    safe_name = (
        normalized_id
        .replace("#", "__")
        .replace("$", "_")
    )

    destination = (
        SPEAKER_PORTRAITS_DIR
        / f"{safe_name}_{size}.png"
    )

    if destination.exists():
        return destination

    source_image_path = (
        get_character_variant_image(
            base_name
        )
    )

    image = Image.open(
        source_image_path
    ).convert("RGBA")

    crop_x_ratio, crop_y_ratio, crop_size_ratio = (
        analyze_character_crop(
            base_name
        )
    )

    width, height = image.size
    base_dimension = min(
        width,
        height
    )

    crop_size = int(
        base_dimension
        * crop_size_ratio
    )

    crop_x = int(
        width * crop_x_ratio
    )

    crop_y = int(
        height * crop_y_ratio
    )

    crop_x = max(
        0,
        min(
            crop_x,
            width - crop_size
        )
    )

    crop_y = max(
        0,
        min(
            crop_y,
            height - crop_size
        )
    )

    cropped = image.crop(
        (
            crop_x,
            crop_y,
            crop_x + crop_size,
            crop_y + crop_size
        )
    )

    resized = cropped.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    mask = Image.new(
        "L",
        (size, size),
        0
    )

    draw = ImageDraw.Draw(mask)

    draw.ellipse(
        (
            0,
            0,
            size - 1,
            size - 1
        ),
        fill=255
    )

    portrait = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    portrait.paste(
        resized,
        (0, 0),
        mask
    )

    portrait.save(
        destination
    )

    return destination

def normalize_character_variant(
    character_id: str
) -> str:
    character_id = (
        character_id
        .strip()
        .lower()
    )

    has_variant = "#" in character_id
    has_subvariant = "$" in character_id

    # avg_xxx#4$2
    if has_variant and has_subvariant:
        return character_id

    # avg_xxx#4
    # -> avg_xxx#4$1
    if has_variant:
        return f"{character_id}$1"

    # avg_xxx$2
    # -> avg_xxx#1$2
    if has_subvariant:
        base_id, subvariant = (
            character_id.split(
                "$",
                1
            )
        )

        return (
            f"{base_id}"
            f"#1"
            f"${subvariant}"
        )

    # avg_xxx
    # -> avg_xxx#1$1
    return f"{character_id}#1$1"

def get_base_character_id(
    character_id: str
) -> str:
    normalized = normalize_character_variant(
        character_id
    )

    return normalized.split(
        "#",
        1
    )[0]


def get_neutral_character_variant(
    character_id: str
) -> str:
    base_id = get_base_character_id(
        character_id
    )

    return f"{base_id}#1$1"


def smooth_values(
    values: list[int],
    window: int
) -> list[float]:
    if window <= 1:
        return [float(v) for v in values]

    radius = window // 2
    smoothed = []

    for index in range(
        len(values)
    ):
        start = max(
            0,
            index - radius
        )
        end = min(
            len(values),
            index + radius + 1
        )

        chunk = values[start:end]

        smoothed.append(
            sum(chunk) / len(chunk)
        )

    return smoothed


def find_first_index_over_threshold(
    values: list[float],
    threshold: float
) -> int:
    for index, value in enumerate(
        values
    ):
        if value >= threshold:
            return index

    return 0


def find_last_index_over_threshold(
    values: list[float],
    threshold: float
) -> int:
    for index in range(
        len(values) - 1,
        -1,
        -1
    ):
        if values[index] >= threshold:
            return index

    return len(values) - 1


def analyze_character_crop(
    character_id: str
) -> tuple[float, float, float]:
    base_id = get_base_character_id(
        character_id
    )

    cached = _CHARACTER_CROP_CACHE.get(
        base_id
    )

    if cached is not None:
        return cached

    reference_variant = (
        get_neutral_character_variant(
            character_id
        )
    )

    try:
        reference_path = (
            get_character_variant_image(
                reference_variant
            )
        )
    except Exception:
        reference_path = (
            get_character_variant_image(
                character_id
            )
        )

    with Image.open(
        reference_path
    ) as img:
        image = img.convert("RGBA")

    width, height = image.size

    alpha = image.getchannel("A")

    row_counts = []

    for y in range(height):
        row = alpha.crop(
            (0, y, width, y + 1)
        )

        occupied = sum(
            1
            for value in row.getdata()
            if value >= ALPHA_THRESHOLD
        )

        row_counts.append(
            occupied
        )

    max_row_density = max(
        row_counts,
        default=0
    )

    top_threshold = max(
        1,
        int(
            max_row_density
            * TOP_DENSITY_RATIO
        )
    )

    top_y = find_first_index_over_threshold(
        row_counts,
        top_threshold
    )

    head_scan_height = max(
        48,
        int(
            height
            * HEAD_SCAN_HEIGHT_RATIO
        )
    )

    scan_bottom = min(
        height,
        top_y + head_scan_height
    )

    column_counts = []

    for x in range(width):
        column = alpha.crop(
            (
                x,
                top_y,
                x + 1,
                scan_bottom
            )
        )

        occupied = sum(
            1
            for value in column.getdata()
            if value >= ALPHA_THRESHOLD
        )

        column_counts.append(
            occupied
        )

    smoothed_columns = smooth_values(
        column_counts,
        SMOOTH_WINDOW
    )

    max_column_density = max(
        smoothed_columns,
        default=0
    )

    side_threshold = max(
        1,
        max_column_density
        * SIDE_DENSITY_RATIO
    )

    left_x = find_first_index_over_threshold(
        smoothed_columns,
        side_threshold
    )

    right_x = find_last_index_over_threshold(
        smoothed_columns,
        side_threshold
    )

    if right_x <= left_x:
        left_x = int(width * 0.30)
        right_x = int(width * 0.70)

    detected_width = (
        right_x - left_x + 1
    )

    crop_size = int(
        detected_width
        * CROP_MARGIN_RATIO
    )

    base_dimension = min(
        width,
        height
    )

    crop_size = max(
        crop_size,
        int(
            base_dimension
            * MIN_CROP_RATIO
        )
    )

    crop_size = min(
        crop_size,
        int(
            base_dimension
            * MAX_CROP_RATIO
        )
    )

    center_x = (
        left_x + right_x
    ) // 2

    crop_x = (
        center_x
        - crop_size // 2
    )

    crop_y = (
        top_y
        - int(
            crop_size
            * TOP_PADDING_RATIO
        )
    )

    crop_x = max(
        0,
        min(
            crop_x,
            width - crop_size
        )
    )

    crop_y = max(
        0,
        min(
            crop_y,
            height - crop_size
        )
    )

    result = (
        crop_x / width,
        crop_y / height,
        crop_size / base_dimension
    )

    _CHARACTER_CROP_CACHE[
        base_id
    ] = result

    return result

def get_character_variant_image(
    character_id: str
) -> Path:
    CHARACTERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_id = (
        normalize_character_variant(
            character_id
        )
    )

    safe_name = (
        normalized_id
        .replace("#", "__")
        .replace("$", "_")
    )

    destination = (
        CHARACTERS_DIR
        / f"{safe_name}.webp"
    )

    if destination.exists():
        return destination

    filename = (
        f"{normalized_id}.webp"
    )

    encoded_filename = quote(
        filename,
        safe=""
    )

    url = (
        f"{CHARACTER_BASE_URL}/"
        f"{encoded_filename}"
    )

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    destination.write_bytes(
        response.content
    )

    return destination