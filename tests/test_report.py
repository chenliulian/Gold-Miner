import os
import tempfile

from datetime import datetime

from gold_miner.report import write_report


class TestWriteReport:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_report_with_output_path(self):
        output_path = os.path.join(self.temp_dir, "custom_report.md")
        content = "# Test Report\n\nThis is a test report."

        result_path = write_report(content, self.temp_dir, output_path)

        assert result_path == output_path
        assert os.path.exists(output_path)

        with open(output_path) as f:
            assert f.read() == content

    def test_write_report_without_output_path_creates_timestamped_file(self):
        content = "# Test Report"

        result_path = write_report(content, self.temp_dir, None)

        assert os.path.exists(result_path)
        assert result_path.startswith(os.path.join(self.temp_dir, "report_"))
        assert result_path.endswith(".md")

        with open(result_path) as f:
            assert f.read() == content

    def test_write_report_creates_reports_directory(self):
        nested_dir = os.path.join(self.temp_dir, "reports", "nested")
        content = "# Test Report"

        result_path = write_report(content, nested_dir, None)

        assert os.path.exists(nested_dir)
        assert os.path.exists(result_path)

    def test_write_report_timestamp_format(self):
        content = "# Test Report"

        result_path = write_report(content, self.temp_dir, None)

        filename = os.path.basename(result_path)
        timestamp_str = filename.replace("report_", "").replace(".md", "")

        try:
            datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            pytest.fail("Timestamp format is not YYYYMMDD_HHMMSS")

    def test_write_report_preserves_multiline_content(self):
        content = """# Multi-line Report

## Section 1
- Item 1
- Item 2

## Section 2
| Column 1 | Column 2 |
|----------|----------|
| Value 1 | Value 2 |
"""

        result_path = write_report(content, self.temp_dir, None)

        with open(result_path) as f:
            assert f.read() == content

    def test_write_report_with_special_characters(self):
        content = "# Report with special chars: 你好世界 🎉"

        result_path = write_report(content, self.temp_dir, None)

        with open(result_path) as f:
            assert f.read() == content

    def test_write_report_returns_absolute_path(self):
        content = "# Test Report"

        result_path = write_report(content, self.temp_dir, None)

        assert os.path.isabs(result_path)

    def test_write_report_with_custom_output_path_and_subdirs(self):
        subdir = os.path.join(self.temp_dir, "subdir1", "subdir2")
        os.makedirs(subdir, exist_ok=True)
        output_path = os.path.join(subdir, "report.md")
        content = "# Test Report"

        result_path = write_report(content, self.temp_dir, output_path)

        assert result_path == output_path
        assert os.path.exists(subdir)
