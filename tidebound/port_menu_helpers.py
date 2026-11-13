from .ship_fittings import CUSTOMISATION_CATEGORIES


def outfitter_detail_lines(selected_item, ship):
    values = [f"Installed on: {ship.get('name', 'Vessel')} ({ship.get('type', 'Unknown class')})"]
    item_kind = selected_item.get("kind", "upgrade")
    if item_kind == "customisation":
        category_titles = {key: title for key, title, _ in CUSTOMISATION_CATEGORIES}
        category = selected_item.get("category", "")
        values.extend((
            f"Category: {category_titles.get(category, category.replace('_', ' ').title())}",
            f"Fitting: {selected_item.get('option', 'Unknown fitting')}",
            "Already installed" if selected_item.get("installed", False) else f"Installation: {int(selected_item.get('cost', 0)):,} gold",
        ))
    elif item_kind == "cannon_pair":
        cannon_type = selected_item.get("cannon_type", "Cannon")
        source_type = selected_item.get("source_type")
        values.extend((
            f"Cannon type: {cannon_type}",
            f"Replacement: {source_type}" if source_type else "No compatible pair available to replace",
            f"Installation: {int(selected_item.get('cost', 0)):,} gold",
        ))
    elif item_kind == "upgrade":
        level = int(selected_item.get("level", 0))
        limit = int(selected_item.get("limit", 0))
        values.extend((
            f"Current level: {level}/{limit}",
            f"Next installation: {int(selected_item.get('cost', 0)):,} gold",
        ))
    else:
        values.append(str(selected_item.get("detail", "A shipwright's fitting.")))
    return values
