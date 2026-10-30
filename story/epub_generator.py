import hashlib
import io
import re
import uuid
import zipfile
from datetime import datetime, timezone
from html import escape, unescape
from pathlib import Path

from PIL import Image

from story.html_generator import generate_story_html

EPUB_STYLE_PATH = (
    Path(__file__).parent
    / "styles"
    / "epub.css"
)

COVERS_FOLDER = Path("assets/covers")

IMAGE_SRC_PATTERN = re.compile(
    r'(<img\b[^>]*\bsrc=")([^"]+)(")',
    re.IGNORECASE
)

IMG_TAG_PATTERN = re.compile(
    r'<img\b([^>]*?)(?<!/)>',
    re.IGNORECASE
)


def _extract_body(
    html: str
) -> str:
    if (
        "<body>" not in html
        or "</body>" not in html
    ):
        return ""

    return (
        html
        .split("<body>", 1)[1]
        .split("</body>", 1)[0]
        .strip()
    )


def _prepare_image(
    source_path: Path
) -> tuple[bytes, str, str]:

    suffix = source_path.suffix.lower()

    if suffix == ".webp":

        with Image.open(
            source_path
        ) as image:

            has_transparency = False

            if "A" in image.getbands():
                alpha = image.getchannel("A")

                alpha_min, _ = (
                    alpha.getextrema()
                )

                has_transparency = (
                    alpha_min < 255
                )

            output = io.BytesIO()

            if has_transparency:

                image.convert(
                    "RGBA"
                ).save(
                    output,
                    format="PNG",
                    optimize=True
                )

                return (
                    output.getvalue(),
                    ".png",
                    "image/png"
                )

            image.convert(
                "RGB"
            ).save(
                output,
                format="JPEG",
                quality=90,
                optimize=True
            )

            return (
                output.getvalue(),
                ".jpg",
                "image/jpeg"
            )

    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
    }

    media_type = media_types.get(
        suffix
    )

    if media_type is None:
        raise ValueError(
            "Formato de imagen no "
            "soportado en EPUB: "
            f"{source_path}"
        )

    return (
        source_path.read_bytes(),
        suffix,
        media_type
    )


def _embed_images(
    html: str,
    story_folder: Path,
    embedded_images: dict
) -> str:

    def replace(
        match: re.Match
    ) -> str:

        source = unescape(
            match.group(2)
        )

        if source.startswith(
            (
                "http://",
                "https://",
                "data:"
            )
        ):
            return match.group(0)

        source_path = (
            story_folder
            / source
        ).resolve()

        if not source_path.exists():
            return match.group(0)

        image_info = (
            embedded_images.get(
                source_path
            )
        )

        if image_info is None:

            (
                image_bytes,
                extension,
                media_type
            ) = _prepare_image(
                source_path
            )

            digest = hashlib.sha1(
                str(
                    source_path
                ).encode("utf-8")
            ).hexdigest()[:12]

            internal_path = (
                f"images/{digest}"
                f"{extension}"
            )

            image_info = {
                "id": f"img_{digest}",
                "path": internal_path,
                "media_type": media_type,
                "content": image_bytes
            }

            embedded_images[
                source_path
            ] = image_info

        return (
            f'{match.group(1)}'
            f'../{image_info["path"]}'
            f'{match.group(3)}'
        )

    html = IMAGE_SRC_PATTERN.sub(
        replace,
        html
    )

    # EPUB usa XHTML.
    # Convertimos:
    #
    # <img ...>
    #
    # en:
    #
    # <img ... />
    return IMG_TAG_PATTERN.sub(
        r'<img\1 />',
        html
    )


def _chapter_xhtml(
    title: str,
    body: str,
    language: str
) -> str:

    safe_title = escape(
        title,
        quote=True
    )

    return f'''<?xml version="1.0" encoding="utf-8"?>
<html
    xmlns="http://www.w3.org/1999/xhtml"
    lang="{language}"
    xml:lang="{language}"
>
<head>
    <meta charset="utf-8" />

    <title>
        {safe_title}
    </title>

    <link
        rel="stylesheet"
        type="text/css"
        href="../styles/epub.css"
    />
</head>

<body>
{body}
</body>

</html>
'''


def _cover_xhtml(
    story_title: str,
    image_path: str,
    language: str
) -> str:

    safe_title = escape(
        story_title,
        quote=True
    )

    return f'''<?xml version="1.0" encoding="utf-8"?>
<html
    xmlns="http://www.w3.org/1999/xhtml"
    lang="{language}"
    xml:lang="{language}"
>
<head>
    <meta charset="utf-8" />

    <title>
        {safe_title}
    </title>

    <style type="text/css">
        body {{
            margin: 0;
            padding: 0;
            text-align: center;
        }}

        img {{
            max-width: 100%;
            max-height: 100%;
        }}
    </style>
</head>

<body>
    <div>
        <img
            src="{image_path}"
            alt="{safe_title}"
        />
    </div>
</body>

</html>
'''


def _nav_xhtml(
    story_title: str,
    chapters: list[dict],
    language: str
) -> str:

    links = []

    for chapter in chapters:

        links.append(
            "<li>"
            f'<a href="text/'
            f'{chapter["filename"]}">'
            f'{escape(chapter["title"])}'
            "</a>"
            "</li>"
        )

    return f'''<?xml version="1.0" encoding="utf-8"?>
<html
    xmlns="http://www.w3.org/1999/xhtml"
    xmlns:epub="http://www.idpf.org/2007/ops"
    lang="{language}"
    xml:lang="{language}"
>
<head>
    <meta charset="utf-8" />

    <title>
        {escape(story_title)}
    </title>
</head>

<body>

    <nav
        epub:type="toc"
        id="toc"
    >
        <h1>
            {escape(story_title)}
        </h1>

        <ol>
            {''.join(links)}
        </ol>

    </nav>

</body>

</html>
'''


def _content_opf(
    story_title: str,
    identifier: str,
    language: str,
    chapters: list[dict],
    images: list[dict],
    has_cover: bool
) -> str:

    manifest = [
        (
            '<item id="nav" '
            'href="nav.xhtml" '
            'media-type="application/xhtml+xml" '
            'properties="nav" />'
        ),
        (
            '<item id="css" '
            'href="styles/epub.css" '
            'media-type="text/css" />'
        )
    ]

    spine = []

    if has_cover:

        manifest.append(
            '<item id="cover-page" '
            'href="cover.xhtml" '
            'media-type="application/xhtml+xml" />'
        )

        spine.append(
            '<itemref idref="cover-page" />'
        )

    for chapter in chapters:

        manifest.append(
            f'<item id="{chapter["id"]}" '
            f'href="text/{chapter["filename"]}" '
            'media-type="application/xhtml+xml" />'
        )

        spine.append(
            f'<itemref idref="{chapter["id"]}" />'
        )

    for image in images:

        properties = (
            ' properties="cover-image"'
            if image.get("cover")
            else ""
        )

        manifest.append(
            f'<item id="{image["id"]}" '
            f'href="{image["path"]}" '
            f'media-type="{image["media_type"]}"'
            f'{properties} />'
        )

    modified = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    return f'''<?xml version="1.0" encoding="utf-8"?>
<package
    xmlns="http://www.idpf.org/2007/opf"
    version="3.0"
    unique-identifier="book-id"
>

    <metadata
        xmlns:dc="http://purl.org/dc/elements/1.1/"
    >
        <dc:identifier id="book-id">
            {escape(identifier)}
        </dc:identifier>

        <dc:title>
            {escape(story_title)}
        </dc:title>

        <dc:language>
            {escape(language)}
        </dc:language>

        <meta property="dcterms:modified">
            {modified}
        </meta>
    </metadata>

    <manifest>
        {''.join(manifest)}
    </manifest>

    <spine>
        {''.join(spine)}
    </spine>

</package>
'''


def generate_story_epub(
    story_folder: Path,
    story_title: str,
    cover_name: str | None,
    chapters: list[dict],
    language: str = "es"
) -> Path | None:

    if not chapters:
        return None

    embedded_images = {}
    epub_chapters = []

    for index, chapter in enumerate(
        chapters,
        start=1
    ):

        chapter_html = generate_story_html(
            scenes=chapter["scenes"],
            chapter_folder=story_folder,
            chapter_title=chapter["title"]
        )

        chapter_body = _extract_body(
            chapter_html
        )

        chapter_body = _embed_images(
            html=chapter_body,
            story_folder=story_folder,
            embedded_images=embedded_images
        )

        filename = (
            f"chapter_{index:03d}.xhtml"
        )

        epub_chapters.append({
            "id": (
                f"chapter_{index:03d}"
            ),

            "filename": filename,

            "title": chapter["title"],

            "content": _chapter_xhtml(
                title=chapter["title"],
                body=chapter_body,
                language=language
            )
        })

    cover_info = None

    if cover_name:

        cover_path = (
            COVERS_FOLDER
            / cover_name
        )

        if cover_path.exists():

            (
                cover_bytes,
                cover_extension,
                cover_media_type
            ) = _prepare_image(
                cover_path
            )

            cover_info = {
                "id": "cover-image",

                "path": (
                    f"images/cover"
                    f"{cover_extension}"
                ),

                "media_type": (
                    cover_media_type
                ),

                "content": (
                    cover_bytes
                ),

                "cover": True
            }

    images = list(
        embedded_images.values()
    )

    if cover_info:
        images.append(
            cover_info
        )

    identifier = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"arknights:{story_title}"
        )
    )

    destination = (
        story_folder
        / f"{story_title}.epub"
    )

    container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container
    version="1.0"
    xmlns="urn:oasis:names:tc:opendocument:xmlns:container"
>
    <rootfiles>
        <rootfile
            full-path="OEBPS/content.opf"
            media-type="application/oebps-package+xml"
        />
    </rootfiles>
</container>
'''

    nav_xhtml = _nav_xhtml(
        story_title=story_title,
        chapters=epub_chapters,
        language=language
    )

    content_opf = _content_opf(
        story_title=story_title,
        identifier=identifier,
        language=language,
        chapters=epub_chapters,
        images=images,
        has_cover=(
            cover_info is not None
        )
    )

    stylesheet = (
        EPUB_STYLE_PATH.read_bytes()
    )

    with zipfile.ZipFile(
        destination,
        "w"
    ) as archive:

        # Debe ser el primer fichero del EPUB
        # y debe ir sin compresión.
        archive.writestr(
            "mimetype",
            "application/epub+zip",
            compress_type=(
                zipfile.ZIP_STORED
            )
        )

        archive.writestr(
            "META-INF/container.xml",
            container_xml,
            compress_type=(
                zipfile.ZIP_DEFLATED
            )
        )

        archive.writestr(
            "OEBPS/content.opf",
            content_opf,
            compress_type=(
                zipfile.ZIP_DEFLATED
            )
        )

        archive.writestr(
            "OEBPS/nav.xhtml",
            nav_xhtml,
            compress_type=(
                zipfile.ZIP_DEFLATED
            )
        )

        archive.writestr(
            "OEBPS/styles/epub.css",
            stylesheet,
            compress_type=(
                zipfile.ZIP_DEFLATED
            )
        )

        if cover_info:

            cover_page = _cover_xhtml(
                story_title=story_title,
                image_path=(
                    cover_info["path"]
                ),
                language=language
            )

            archive.writestr(
                "OEBPS/cover.xhtml",
                cover_page,
                compress_type=(
                    zipfile.ZIP_DEFLATED
                )
            )

        for chapter in epub_chapters:

            archive.writestr(
                (
                    "OEBPS/text/"
                    f"{chapter['filename']}"
                ),
                chapter["content"],
                compress_type=(
                    zipfile.ZIP_DEFLATED
                )
            )

        for image in images:

            archive.writestr(
                (
                    "OEBPS/"
                    f"{image['path']}"
                ),
                image["content"],
                compress_type=(
                    zipfile.ZIP_DEFLATED
                )
            )

    return destination