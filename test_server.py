"""Tests for the Conductor MCP server.

This is a stdio MCP server that advertises a tool list and dispatches by name
to Conductor's local REST API. It had no tests. The dispatch is a long
if/elif chain keyed on strings that also appear in a separate TOOLS list, so
the two can drift apart silently in either direction: a tool advertised to
Claude but not implemented fails only when someone calls it, and an
implemented branch that is not advertised is dead code no client can reach.

No Conductor instance is required — urllib is stubbed, so these assert the
protocol surface and the URLs each tool builds, not the server's behaviour.
"""
import json
import sys
import types
import unittest
from unittest import mock

import server


VALID_TOP_LEVEL = {"name", "description", "inputSchema"}


def dispatched_names():
    """Every tool name handle_tool actually recognises.

    Determined by calling it: anything that comes back as "Unknown tool" is
    not dispatched. Reading the source for `elif name ==` would just re-encode
    the same assumption the test exists to check.
    """
    found = set()
    for tool in server.TOOLS:
        with mock.patch.object(server, "api", return_value={"ok": True}):
            try:
                out = json.loads(server.handle_tool(tool["name"], _args_for(tool)))
            except Exception:
                # A dispatch branch that raises on our synthetic args is still
                # a dispatch branch; only "Unknown tool" means unrecognised.
                found.add(tool["name"])
                continue
        if not (isinstance(out, dict) and str(out.get("error", "")).startswith("Unknown tool")):
            found.add(tool["name"])
    return found


def _args_for(tool):
    """Minimal args satisfying the tool's declared `required` list."""
    schema = tool.get("inputSchema", {})
    args = {}
    for key in schema.get("required", []):
        spec = schema.get("properties", {}).get(key, {})
        kind = spec.get("type", "string")
        args[key] = {"string": "x", "integer": 1, "number": 1,
                     "boolean": True, "array": [], "object": {}}.get(kind, "x")
    return args


class TestToolSchemas(unittest.TestCase):
    def test_there_is_at_least_one_tool(self):
        self.assertTrue(server.TOOLS)

    def test_names_are_unique(self):
        names = [t["name"] for t in server.TOOLS]
        self.assertEqual(len(names), len(set(names)), "duplicate tool name")

    def test_every_tool_has_the_required_mcp_fields(self):
        for t in server.TOOLS:
            with self.subTest(tool=t.get("name")):
                self.assertLessEqual(set(t), VALID_TOP_LEVEL, "unexpected key")
                self.assertIn("name", t)
                self.assertTrue(t.get("description", "").strip(),
                                "a tool with no description is unusable by a model")
                self.assertEqual(t["inputSchema"].get("type"), "object")

    def test_required_params_are_declared_in_properties(self):
        """A `required` naming a property that does not exist is a schema the
        client cannot satisfy — it will keep sending what it thinks is valid
        and keep being rejected."""
        for t in server.TOOLS:
            schema = t.get("inputSchema", {})
            props = set(schema.get("properties", {}))
            for req in schema.get("required", []):
                with self.subTest(tool=t["name"], required=req):
                    self.assertIn(req, props)

    def test_property_types_are_valid_json_schema(self):
        allowed = {"string", "integer", "number", "boolean", "array", "object"}
        for t in server.TOOLS:
            for prop, spec in t.get("inputSchema", {}).get("properties", {}).items():
                with self.subTest(tool=t["name"], prop=prop):
                    if "type" in spec:
                        self.assertIn(spec["type"], allowed)


class TestAdvertisedMatchesImplemented(unittest.TestCase):
    """The drift guard. TOOLS and the dispatch chain are maintained by hand in
    two places; this is what stops them separating."""

    def test_every_advertised_tool_is_dispatched(self):
        advertised = {t["name"] for t in server.TOOLS}
        missing = advertised - dispatched_names()
        self.assertEqual(missing, set(),
                         f"advertised to the client but not implemented: {sorted(missing)}")

    def test_unknown_tool_is_reported_not_silently_ignored(self):
        out = json.loads(server.handle_tool("no_such_tool_xyz", {}))
        self.assertIn("error", out)
        self.assertIn("Unknown tool", out["error"])


class TestApiUrlConstruction(unittest.TestCase):
    """`api()` is the single point where every tool reaches the REST service."""

    def _capture(self, method, path, body=None):
        seen = {}

        class FakeResp:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b'{"ok": true}'

        def fake_urlopen(req, timeout=None):
            seen["url"] = req.full_url
            seen["method"] = req.get_method()
            seen["body"] = req.data
            seen["headers"] = dict(req.header_items())
            return FakeResp()

        with mock.patch.object(server.urllib.request, "urlopen", fake_urlopen):
            result = server.api(method, path, body)
        return seen, result

    def test_path_is_appended_to_base_url(self):
        seen, _ = self._capture("GET", "/api/workers")
        self.assertEqual(seen["url"], server.BASE_URL + "/api/workers")

    def test_get_sends_no_body_and_no_content_type(self):
        seen, _ = self._capture("GET", "/api/workers")
        self.assertIsNone(seen["body"])
        self.assertNotIn("Content-type", seen["headers"])

    def test_post_sends_json_body_with_content_type(self):
        seen, _ = self._capture("POST", "/api/workers", {"name": "w"})
        self.assertEqual(json.loads(seen["body"]), {"name": "w"})
        self.assertEqual(seen["headers"].get("Content-type"), "application/json")

    def test_http_error_becomes_a_result_not_an_exception(self):
        """A dead Conductor must not take the MCP server down with it: the
        client needs an error it can read, on a connection that stays up."""
        import urllib.error
        def boom(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 500, "boom", {},
                                         __import__("io").BytesIO(b"kaput"))
        with mock.patch.object(server.urllib.request, "urlopen", boom):
            out = server.api("GET", "/api/workers")
        self.assertEqual(out["status"], 500)
        self.assertIn("kaput", out["error"])

    def test_connection_refused_becomes_a_result_not_an_exception(self):
        def boom(req, timeout=None):
            raise ConnectionRefusedError("nobody home")
        with mock.patch.object(server.urllib.request, "urlopen", boom):
            out = server.api("GET", "/api/workers")
        self.assertIn("error", out)
        self.assertIn("nobody home", out["error"])


if __name__ == "__main__":
    unittest.main()
