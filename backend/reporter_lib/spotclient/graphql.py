from __future__ import annotations

import gzip
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


DEFAULT_GRAPHQL_URL = "https://san-francisco2-production.spotmobile.net/graphql"

# SF311 allowed ticket type (Blocked driveway and illegal parking).
# Default to this, but allow callers to override via build_payload_from_args().
DEFAULT_TICKET_TYPE_ID = "963f1454-7c22-43be-aacb-3f34ae5d0dc7"

# Copied from reporter.py (kept as the default ExploreQuery payload).
DEFAULT_PAYLOAD: Dict[str, Any] = {
    "operationName": "ExploreQuery",
    "variables": {
        "scope": "recently_opened",
        "order": {
            "by": "distance",
            "direction": "ascending",
            "latitude": 37.7,
            "longitude": -122.4,
        },
        "filters": {
            "ticket_type_id": [DEFAULT_TICKET_TYPE_ID],
            "search": "Parking sidewalk",
        },
        "limit": 200,
    },
    "query": "query ExploreQuery($scope: TicketsScopeEnum, $order: Json, $filters: Json, $limit: Int) {\n"
    "  tickets(first: $limit, scope: $scope, order: $order, filters: $filters) {\n"
    "    nodes {\n"
    "      id\n"
    "      name\n"
    "      status\n"
    "      description\n"
    "      statusLabel\n"
    "      outcomePending\n"
    "      submittedAt\n"
    "      openedAt\n"
    "      closedAt\n"
    "      priority\n"
    "      publicId\n"
    "      bookmarked\n"
    "      photos {\n"
    "        url\n"
    "        __typename\n"
    "      }\n"
    "      location {\n"
    "        address\n"
    "        latitude\n"
    "        longitude\n"
    "        __typename\n"
    "      }\n"
    "      ticketType {\n"
    "        id\n"
    "        name\n"
    # "        color\n"
    # "        icon\n"
    # "        initials\n"
    # "        mapMarkers\n"
    "        __typename\n"
    "      }\n"
    "      __typename\n"
    "    }\n"
    "    pageInfo {\n"
    "      endCursor\n"
    "      hasNextPage\n"
    "      __typename\n"
    "    }\n"
    "    facets {\n"
    "      id\n"
    "      name\n"
    "      field\n"
    "      __typename\n"
    "    }\n"
    "    __typename\n"
    "  }\n"
    "  currentUser {\n"
    "    ...userFragment\n"
    "    remoteLogUntil\n"
    "    __typename\n"
    "  }\n"
    # "  organization {\n"
    # "    ...organizationFragment\n"
    # "    __typename\n"
    # "  }\n"
    "}\n"
    "\n"
    "fragment userFragment on User {\n"
    "  id\n"
    "  name\n"
    "  initials\n"
    "  icon\n"
    "  color\n"
    "  email\n"
    "  __typename\n"
    "}\n"
    "\n"
    # "fragment organizationFragment on Organization {\n"
    # "  id\n"
    # "  name\n"
    # "  color\n"
    # "  colors\n"
    # "  initials\n"
    # "  icon\n"
    # "  heroImage\n"
    # "  heroText\n"
    # "  menuImage\n"
    # "  newReportMessage\n"
    # "  newReportBehavior\n"
    # "  geocoder\n"
    # "  reverseGeocoder\n"
    # "  brandName\n"
    # "  productPageUrl\n"
    # "  supportEmail\n"
    # "  supportEmailSubject\n"
    # "  supportEmailBody\n"
    # "  shareAppSubject\n"
    # "  shareAppBody\n"
    # "  termsOfServiceUrl\n"
    # "  privacyPolicyUrl\n"
    # "  workersBrandName\n"
    # "  workersProductPageUrl\n"
    # "  workersSupportEmail\n"
    # "  workersSupportEmailSubject\n"
    # "  workersSupportEmailBody\n"
    # "  limits\n"
    # "  features\n"
    # "  __typename\n"
    # "}",
}

INTROSPECTION_PAYLOAD: Dict[str, Any] = {
    "operationName": "IntrospectionQuery",
    "variables": {},
    "query": "query IntrospectionQuery {\n"
    "  __schema {\n"
    "    types {\n"
    "      kind\n"
    "      name\n"
    "      description\n"
    "      fields(includeDeprecated: true) {\n"
    "        name\n"
    "        description\n"
    "        isDeprecated\n"
    "        deprecationReason\n"
    "        type {\n"
    "          kind\n"
    "          name\n"
    "        }\n"
    "      }\n"
    "    }\n"
    "  }\n"
    "}\n",
}


class GraphQLHTTPError(RuntimeError):
    def __init__(self, status: int, body: bytes):
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


@dataclass(frozen=True)
class GraphQLResponse:
    status: int
    headers: Dict[str, str]
    body: bytes
    elapsed_ms: int

    def json(self) -> Any:
        return json.loads(self.text())

    def text(self) -> str:
        b = self.body
        if (self.headers.get("Content-Encoding") or "").lower().strip() == "gzip":
            b = gzip.decompress(b)
        return b.decode("utf-8", errors="replace")


def redact(value: Optional[str], keep: int = 10) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "***"
    return f"{value[:keep]}***"


def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_curl(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> str:
    safe_headers = dict(headers)
    if "Authorization" in safe_headers:
        safe_headers["Authorization"] = f"Bearer {redact(safe_headers['Authorization'].replace('Bearer ', ''), keep=12)}"
    if "Cookie" in safe_headers:
        safe_headers["Cookie"] = redact(safe_headers["Cookie"], keep=20)

    parts = ["curl", "-sS", "-X", "POST", repr(url)]
    for k, v in safe_headers.items():
        parts += ["-H", repr(f"{k}: {v}")]
    parts += ["--data-binary", repr(json.dumps(payload))]
    return " ".join(parts)


def build_default_headers(*, cookie: str = "", bearer: str = "") -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Host": "san-francisco2-production.spotmobile.net",
        "x-spot-environment": "Production v6",
        "x-spot-platform": "ios",
        "x-spot-bundleid": "com.connectedbits.sf311",
        "User-Agent": "San Francisco:Production v6:Reporters:ios/6.4.29.5291",
        "x-spot-version": "6.4.29",
        "x-spot-model": "iPhone 15 Pro",
        "x-spot-node_env": "production",
        "x-spot-simulator": "false",
        "x-spot-os": "18.6.2",
        "apollographql-client-name": "San Francisco:Production v6:Reporters:ios",
        "x-spot-installation-id": "6d4478aa-66dc-4bb0-a7cd-1eb09wec401a",
        "apollographql-client-version": "6.4.29.5291",
        "x-spot-tenant": "San Francisco",
        "Accept-Language": "en-US,ja-US,zh-Hans-US,zh-Hant-US",
        "Accept": "*/*",
        # keep gzip for parity with captures; GraphQLResponse.text() will transparently decompress
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
        "x-spot-build": "5291",
        "Connection": "keep-alive",
    }
    if cookie:
        headers["Cookie"] = cookie
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers


def _deepcopy_jsonable(obj: Any) -> Any:
    return json.loads(json.dumps(obj))


def build_payload_from_args(
    *,
    payload_json: Optional[str],
    payload_file: Optional[str],
    search: Optional[str],
    ticket_type_id: Optional[str],
    limit: Optional[int],
    latitude: Optional[float],
    longitude: Optional[float],
    scope: Optional[str],
) -> Dict[str, Any]:
    if payload_json:
        return json.loads(payload_json)
    if payload_file:
        payload = load_json_file(payload_file)
        if not isinstance(payload, dict):
            raise ValueError("--payload-file must contain a JSON object")
        return payload

    payload = _deepcopy_jsonable(DEFAULT_PAYLOAD)
    if search is not None:
        payload["variables"]["filters"]["search"] = search
    if ticket_type_id is not None:
        payload["variables"]["filters"]["ticket_type_id"] = [ticket_type_id]
    if limit is not None:
        payload["variables"]["limit"] = limit
    if latitude is not None:
        payload["variables"]["order"]["latitude"] = latitude
    if longitude is not None:
        payload["variables"]["order"]["longitude"] = longitude
    if scope is not None:
        if scope not in {"recently_opened", "recently_closed"}:
            raise ValueError("--scope must be one of: recently_opened, recently_closed")
        payload["variables"]["scope"] = scope
    return payload


def build_introspection_payload() -> Dict[str, Any]:
    """
    Build an IntrospectionQuery payload without modifying DEFAULT_PAYLOAD.
    """
    return _deepcopy_jsonable(INTROSPECTION_PAYLOAD)


class SpotGraphQLClient:
    def __init__(self, url: str = DEFAULT_GRAPHQL_URL, *, timeout: float = 30.0, insecure: bool = False):
        self.url = url
        self.timeout = timeout
        self.insecure = insecure

        context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
        self._opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))

    def post(self, *, headers: Dict[str, str], payload: Dict[str, Any]) -> GraphQLResponse:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)

        t0 = time.time()
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                body = resp.read()
                hdrs = {k: v for k, v in resp.headers.items()}
                dt_ms = int((time.time() - t0) * 1000)
                return GraphQLResponse(status=resp.getcode(), headers=hdrs, body=body, elapsed_ms=dt_ms)
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            dt_ms = int((time.time() - t0) * 1000)
            hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
            return GraphQLResponse(status=e.code, headers=hdrs, body=body, elapsed_ms=dt_ms)


