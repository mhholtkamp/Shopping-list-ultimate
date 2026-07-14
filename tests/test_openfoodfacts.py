from custom_components.shopping_list_ultimate.openfoodfacts import parse_product


def test_parse_product():
    result = parse_product(
        {
            "status": 1,
            "product": {
                "product_name": "Milk",
                "brands": "Example",
                "quantity": "1 L",
                "categories_tags": ["en:milk"],
                "countries_tags": ["en:netherlands"],
                "image_front_url": "https://example.test/a.jpg",
            },
        },
        "4006381333931",
    )
    assert result["name"] == "Milk"
    assert result["category"] == "milk"
    assert result["source"] == "open_food_facts"


def test_parse_missing_product():
    assert parse_product({"status": 0}, "4006381333931") is None
