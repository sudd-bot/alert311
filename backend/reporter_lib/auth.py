#!/usr/bin/env python3
"""
Replicate Spot "authorization_code" flow observed in RawIpad logs to obtain:
  - access_token (JWT, used as `Authorization: Bearer ...`)
  - refresh_token
  - id_token (optional)

Flow (as captured):
  1) GET  /auth?...&client_id=...&redirect_uri=sf311://auth&response_type=code
     - receives HTML with a form POSTing to /auth/convey and a _spot_session cookie
  2) POST /auth/convey with hidden form fields + session cookie
     - 302 Location: /auth/callback?auth=...
  3) GET  /auth/callback?auth=...
     - 302 Location: sf311://auth?code=<uuid>
  4) POST /auth/token with JSON: { code, redirect_uri, client_id, grant_type: authorization_code }
     - 200 JSON: { token_type, access_token, refresh_token, id_token, expires_in, scope }

This script uses ONLY the Python standard library (no requests dependency).

Security note:
  - Tokens are sensitive. By default this prints them to stdout.
    Prefer using --out to write JSON to a file you can protect.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from typing import Any, Dict, Optional, Tuple


DEFAULT_BASE_URL = "https://san-francisco2-production.spotmobile.net"
DEFAULT_CLIENT_ID = "60c3c1d3-0ebe-49f4-97a8-4f4272120366"
DEFAULT_REDIRECT_URI = "sf311://auth"
DEFAULT_SCOPE = "refresh_token read write openid"


class NonHttpRedirect(Exception):
    def __init__(self, location: str):
        super().__init__(f"Redirected to non-http(s) location: {location}")
        self.location = location


class RedirectCatchingHandler(urllib.request.HTTPRedirectHandler):
    """
    urllib will happily try to follow redirects; we need to:
      - follow http/https redirects
      - STOP on custom scheme redirect (sf311://auth?code=...)
    """

    def _maybe_raise_on_non_http_location(self, headers) -> None:
        location = None
        # urllib header mapping is case-insensitive, but may present as different casings.
        for k in ("Location", "location"):
            if k in headers:
                location = headers[k]
                break
        if not location:
            return
        parsed = urllib.parse.urlparse(location)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            raise NonHttpRedirect(location)

    # In some Python versions, the redirect logic hits http_error_30x before redirect_request.
    # Intercept here so urllib never attempts to open a non-http(s) URL type (e.g. sf311://).
    def http_error_301(self, req, fp, code, msg, headers):
        self._maybe_raise_on_non_http_location(headers)
        return super().http_error_301(req, fp, code, msg, headers)

    def http_error_302(self, req, fp, code, msg, headers):
        self._maybe_raise_on_non_http_location(headers)
        return super().http_error_302(req, fp, code, msg, headers)

    def http_error_303(self, req, fp, code, msg, headers):
        self._maybe_raise_on_non_http_location(headers)
        return super().http_error_303(req, fp, code, msg, headers)

    def http_error_307(self, req, fp, code, msg, headers):
        self._maybe_raise_on_non_http_location(headers)
        return super().http_error_307(req, fp, code, msg, headers)

    def http_error_308(self, req, fp, code, msg, headers):
        self._maybe_raise_on_non_http_location(headers)
        # Base class may not implement 308 in older versions; fall back to 307 handler.
        handler = getattr(super(), "http_error_308", None)
        if callable(handler):
            return handler(req, fp, code, msg, headers)
        return super().http_error_307(req, fp, code, msg, headers)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            raise NonHttpRedirect(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HiddenFormParser(HTMLParser):
    """
    Minimal HTML parser to extract:
      - a POST form's action
      - all hidden input fields within that form
    """

    def __init__(self):
        super().__init__()
        self._in_form = False
        self.form_action: Optional[str] = None
        self.hidden_fields: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        if tag.lower() == "form":
            method = (attrs_dict.get("method") or "").lower()
            action = attrs_dict.get("action")
            if method == "post" and action:
                # We only care about the first POST form (matches captured /auth page)
                if not self._in_form and self.form_action is None:
                    self._in_form = True
                    self.form_action = action
        elif tag.lower() == "input" and self._in_form:
            if (attrs_dict.get("type") or "").lower() == "hidden":
                name = attrs_dict.get("name")
                value = attrs_dict.get("value", "")
                if name:
                    self.hidden_fields[name] = value

    def handle_endtag(self, tag: str):
        if tag.lower() == "form" and self._in_form:
            self._in_form = False


@dataclass(frozen=True)
class AuthTokens:
    token_type: str
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str
    id_token: Optional[str] = None


def _build_opener() -> urllib.request.OpenerDirector:
    jar = CookieJar()
    handlers = [
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        RedirectCatchingHandler(),
    ]
    return urllib.request.build_opener(*handlers)


def _request(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
    timeout: int = 30,
) -> Tuple[int, Dict[str, str], bytes]:
    req = urllib.request.Request(url=url, data=data, method=method.upper())
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)

    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read()
            # normalize headers to a simple dict; duplicate headers will be joined by urllib
            hdrs = {k: v for k, v in resp.headers.items()}
            return resp.getcode(), hdrs, body
    except NonHttpRedirect as e:
        # This is our intentional escape hatch for sf311://auth?code=...
        raise
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
        return e.code, hdrs, body


def _extract_convey_form(html_bytes: bytes) -> Tuple[str, Dict[str, str]]:
    html = html_bytes.decode("utf-8", errors="replace")
    parser = HiddenFormParser()
    parser.feed(html)
    if not parser.form_action:
        raise RuntimeError("Could not find a POST form action in /auth HTML.")
    if not parser.hidden_fields:
        raise RuntimeError("Found form action but no hidden fields in /auth HTML.")
    return parser.form_action, parser.hidden_fields


def _pick_identity_provider_id(fields: Dict[str, str], preferred: Optional[str]) -> str:
    # Captured flow had a single provider; identity_provider_id was in hidden input.
    ipid = fields.get("identity_provider_id")
    if preferred:
        return preferred
    if not ipid:
        raise RuntimeError("No identity_provider_id in /auth page hidden fields. Specify --identity-provider-id.")
    return ipid


def _extract_location(headers: Dict[str, str]) -> str:
    # urllib folds header names; handle common capitalizations.
    for k in ("Location", "location"):
        if k in headers:
            return headers[k]
    raise RuntimeError("Missing Location header on redirect response.")


def _extract_code_from_sf311_redirect(location: str) -> str:
    # Expected: sf311://auth?code=<uuid>
    parsed = urllib.parse.urlparse(location)
    if parsed.scheme != "sf311":
        raise RuntimeError(f"Expected sf311:// redirect, got: {location}")
    qs = urllib.parse.parse_qs(parsed.query)
    code = (qs.get("code") or [None])[0]
    if not code:
        raise RuntimeError(f"No code=... in redirect: {location}")
    return code


def acquire_tokens(
    *,
    base_url: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    identity_provider_id: Optional[str],
    user_agent_web: str,
    user_agent_app: str,
    timeout: int,
) -> AuthTokens:
    opener = _build_opener()

    # 1) GET /auth
    auth_url = (
        f"{base_url}/auth?"
        + urllib.parse.urlencode(
            {
                "scope": scope,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "response_type": "code",
            }
        )
    )
    status, headers, body = _request(
        opener,
        "GET",
        auth_url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": user_agent_web,
        },
        timeout=timeout,
    )
    if status != 200:
        raise RuntimeError(f"GET /auth failed: HTTP {status}\n{body[:5000].decode('utf-8', errors='replace')}")

    convey_action, form_fields = _extract_convey_form(body)
    # Ensure the key fields are aligned with what we intend (overrides are fine).
    form_fields["client_id"] = client_id
    form_fields["scope"] = scope
    form_fields["response_type"] = "code"
    form_fields["redirect_uri"] = redirect_uri
    form_fields["identity_provider_id"] = _pick_identity_provider_id(form_fields, identity_provider_id)

    # 2) POST /auth/convey
    convey_url = urllib.parse.urljoin(base_url + "/", convey_action.lstrip("/"))
    convey_data = urllib.parse.urlencode(form_fields).encode("utf-8")
    sf311_location: Optional[str] = None
    callback_url: Optional[str] = None
    try:
        status2, headers2, _ = _request(
            opener,
            "POST",
            convey_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Origin": base_url,
                "Referer": auth_url,
                "User-Agent": user_agent_web,
            },
            data=convey_data,
            timeout=timeout,
        )
        if status2 not in (301, 302, 303):
            raise RuntimeError(f"POST /auth/convey expected redirect, got HTTP {status2}")
        callback_url = _extract_location(headers2)
        if callback_url.startswith("/"):
            callback_url = urllib.parse.urljoin(base_url + "/", callback_url.lstrip("/"))
    except NonHttpRedirect as e:
        # urllib may follow redirects automatically (302 -> /auth/callback -> sf311://auth?code=...).
        # If that happens, we can skip the explicit callback step and just parse the code now.
        sf311_location = e.location

    # 3) GET /auth/callback -> expect redirect to sf311://auth?code=...
    if not sf311_location:
        if not callback_url:
            raise RuntimeError("Missing callback URL and did not receive an sf311:// redirect.")
        try:
            status3, headers3, _ = _request(
                opener,
                "GET",
                callback_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": auth_url,
                    "User-Agent": user_agent_web,
                },
                timeout=timeout,
            )
            # If urllib didn't raise, it means it didn't hit a custom scheme redirect.
            if status3 not in (301, 302, 303):
                raise RuntimeError(f"GET /auth/callback expected redirect, got HTTP {status3}")
            sf311_location = _extract_location(headers3)
        except NonHttpRedirect as e:
            sf311_location = e.location

    code = _extract_code_from_sf311_redirect(sf311_location)

    # 4) POST /auth/token (native app call)
    token_url = f"{base_url}/auth/token"
    token_payload = {
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "grant_type": "authorization_code",
    }
    token_data = json.dumps(token_payload).encode("utf-8")
    status4, headers4, body4 = _request(
        opener,
        "POST",
        token_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": user_agent_app,
        },
        data=token_data,
        timeout=timeout,
    )
    if status4 != 200:
        raise RuntimeError(f"POST /auth/token failed: HTTP {status4}\n{body4[:5000].decode('utf-8', errors='replace')}")

    try:
        token_json: Dict[str, Any] = json.loads(body4.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse /auth/token JSON: {e}")

    # Basic validation
    if (token_json.get("token_type") or "").lower() != "bearer":
        raise RuntimeError(f"Unexpected token_type in /auth/token response: {token_json.get('token_type')!r}")
    if not token_json.get("access_token") or not token_json.get("refresh_token"):
        raise RuntimeError("Missing access_token/refresh_token in /auth/token response.")

    return AuthTokens(
        token_type=str(token_json["token_type"]),
        access_token=str(token_json["access_token"]),
        refresh_token=str(token_json["refresh_token"]),
        id_token=str(token_json.get("id_token")) if token_json.get("id_token") else None,
        expires_in=int(token_json.get("expires_in") or 0),
        scope=str(token_json.get("scope") or ""),
    )


def refresh_tokens(
    *,
    base_url: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    refresh_token: str,
    user_agent_app: str,
    timeout: int,
) -> AuthTokens:
    """
    Attempt to obtain a new access_token using an existing refresh_token.

    Note: This endpoint/shape is not captured in Raw logs, but many OAuth flows
    support POST /auth/token with grant_type=refresh_token.
    """
    opener = _build_opener()

    token_url = f"{base_url}/auth/token"
    token_payload = {
        "refresh_token": refresh_token,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "grant_type": "refresh_token",
        "scope": scope,
    }
    token_data = json.dumps(token_payload).encode("utf-8")
    status, _, body = _request(
        opener,
        "POST",
        token_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": user_agent_app,
        },
        data=token_data,
        timeout=timeout,
    )
    if status != 200:
        raise RuntimeError(f"POST /auth/token (refresh) failed: HTTP {status}\n{body[:5000].decode('utf-8', errors='replace')}")

    try:
        token_json: Dict[str, Any] = json.loads(body.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse /auth/token refresh JSON: {e}")

    if (token_json.get("token_type") or "").lower() != "bearer":
        raise RuntimeError(f"Unexpected token_type in refresh response: {token_json.get('token_type')!r}")
    if not token_json.get("access_token") or not token_json.get("refresh_token"):
        raise RuntimeError("Missing access_token/refresh_token in refresh response.")

    return AuthTokens(
        token_type=str(token_json["token_type"]),
        access_token=str(token_json["access_token"]),
        refresh_token=str(token_json["refresh_token"]),
        id_token=str(token_json.get("id_token")) if token_json.get("id_token") else None,
        expires_in=int(token_json.get("expires_in") or 0),
        scope=str(token_json.get("scope") or ""),
    )


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Acquire Spot bearer JWT via /auth + /auth/convey + /auth/callback + /auth/token.")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Base URL (default: {DEFAULT_BASE_URL})")
    p.add_argument("--client-id", default=DEFAULT_CLIENT_ID, help="OAuth client_id")
    p.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI, help="Redirect URI (default matches captured: sf311://auth)")
    p.add_argument("--scope", default=DEFAULT_SCOPE, help='Scope string (default: "refresh_token read write openid")')
    p.add_argument("--identity-provider-id", default=None, help="Override identity_provider_id if /auth page has multiple providers")
    p.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds")
    p.add_argument("--out", default=None, help="Write tokens JSON to this path instead of printing to stdout")
    p.add_argument("--print", dest="do_print", action="store_true", help="Print tokens JSON to stdout (default if --out not set)")
    args = p.parse_args(argv)

    # Mirror captured user agents (roughly): one for webview, one for native app
    user_agent_web = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)"
    user_agent_app = "Reporters/5291 CFNetwork/3826.500.131 Darwin/24.5.0"

    tokens = acquire_tokens(
        base_url=args.base_url.rstrip("/"),
        client_id=args.client_id,
        redirect_uri=args.redirect_uri,
        scope=args.scope,
        identity_provider_id=args.identity_provider_id,
        user_agent_web=user_agent_web,
        user_agent_app=user_agent_app,
        timeout=args.timeout,
    )

    out_obj: Dict[str, Any] = {
        "token_type": tokens.token_type,
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "expires_in": tokens.expires_in,
        "scope": tokens.scope,
    }
    if tokens.id_token:
        out_obj["id_token"] = tokens.id_token

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, indent=2)
        print(f"Wrote tokens to {args.out}", file=sys.stderr)
        return 0

    if args.do_print or not args.out:
        print(json.dumps(out_obj, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


