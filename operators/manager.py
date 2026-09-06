def get_operator_data(
    operator_id: str,
    operator_name: str,
    catalog: dict,
    files_data: dict,
    modules_data: dict
) -> dict:

    operator_files = []

    # ---------------------------------
    # Archivos del operador
    # ---------------------------------

    for entry in files_data.get(
        operator_id,
        []
    ):

        if (
            not isinstance(entry, list)
            or len(entry) < 2
        ):
            continue

        title = entry[0]
        text = entry[1]

        operator_files.append({
            "title": title,
            "text": text
        })

    # ---------------------------------
    # Módulos
    # ---------------------------------

    equip = catalog.get(
        "equip",
        {}
    )

    char_equip = equip.get(
        "charEquip",
        {}
    )

    equip_dict = equip.get(
        "equipDict",
        {}
    )

    module_ids = char_equip.get(
        operator_id,
        []
    )

    operator_modules = []

    for module_id in module_ids:

        equip_info = equip_dict.get(
            module_id,
            {}
        )

        module_info = modules_data.get(
            module_id,
            {}
        )

        operator_modules.append({
            "id": module_id,

            "name": equip_info.get(
                "uniEquipName",
                module_id
            ),

            "description": module_info.get(
                "uniEquipDesc",
                ""
            ),

            "icon": module_info.get(
                "uniEquipIcon"
            ),

            "type": equip_info.get(
                "typeName1"
            ),

            "variant": equip_info.get(
                "typeName2"
            )
        })

    return {
        "id": operator_id,
        "name": operator_name,
        "files": operator_files,
        "modules": operator_modules,
        "stories": get_operator_stories(
            operator_id=operator_id,
            catalog=catalog
        )
    }
    
def get_operator_stories(
    operator_id: str,
    catalog: dict
) -> list[dict]:

    parts = operator_id.split(
        "_",
        2
    )

    if len(parts) < 3:
        return []

    short_name = parts[2]

    review = catalog.get(
        "review",
        {}
    )

    prefix = (
        f"story_{short_name}_set_"
    )

    story_groups = []

    for group_id, story_group in (
        review.items()
    ):

        if not group_id.startswith(
            prefix
        ):
            continue

        suffix = group_id[
            len(prefix):
        ]

        if not suffix.isdigit():
            continue

        story_groups.append(
            (
                int(suffix),
                group_id,
                story_group
            )
        )

    story_groups.sort(
        key=lambda item: item[0]
    )

    stories = []

    for (
        set_number,
        group_id,
        story_group
    ) in story_groups:

        chapters = []

        info_unlock_datas = (
            story_group.get(
                "infoUnlockDatas",
                []
            )
        )

        for chapter in sorted(
            info_unlock_datas,
            key=lambda item: item.get(
                "storySort",
                0
            )
        ):

            story_txt = chapter.get(
                "storyTxt"
            )

            if not story_txt:
                continue

            chapters.append({
                "name": chapter.get(
                    "storyName",
                    story_group.get(
                        "name",
                        group_id
                    )
                ),
                "storyTxt": story_txt
            })

        stories.append({
            "id": group_id,
            "set": set_number,
            "name": story_group.get(
                "name",
                group_id
            ),
            "chapters": chapters
        })

    return stories