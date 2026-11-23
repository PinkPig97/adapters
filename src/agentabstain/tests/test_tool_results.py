import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from fastmcp import FastMCP
from fastmcp.tools.base import _convert_to_content


SPEC = importlib.util.spec_from_file_location(
    "runtime_base", Path(__file__).resolve().parents[1] / "assets/runtime/base.py"
)
runtime_base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_base)


class ToolResultTests(unittest.TestCase):
    def test_sidecar_returns_the_records_visible_through_mcp(self):
        server = FastMCP("test-results")
        records = [{"id": "A", "name": "Café"}, {"id": "B", "name": "North"}]

        @server.tool
        def lookup(empty: bool) -> list:
            return [] if empty else records

        @server.tool
        def typed_lookup() -> list[dict]:
            return records

        @server.tool
        def detail() -> dict:
            return records[0]

        env = SimpleNamespace(mcp=server, _broken_tools={})
        for name, args, expected in (("lookup", {"empty": False}, records), ("lookup", {"empty": True}, []),
                                     ("typed_lookup", {}, records), ("detail", {}, records[0])):
            with self.subTest(tool=name, args=args):
                native = asyncio.run(server.call_tool(name, args))
                actual = runtime_base.BaseEnvironment.call_tool(env, name, **args)
                self.assertEqual(actual, expected)
                self.assertEqual(_convert_to_content(actual), native.content)
