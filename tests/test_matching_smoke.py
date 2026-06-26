import os
import unittest

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "tuktak_test")
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

from sqlalchemy.orm import configure_mappers

from app.schemas.matching_request import MatchingRequestCreate
from main import app


class MatchingSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configure_mappers()

    def test_openapi_contains_matching_contract(self) -> None:
        expected = {
            "/api/v1/matching-requests",
            "/api/v1/matching-requests/{matching_request_id}",
            "/api/v1/matching-requests/{matching_request_id}/quotes",
            "/api/v1/matching-requests/{matching_request_id}/select-quote",
            "/api/v1/contractors/me/matching-requests",
        }
        self.assertTrue(expected.issubset(app.openapi()["paths"]))

    def test_matching_request_rejects_invalid_budget_range(self) -> None:
        with self.assertRaises(ValueError):
            MatchingRequestCreate.model_validate(
                {
                    "title": "sink repair",
                    "budget_min": "500000",
                    "budget_max": "100000",
                }
            )


if __name__ == "__main__":
    unittest.main()
