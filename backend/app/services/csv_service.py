import csv
import io
from typing import List, Dict, Any, Tuple

REQUIRED_LOGICAL_FIELDS = ["topic", "primary_keyword"]
OPTIONAL_LOGICAL_FIELDS = [
    "search_volume",
    "keyword_difficulty",
    "target_density",
    "category",
    "audience",
    "notes"
]
ALL_LOGICAL_FIELDS = REQUIRED_LOGICAL_FIELDS + OPTIONAL_LOGICAL_FIELDS

COLUMN_ALIASES = {
    "topic": ["blog topic", "topic", "article topic", "title", "headline", "post topic"],
    "primary_keyword": ["primary keyword", "keyword", "target keyword", "main keyword", "focus keyword"],
    "search_volume": ["vol.", "volume", "search volume", "vol", "monthly volume"],
    "keyword_difficulty": ["kd", "keyword difficulty", "difficulty", "kd%"],
    "target_density": ["target density", "density", "kw density", "keyword density"],
    "category": ["category", "cat", "niche", "topic category"],
    "audience": ["audience", "target audience", "persona"],
    "notes": ["notes", "instructions", "comments", "brief notes"]
}

class CSVService:
    @staticmethod
    def auto_detect_mapping(headers: List[str]) -> Dict[str, str]:
        """
        Suggests mapping from CSV header to logical field name.
        Returns dict of {csv_header: logical_field_name}
        """
        mapping = {}
        headers_lower = [h.strip().lower() for h in headers]
        
        for logical_field, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                for idx, orig_header in enumerate(headers):
                    if orig_header in mapping:
                        continue
                    if headers_lower[idx] == alias or alias in headers_lower[idx]:
                        mapping[orig_header] = logical_field
                        break
                if logical_field in mapping.values():
                    break
        return mapping

    @classmethod
    def parse_csv_content(cls, csv_text: str) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Parses raw CSV string into headers and list of row dicts.
        """
        reader = csv.reader(io.StringIO(csv_text))
        rows = [row for row in reader if any(field.strip() for field in row)]
        if not rows:
            return [], []
        headers = [h.strip() for h in rows[0]]
        data_rows = []
        for r in rows[1:]:
            row_dict = {}
            for i, val in enumerate(r):
                if i < len(headers):
                    row_dict[headers[i]] = val.strip()
            data_rows.append(row_dict)
        return headers, data_rows

    @classmethod
    def validate_and_preview(
        cls, headers: List[str], data_rows: List[Dict[str, str]], column_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Applies user mapping and validates each row.
        """
        mapped_rows = []
        seen_topics = set()
        seen_combos = set()
        
        valid_count = 0
        invalid_count = 0
        duplicate_count = 0

        for idx, row in enumerate(data_rows, start=1):
            mapped_item = {"row_index": idx, "is_valid": True, "errors": [], "warnings": []}
            
            # Map fields according to column_mapping dict
            for csv_col, logical_field in column_mapping.items():
                if logical_field and csv_col in row:
                    mapped_item[logical_field] = row[csv_col]

            # Standardize defaults
            topic = mapped_item.get("topic", "").strip()
            keyword = mapped_item.get("primary_keyword", "").strip()
            volume_str = mapped_item.get("search_volume", "").strip() if mapped_item.get("search_volume") else None
            kd_str = mapped_item.get("keyword_difficulty", "").strip() if mapped_item.get("keyword_difficulty") else None

            # Required field checks
            if not topic:
                mapped_item["is_valid"] = False
                mapped_item["errors"].append("Blog topic is required and cannot be empty.")
            if not keyword:
                mapped_item["is_valid"] = False
                mapped_item["errors"].append("Primary keyword is required and cannot be empty.")

            # Numeric checks
            if volume_str:
                try:
                    vol_clean = volume_str.replace(",", "").replace(".", "")
                    mapped_item["search_volume"] = int(vol_clean)
                except ValueError:
                    mapped_item["warnings"].append(f"Invalid numeric search volume '{volume_str}'. Defaulting to None.")
                    mapped_item["search_volume"] = None
            else:
                mapped_item["search_volume"] = None

            if kd_str:
                try:
                    kd_clean = kd_str.replace("%", "").strip()
                    mapped_item["keyword_difficulty"] = int(float(kd_clean))
                except ValueError:
                    mapped_item["warnings"].append(f"Invalid numeric KD '{kd_str}'. Defaulting to None.")
                    mapped_item["keyword_difficulty"] = None
            else:
                mapped_item["keyword_difficulty"] = None

            # Duplicate checks
            topic_lower = topic.lower()
            combo_key = f"{topic_lower}::{keyword.lower()}"
            
            if topic_lower in seen_topics:
                mapped_item["warnings"].append("Duplicate topic detected in CSV.")
                duplicate_count += 1
            if combo_key in seen_combos:
                mapped_item["warnings"].append("Duplicate topic + keyword combination detected.")
            
            if topic_lower:
                seen_topics.add(topic_lower)
            if combo_key:
                seen_combos.add(combo_key)

            if mapped_item["is_valid"]:
                valid_count += 1
            else:
                invalid_count += 1

            mapped_rows.append(mapped_item)

        return {
            "total_rows": len(data_rows),
            "headers": headers,
            "column_mapping": column_mapping,
            "valid_rows_count": valid_count,
            "invalid_rows_count": invalid_count,
            "duplicate_count": duplicate_count,
            "rows": mapped_rows
        }
