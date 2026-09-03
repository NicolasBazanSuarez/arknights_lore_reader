def get_story_chapters(
    group_id: str,
    group: dict,
    catalog: dict
) -> list[dict]:

    category = group.get(
        "category"
    )

    if category in {
        "main",
        "side",
        "mini"
    }:
        return get_review_chapters(
            group_id,
            catalog
        )

    if category == "rogue":
        return get_rogue_chapters(
            group_id,
            group,
            catalog
        )

    if category == "sandbox":
        return get_sandbox_chapters(
            group_id,
            group,
            catalog
        )

    if category == "extra":
        return get_extra_chapters(
            group_id,
            group,
            catalog
        )

    return []


def get_review_chapters(
    group_id: str,
    catalog: dict
) -> list[dict]:

    review = catalog.get(
        "review",
        {}
    )

    story_group = review.get(
        group_id
    )

    if not story_group:
        return []

    chapters = story_group.get(
        "infoUnlockDatas",
        []
    )

    return sorted(
        chapters,
        key=lambda chapter: chapter.get(
            "storySort",
            0
        )
    )


def get_rogue_chapters(
    group_id: str,
    group: dict,
    catalog: dict
) -> list[dict]:

    rogue = catalog.get(
        "rogue",
        {}
    )

    # ---------------------------------
    # IS#1 - Ceobe's Fungimist
    # ---------------------------------

    if group_id == "rogue_0":
        return [
            {
                "storyName": "Prologue",
                "storyTxt": (
                    "activities/act12d6/"
                    "level_act12d6_entry"
                )
            },
            {
                "storyName": "Dust of Dreams",
                "storyTxt": (
                    "activities/act12d6/"
                    "level_act12d6_ending_1"
                )
            },
            {
                "storyName": "Perplexed Traveler",
                "storyTxt": (
                    "activities/act12d6/"
                    "level_act12d6_ending_2"
                )
            },
            {
                "storyName": "Return to the Wilds",
                "storyTxt": (
                    "activities/act12d6/"
                    "level_act12d6_ending_3"
                )
            }
        ]

    topics = rogue.get(
        "topics",
        {}
    )

    details = rogue.get(
        "details",
        {}
    )

    if group_id not in topics:
        return []

    detail = details.get(
        group_id
    )

    if not detail:
        return []

    rogue_number = group_id.split(
        "_",
        1
    )[1]

    chapters = []

    # ---------------------------------
    # Prólogo
    # ---------------------------------

    prologue = (
        f"obt/roguelike/ro{rogue_number}/"
        f"level_rogue{rogue_number}_entry"
    )

    if has_story(
        prologue,
        catalog
    ):
        chapters.append({
            "storyName": "Prologue",
            "storyTxt": prologue
        })

    # ---------------------------------
    # Endings / Endbook
    # ---------------------------------

    archive_comp = detail.get(
        "archiveComp",
        {}
    )

    endbook = (
        archive_comp
        .get("endbook", {})
        .get("endbook", {})
    )

    if not endbook:

        # rogue_1 no tiene Endbook.
        endings = detail.get(
            "endings",
            {}
        )

        for ending_id, ending in endings.items():

            ending_number = (
                ending_id
                .rsplit("_", 1)[-1]
            )

            chapters.append({
                "storyName": ending.get(
                    "name",
                    f"Ending {ending_number}"
                ),
                "storyTxt": (
                    f"obt/roguelike/"
                    f"ro{rogue_number}/"
                    f"level_rogue"
                    f"{rogue_number}_ending_"
                    f"{ending_number}"
                )
            })

    else:

        for ending in endbook.values():

            ending_title = ending.get(
                "title",
                "Ending"
            )

            avg_id = ending.get(
                "avgId"
            )

            if avg_id:
                chapters.append({
                    "storyName": ending_title,
                    "storyTxt": avg_id.lower()
                })

            endbook_items = ending.get(
                "clientEndbookItemDatas",
                {}
            )

            for item in endbook_items.values():

                text_id = item.get(
                    "textId"
                )

                if not text_id:
                    continue

                item_name = item.get(
                    "endbookName",
                    ""
                )

                chapters.append({
                    "storyName": (
                        f"{ending_title} - "
                        f"{item_name}"
                    ),
                    "storyTxt": text_id.lower(),
                    "storyBackground": (
                        ending.get("cgId")
                    )
                })

    # ---------------------------------
    # Monthly Squads
    # ---------------------------------

    month_squads = detail.get(
        "monthSquad",
        {}
    )

    chats = (
        archive_comp
        .get("chat", {})
        .get("chat", {})
    )

    for month_number, squad in enumerate(
        month_squads.values(),
        start=1
    ):

        team_name = squad.get(
            "teamName",
            f"Monthly Squad {month_number}"
        )

        chat_id = squad.get(
            "chatId"
        )

        if not chat_id:
            continue

        chat = chats.get(
            chat_id,
            {}
        )

        items = (
            chat.get("clientChatItemData")
            or chat.get("chatItemList")
            or {}
        )

        for item in items.values():

            story_txt = item.get(
                "chatStoryId"
            )

            if not story_txt:
                continue

            floor = item.get(
                "chatFloor"
            )

            if floor is None:
                floor = item.get(
                    "floor"
                )

            chapters.append({
                "storyName": (
                    f"M{month_number} - "
                    f"{team_name} - "
                    f"Floor {floor}"
                ),
                "storyTxt": (
                    story_txt.lower()
                ),
                "storyBackground": (
                    f"pic_{group_id}_1"
                )
            })

    return chapters


def get_sandbox_chapters(
    group_id: str,
    group: dict,
    catalog: dict
) -> list[dict]:

    # Lo implementaremos después.
    return []


def get_extra_chapters(
    group_id: str,
    group: dict,
    catalog: dict
) -> list[dict]:

    # Lo implementaremos después.
    return []

def has_story(
    path: str,
    catalog: dict
) -> bool:

    story_keys = catalog.get(
        "storyKeys",
        []
    )

    normalized_path = path.lower()

    return any(
        key.lower() == normalized_path
        for key in story_keys
    )
    
def build_speaker_names(
    catalog: dict
) -> dict[str, str]:

    names = {}

    # ---------------------------------
    # Operators
    # ---------------------------------

    for char_id, data in catalog.get(
        "ops",
        {}
    ).items():

        if not isinstance(
            data,
            list
        ):
            continue

        if not data:
            continue

        name = data[0]

        if not name and len(data) > 1:
            name = data[1]

        if name:
            names[
                char_id.lower()
            ] = name.strip()

    # ---------------------------------
    # Voice index como fallback
    # ---------------------------------

    for char_id, data in catalog.get(
        "voices",
        {}
    ).items():

        if not isinstance(
            data,
            dict
        ):
            continue

        name = data.get(
            "name"
        )

        if name:
            names.setdefault(
                char_id.lower(),
                name.strip()
            )

    return names