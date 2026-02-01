"""
spotclient: tiny stdlib-only client utilities for Spotmobile (SF311).

- `spotclient.graphql` provides a GraphQL POST client + helpers for headers/payloads
"""

from .graphql import (  # noqa: F401
    DEFAULT_GRAPHQL_URL,
    DEFAULT_PAYLOAD,
    INTROSPECTION_PAYLOAD,
    GraphQLHTTPError,
    SpotGraphQLClient,
    build_default_headers,
    build_payload_from_args,
    build_introspection_payload,
    load_json_file,
    redact,
    to_curl,
)


