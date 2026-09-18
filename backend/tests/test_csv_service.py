import pytest
from app.services.csv_service import CSVService

def test_csv_parser_and_mapping():
    csv_text = """Blog topic,Primary keyword,Vol.,KD,Target density
Career Options: How to Choose the Right Career Path,career options,4400,35,0.8–1.0%
Career Opportunities in India,career opportunities,18100,57,0.7–0.9%
,"",9900,37,0.8–1.0%"""

    headers, data_rows = CSVService.parse_csv_content(csv_text)
    assert len(headers) == 5
    assert len(data_rows) == 3

    detected_mapping = CSVService.auto_detect_mapping(headers)
    assert detected_mapping["Blog topic"] == "topic"
    assert detected_mapping["Primary keyword"] == "primary_keyword"

    preview = CSVService.validate_and_preview(headers, data_rows, detected_mapping)
    assert preview["total_rows"] == 3
    assert preview["valid_rows_count"] == 2
    assert preview["invalid_rows_count"] == 1
    assert preview["rows"][2]["is_valid"] is False
