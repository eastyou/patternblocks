from __future__ import annotations

# 命令行入口的单元测试。

import io
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from patternblocks.cli import main


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    """执行 CLI 并收集退出码、标准输出与标准错误。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class CliSuccessTests(unittest.TestCase):
    """成功路径测试。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.output = Path(self.temp_dir.name) / "blocks.html"

    def test_success_exit_code(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--each", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")

    def test_output_file_created(self) -> None:
        run_cli(["-o", str(self.output), "--each", "2"])
        self.assertTrue(self.output.exists())

    def test_output_is_html(self) -> None:
        run_cli(["-o", str(self.output), "--each", "2"])
        text = self.output.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("<!DOCTYPE html>"))
        self.assertIn("图案积木裁剪片", text)

    def test_success_message_format(self) -> None:
        code, stdout, _ = run_cli(["-o", str(self.output), "--each", "2"])
        self.assertEqual(code, 0)
        self.assertRegex(
            stdout.strip(),
            r"^已生成 .+（\d+ 页，\d+ 片积木）$",
        )

    def test_message_block_count(self) -> None:
        code, stdout, _ = run_cli(["-o", str(self.output), "--each", "2"])
        self.assertEqual(code, 0)
        self.assertIn("10 片积木", stdout)

    def test_message_page_count_matches_document(self) -> None:
        code, stdout, _ = run_cli(["-o", str(self.output), "--each", "2"])
        self.assertEqual(code, 0)
        match = re.search(r"（(\d+) 页，", stdout)
        self.assertIsNotNone(match)
        assert match is not None
        expected = int(match.group(1))
        text = self.output.read_text(encoding="utf-8")
        self.assertEqual(text.count('<section class="page">'), expected)

    def test_no_challenges_flag(self) -> None:
        code, stdout, _ = run_cli(
            ["-o", str(self.output), "--each", "1", "--no-challenges"]
        )
        self.assertEqual(code, 0)
        self.assertIn("2 页", stdout)
        text = self.output.read_text(encoding="utf-8")
        self.assertNotIn("拼图挑战卡", text)

    def test_custom_shapes(self) -> None:
        code, _, _ = run_cli(
            ["-o", str(self.output), "--each", "3", "--shapes", "菱形,三角形"]
        )
        self.assertEqual(code, 0)
        text = self.output.read_text(encoding="utf-8")
        self.assertEqual(text.count('class="polygon-block"'), 6)

    def test_custom_side_in_output(self) -> None:
        code, _, _ = run_cli(["-o", str(self.output), "--side", "45", "--each", "1"])
        self.assertEqual(code, 0)
        text = self.output.read_text(encoding="utf-8")
        self.assertIn("45 mm", text)

    def test_custom_title_escaped(self) -> None:
        code, _, _ = run_cli(
            ["-o", str(self.output), "--title", "<b>我的积木</b>", "--each", "1"]
        )
        self.assertEqual(code, 0)
        text = self.output.read_text(encoding="utf-8")
        self.assertIn("&lt;b&gt;我的积木&lt;/b&gt;", text)
        self.assertNotIn("<b>我的积木</b>", text)

    def test_nested_output_directory_created(self) -> None:
        target = Path(self.temp_dir.name) / "nested" / "deep" / "blocks.html"
        code, _, _ = run_cli(["-o", str(target), "--each", "1"])
        self.assertEqual(code, 0)
        self.assertTrue(target.exists())

    def test_help_returns_zero(self) -> None:
        code, stdout, _ = run_cli(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("patternblocks", stdout)


class CliErrorTests(unittest.TestCase):
    """参数错误与写文件失败测试。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.output = Path(self.temp_dir.name) / "blocks.html"

    def test_side_below_range(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--side", "10"])
        self.assertEqual(code, 2)
        self.assertIn("参数错误", stderr)
        self.assertIn("边长", stderr)

    def test_side_above_range(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--side", "80"])
        self.assertEqual(code, 2)
        self.assertIn("边长", stderr)

    def test_side_not_number(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--side", "abc"])
        self.assertEqual(code, 2)
        self.assertIn("边长必须是数字", stderr)

    def test_side_empty(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--side", " "])
        self.assertEqual(code, 2)
        self.assertIn("边长", stderr)

    def test_each_zero(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--each", "0"])
        self.assertEqual(code, 2)
        self.assertIn("数量", stderr)

    def test_each_too_large(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--each", "13"])
        self.assertEqual(code, 2)
        self.assertIn("数量", stderr)

    def test_each_not_integer(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--each", "2.5"])
        self.assertEqual(code, 2)
        self.assertIn("必须是整数", stderr)

    def test_unknown_shape(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--shapes", "circle"])
        self.assertEqual(code, 2)
        self.assertIn("未知形状", stderr)

    def test_empty_shapes(self) -> None:
        code, _, stderr = run_cli(["-o", str(self.output), "--shapes", ""])
        self.assertEqual(code, 2)
        self.assertIn("不能为空", stderr)

    def test_write_failure_returns_one(self) -> None:
        directory = Path(self.temp_dir.name) / "folder"
        directory.mkdir()
        code, _, stderr = run_cli(["-o", str(directory), "--each", "1"])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", stderr)

    def test_error_does_not_create_file(self) -> None:
        run_cli(["-o", str(self.output), "--side", "10"])
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
