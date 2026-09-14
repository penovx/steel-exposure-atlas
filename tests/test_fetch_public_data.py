import json
import unittest

from pipeline.fetch_public_data import git_blob_sha1, validate_geojson


class FetchPublicDataTests(unittest.TestCase):
    def test_git_blob_sha1_matches_git_object_format(self):
        self.assertEqual(
            git_blob_sha1(b"hello\n"),
            "ce013625030ba8dba906f756967f9e9ca394464a",
        )

    def test_validate_geojson_accepts_feature_collection(self):
        payload = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature"}]}).encode()
        result = validate_geojson(payload)
        self.assertEqual(result["type"], "FeatureCollection")

    def test_validate_geojson_rejects_empty_collection(self):
        payload = b'{"type":"FeatureCollection","features":[]}'
        with self.assertRaises(ValueError):
            validate_geojson(payload)


if __name__ == "__main__":
    unittest.main()
