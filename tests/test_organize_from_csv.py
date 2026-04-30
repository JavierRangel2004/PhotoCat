import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from organize_from_csv import (
    organize_commit,
    organize_preview,
    resolve_fs_path,
    restore_from_manifest,
)


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

    def test_resolve_fs_path_normalizes_backslashes_on_posix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out = root / "portfolio_out"
            out.mkdir()
            posix_path = str(out.resolve())
            backslash_path = posix_path.replace("/", "\\")
            self.assertEqual(resolve_fs_path(backslash_path), posix_path)

    def test_preview_reports_resolved_output_dir_with_backslash_input(self):
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
                        "dest_relpath": "photos/city/image.jpg",
                    }
                ],
            )
            output_dir = root / "out"
            output_dir.mkdir()
            weird = str(output_dir.resolve()).replace("/", "\\")
            preview = organize_preview(str(csv_path), weird)
            self.assertTrue(preview["contract_valid"])
            self.assertEqual(preview["resolved_output_dir"], str(output_dir.resolve()))

    def test_append_dedupe_skips_when_same_bytes_exist_in_portfolio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "out"
            existing = output_dir / "photos" / "city"
            existing.mkdir(parents=True)
            payload = b"same-bytes"
            (existing / "already.jpg").write_bytes(payload)

            source = root / "incoming" / "different_name.jpg"
            source.parent.mkdir(parents=True)
            source.write_bytes(payload)

            csv_path = root / "corrected.csv"
            self.write_csv(
                csv_path,
                [
                    {
                        "source_path": str(source),
                        "filename": "different_name.jpg",
                        "effective_genre": "Street Documentary",
                        "portfolio_category": "city",
                        "export_include": "true",
                        "dest_relpath": "photos/city/different_name.jpg",
                    }
                ],
            )

            preview = organize_preview(
                str(csv_path), str(output_dir), mode="append_dedupe"
            )
            self.assertTrue(preview["contract_valid"])
            self.assertEqual(preview["moves"], [])
            self.assertEqual(preview["dedupe_skipped_duplicate"], 1)

            commit = organize_commit(
                str(csv_path), str(output_dir), include_excluded=False, mode="append_dedupe"
            )
            self.assertEqual(commit["errors"], [])
            self.assertEqual(commit["moved"], 0)
            self.assertEqual(commit["dedupe_skipped_duplicate"], 1)
            self.assertTrue(source.is_file())

    def test_append_dedupe_renames_on_collision_different_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "out"
            dest_dir = output_dir / "photos" / "city"
            dest_dir.mkdir(parents=True)
            (dest_dir / "frame.jpg").write_bytes(b"old")

            source = root / "src" / "frame.jpg"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"new")

            csv_path = root / "corrected.csv"
            self.write_csv(
                csv_path,
                [
                    {
                        "source_path": str(source),
                        "filename": "frame.jpg",
                        "effective_genre": "Street Documentary",
                        "portfolio_category": "city",
                        "export_include": "true",
                        "dest_relpath": "photos/city/frame.jpg",
                    }
                ],
            )

            preview = organize_preview(
                str(csv_path), str(output_dir), mode="append_dedupe"
            )
            self.assertTrue(preview["contract_valid"])
            self.assertEqual(preview["dedupe_renamed_collision"], 1)
            self.assertEqual(len(preview["moves"]), 1)
            new_dest = preview["moves"][0]["dest_path"]
            self.assertNotEqual(
                new_dest, str((dest_dir / "frame.jpg").resolve())
            )

            commit = organize_commit(
                str(csv_path), str(output_dir), include_excluded=False, mode="append_dedupe"
            )
            self.assertEqual(commit["errors"], [])
            self.assertEqual(commit["moved"], 1)
            self.assertEqual(commit["dedupe_renamed_collision"], 1)
            self.assertTrue(Path(new_dest).is_file())
            self.assertEqual(Path(new_dest).read_bytes(), b"new")
            self.assertEqual((dest_dir / "frame.jpg").read_bytes(), b"old")


if __name__ == "__main__":
    unittest.main()
