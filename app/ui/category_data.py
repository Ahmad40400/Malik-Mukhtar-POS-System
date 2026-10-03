# app/ui/category_data.py
CATEGORY_ICONS = {
    "All": "◆", "Grocery": "▣", "Beverages": "◉",
    "Personal Care": "✿", "Household": "⌂",
    "Electronics": "▤", "Accessories": "◇", "Other": "●",
}


def get_initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "?"


def get_category_icon(category: str) -> str:
    return CATEGORY_ICONS.get(category, "●")