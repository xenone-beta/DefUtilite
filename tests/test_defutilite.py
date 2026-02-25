import tempfile
import unittest
from pathlib import Path

from defutilite import calculate_folder_size, delete_by_name, find_paths, remove_empty_dirs


class TestDefUtilite(unittest.TestCase):
    def test_find_paths_and_delete_by_name_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "a.tmp").write_text("x", encoding="utf-8")
            (root / "b.log").write_text("y", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "c.tmp").write_text("z", encoding="utf-8")

            matches = find_paths(root, "*.tmp")
            self.assertEqual(len(matches), 2)

            code = delete_by_name(root, "*.tmp", dry_run=True)
            self.assertEqual(code, 0)
            self.assertTrue((root / "a.tmp").exists())
            self.assertTrue((root / "nested" / "c.tmp").exists())

    def test_folder_size_and_cleanup_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "file1.txt").write_text("1234", encoding="utf-8")
            (root / "empty_dir").mkdir()
            (root / "non_empty").mkdir()
            (root / "non_empty" / "file2.txt").write_text("12", encoding="utf-8")

            size = calculate_folder_size(root)
            self.assertGreaterEqual(size, 6)

            removed, errors = remove_empty_dirs(root)
            self.assertEqual(errors, 0)
            self.assertEqual(removed, 1)
            self.assertFalse((root / "empty_dir").exists())


if __name__ == "__main__":
    unittest.main()
