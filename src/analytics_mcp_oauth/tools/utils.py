"""Shared utilities — ported directly from google-analytics-mcp."""

from typing import Any, Dict

import proto


def construct_property_rn(property_value: int | str) -> str:
    """Returns a GA property resource name in the format 'properties/<id>'."""
    property_num = None
    if isinstance(property_value, int):
        property_num = property_value
    elif isinstance(property_value, str):
        property_value = property_value.strip()
        if property_value.isdigit():
            property_num = int(property_value)
        elif property_value.startswith("properties/"):
            numeric_part = property_value.split("/")[-1]
            if numeric_part.isdigit():
                property_num = int(numeric_part)

    if property_num is None:
        raise ValueError(
            f"Invalid property ID: {property_value!r}. "
            "Expected a number or 'properties/<number>'."
        )
    return f"properties/{property_num}"


def proto_to_dict(obj: proto.Message) -> Dict[str, Any]:
    """Converts a proto-plus message to a plain dict."""
    return type(obj).to_dict(
        obj, use_integers_for_enums=False, preserving_proto_field_name=True
    )


def proto_to_json(obj: proto.Message) -> str:
    """Converts a proto-plus message to a compact JSON string."""
    return type(obj).to_json(obj, indent=None, preserving_proto_field_name=True)
