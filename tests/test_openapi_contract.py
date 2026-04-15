from __future__ import annotations

from app.main import app


def test_questions_api_query_schema_has_no_service_fields() -> None:
    schema = app.openapi()
    parameters = schema["paths"]["/eduportal/questions/questions_api/"]["get"]["parameters"]
    parameter_names = {parameter["name"] for parameter in parameters}

    assert "extra_data" not in parameter_names
    assert parameter_names == {"publicorder", "page_count", "page"}


def test_test_endpoint_documented_as_plain_text() -> None:
    schema = app.openapi()
    responses = schema["paths"]["/eduportal/questions/test/"]["get"]["responses"]["200"]["content"]

    assert "text/plain" in responses
    assert "application/json" not in responses


def test_validation_error_documented_as_legacy_400() -> None:
    schema = app.openapi()
    responses = schema["paths"]["/eduportal/questions/questionslist/"]["post"]["responses"]

    assert "422" not in responses
    assert "400" in responses
    assert (
        responses["400"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/LegacyErrorResponse"
    )
    assert "HTTPValidationError" not in schema["components"]["schemas"]
