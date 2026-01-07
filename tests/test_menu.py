from app.services.menu import all_items, load_menu, validate_menu


def test_menu_loads():
    menu = load_menu("menu.json")
    assert len(all_items(menu)) >= 10


def test_menu_validation():
    valid_menu = {"categories": [{"name": "Test", "items": [{"id": "x", "name": "Item"}]}]}
    validate_menu(valid_menu)
