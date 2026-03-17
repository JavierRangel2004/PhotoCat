import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from organize_from_csv import organize_commit, organize_preview, restore_from_manifest


class OrganizeFromCsvTests(unittest.TestCase):
    def write_csv(self, csv_path: Path, rows: list[dict[str, str]]) -> None:
        fieldnames = list(rows[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_preview_rejects_csv_without_corrected_contract_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "raw.csv"
            self.write_csv(
                csv_path,
                [
                    {
                        "source_path": str(Path(temp_dir) / "image.jpg"),
                        "filename": "image.jpg",
                    }
                ],
            )

            preview = organize_preview(str(csv_path), str(Path(temp_dir) / "out"))

            self.assertFalse(preview["contract_valid"])
            self.assertIn("missing required columns", preview["errors"][0])

    def test_preview_flags_path_escape_as_invalid_destination(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "image.jpg"
            image_path.write_bytes(b"img")
            csv_path = root / "corrected.csv"
            self.write_csv(
                csv_path,
                [
                    {
                        "source_path": str(image_path),
                        "filename": "image.jpg",
                        "effective_genre": "Street Documentary",
                        "portfolio_category": "city",
                        "export_include": "true",
                        "dest_relpath": "../escape/image.jpg",
                    }
                ],
            )

            preview = organize_preview(str(csv_path), str(root / "out"))

            self.assertFalse(preview["contract_valid"])
            self.assertEqual(len(preview["invalid_destinations"]), 1)
            self.assertIn("photos/<category>", preview["invalid_destinations"][0]["reason"])

    def test_commit_moves_sidecar_and_restore_reverses_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "source" / "frame.jpg"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(b"image")
            xmp_path = image_path.with_suffix(".xmp")
            xmp_path.write_text("sidecar", encoding="utf-8")

            csv_path = root / "corrected.csv"
            self.write_csv(
                csv_path,
                [
                    {
                        "source_path": str(image_path),
                        "filename": "frame.jpg",
                        "effective_genre": "Street Documentary",
                        "portfolio_category": "city",
                        "export_include": "true",
                        "dest_relpath": "photos/city/frame.jpg",
                    }
                ],
            )

            output_dir = root / "organized"
            preview = organize_preview(str(csv_path), str(output_dir))
            self.assertTrue(preview["contract_valid"])
            self.assertEqual(preview["errors"], [])
            self.assertEqual(len(preview["moves"]), 1)

            commit = organize_commit(str(csv_path), str(output_dir), include_excluded=False)
            self.assertEqual(commit["errors"], [])
            self.assertEqual(commit["moved"], 1)

            moved_image = output_dir / "photos" / "city" / "frame.jpg"
            moved_xmp = output_dir / "photos" / "city" / "frame.xmp"
            self.assertTrue(moved_image.is_file())
            self.assertTrue(moved_xmp.is_file())
            self.assertTrue(Path(commit["manifest_path"]).is_file())

            restored = restore_from_manifest(commit["manifest_path"])
            self.assertEqual(restored["errors"], [])
            self.assertEqual(restored["restored"], 1)
            self.assertTrue(image_path.is_file())
            self.assertTrue(xmp_path.is_file())


if __name__ == "__main__":
    unittest.main()
