"""
Unit tests for Persistent SQLite Deduplication & Concurrency
"""

import os
import unittest
from handlers.dedup import check_existing_lead, clear_dedup_cache

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), ".test_dedup.db")


class TestSQLiteDedup(unittest.TestCase):

    def setUp(self):
        clear_dedup_cache(db_path=TEST_DB_PATH)

    def tearDown(self):
        clear_dedup_cache(db_path=TEST_DB_PATH)
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass

    def test_sqlite_persistence_across_runs(self):
        lead = {"email": "persistent.lead@acme.com", "company": "Acme Corp"}

        # First run saves to SQLite
        res1 = check_existing_lead({"data": lead}, use_sqlite=True, db_path=TEST_DB_PATH)
        self.assertEqual(res1["action"], "passed")
        self.assertFalse(res1["is_duplicate"])

        # Second run queries SQLite and detects duplicate
        res2 = check_existing_lead({"data": lead}, use_sqlite=True, db_path=TEST_DB_PATH)
        self.assertEqual(res2["action"], "duplicate_skipped")
        self.assertTrue(res2["is_duplicate"])


if __name__ == "__main__":
    unittest.main()
