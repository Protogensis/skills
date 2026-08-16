#!/usr/bin/env python3
"""离线测试：fake client 捕获 grok_gen.py 发出的 API 参数，不发真实请求。

运行: python3 scripts/test_grok_gen.py
"""
import base64
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import grok_gen


def run_generate(argv, fail_first_generate=True):
    """跑一次 generate 子命令，返回 (捕获的 kwargs 列表, 输出文件路径, stdout)。

    fail_first_generate=True 时首次 generate 抛错，模拟中转站不支持
    response_format 的场景，验证 fallback 重试不丢参数。
    """
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        if fail_first_generate and len(calls) == 1:
            raise RuntimeError("response_format not supported")
        return SimpleNamespace(data=[SimpleNamespace(
            b64_json=base64.b64encode(b"fakepng").decode(), url=None)])

    fake_client = SimpleNamespace(images=SimpleNamespace(generate=generate))
    out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    argv = ["grok_gen.py"] + argv + ["--out", out]
    stdout = io.StringIO()
    with mock.patch.object(sys, "argv", argv), \
         mock.patch.object(grok_gen, "client", return_value=fake_client), \
         contextlib.redirect_stdout(stdout):
        grok_gen.main()
    return calls, out, stdout.getvalue()


class GenerateParamsTest(unittest.TestCase):
    def test_default_sends_auto_aspect_no_size(self):
        calls, _, _ = run_generate(["generate", "--prompt", "p"])
        self.assertEqual(len(calls), 2)  # 首次 + fallback
        for kw in calls:
            self.assertNotIn("size", kw)
            self.assertNotIn("quality", kw)  # 未指定时不发送（上游拒绝 auto）
            self.assertEqual(kw["extra_body"], {"aspect_ratio": "auto"})
            self.assertEqual(kw["n"], 1)
        self.assertEqual(calls[0]["response_format"], "b64_json")
        self.assertNotIn("response_format", calls[1])

    def test_explicit_aspect_ratio(self):
        calls, out, stdout = run_generate(
            ["generate", "--prompt", "p", "--aspect-ratio", "16:9"])
        for kw in calls:
            self.assertNotIn("size", kw)
            self.assertEqual(kw.get("extra_body"), {"aspect_ratio": "16:9"})
        self.assertEqual(Path(out).read_bytes(), b"fakepng")  # b64 解码后落盘
        self.assertIn("已保存", stdout)

    def test_fallback_keeps_aspect_ratio(self):
        calls, _, _ = run_generate(
            ["generate", "--prompt", "p", "--aspect-ratio", "9:16"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]["extra_body"], {"aspect_ratio": "9:16"})

    def test_aspect_ratio_decimal(self):
        calls, _, _ = run_generate(
            ["generate", "--prompt", "p", "--aspect-ratio", "19.5:9"])
        self.assertEqual(calls[0]["extra_body"], {"aspect_ratio": "19.5:9"})

    def test_invalid_aspect_ratio_exits_before_request(self):
        argv = ["grok_gen.py", "generate", "--prompt", "p",
                "--aspect-ratio", "garbage", "--out", "/tmp/x.png"]
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(grok_gen, "client") as c:
            with self.assertRaises(SystemExit):
                grok_gen.main()
        c.assert_not_called()  # 校验失败不得发出任何请求


class EditParamsTest(unittest.TestCase):
    def test_edit_sends_no_size_and_follows_input_ratio(self):
        """edit 不发 size/aspect_ratio，输出跟随输入图比例（Imagine 语义）。"""
        edit_calls = []

        def edit(**kwargs):
            edit_calls.append(kwargs)
            return SimpleNamespace(data=[SimpleNamespace(
                b64_json=base64.b64encode(b"fakepng").decode(), url=None)])

        fake_client = SimpleNamespace(images=SimpleNamespace(edit=edit))
        src = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        Path(src).write_bytes(b"src")
        out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
        argv = ["grok_gen.py", "edit", "--image", src,
                "--prompt", "p", "--out", out]
        stdout = io.StringIO()
        with mock.patch.object(sys, "argv", argv), \
             mock.patch.object(grok_gen, "client", return_value=fake_client), \
             contextlib.redirect_stdout(stdout):
            grok_gen.main()
        self.assertEqual(len(edit_calls), 1)
        kw = edit_calls[0]
        self.assertNotIn("size", kw)
        self.assertNotIn("extra_body", kw)
        self.assertEqual(kw["image"], b"src")
        self.assertEqual(kw["n"], 1)
        self.assertEqual(Path(out).read_bytes(), b"fakepng")
        self.assertIn("已保存", stdout.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
