from app.services.llm_order_extractor import parse_llm_response


def test_parse_llm_response_json():
    text = '{"order": {"items": []}, "missing_fields": ["items"], "question": "What would you like?"}'
    parsed = parse_llm_response(text)
    assert parsed["missing_fields"] == ["items"]


def test_parse_llm_response_embedded_json():
    text = "Here is the result: {\"order\": {\"items\": []}, \"missing_fields\": [\"items\"], \"question\": \"What would you like?\"}"
    parsed = parse_llm_response(text)
    assert "order" in parsed


def test_parse_llm_response_code_fence():
    text = "```json\n{\"order\": {\"items\": []}, \"missing_fields\": [], \"question\": null}\n```"
    parsed = parse_llm_response(text)
    assert parsed.get("order") == {"items": []}
