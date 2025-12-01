import re
import json
import os
import unicodedata


def slugify(text: str) -> str:
    """
    Turn a header like '🚀 Developer Tools' into a safe key like 'developer-tools'.
    - Strips emoji and symbols
    - Lowercases
    - Replaces whitespace with hyphens
    """
    if not text:
        return ""

    # Normalize and drop non-spacing marks (helps strip some emoji artifacts)
    text = unicodedata.normalize("NFKD", text)

    # Remove anything that's not word, space, or hyphen
    text = re.sub(r"[^\w\s-]", "", text)

    # Lowercase and collapse whitespace to hyphens
    text = text.lower().strip()
    text = re.sub(r"\s+", "-", text)

    return text


def parse_readme_to_json(readme_path="README.md", json_path="data.json"):
    """
    Parses the README.md into a structured JSON file (data.json) using the strict
    tool block format:

    * Tool Name
      * **Short Description:** ...
      * **Benefit:** ...
      * **Verification:** ...
      * **Cost:** ...
      * **Link:** ...
    """

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into alternating [text, header, text, header, text...]
    sections = re.split(r"\n(#{1,3}\s[^\n]+)", content)

    tool_block_regex = re.compile(
        r"\*\s+(.+?)\n"                                  # Tool Name
        r"\s*\*\s+\*\*Short Description:\*\*\s+(.+?)\n"  # Short Description
        r"\s*\*\s+\*\*Benefit:\*\*\s+(.+?)\n"           # Benefit
        r"\s*\*\s+\*\*Verification:\*\*\s+(.+?)\n"      # Verification
        r"\s*\*\s+\*\*Cost:\*\*\s+(.+?)\n"              # Cost
        r"\s*\*\s+\*\*Link:\*\*\s+(.+?)(?:\n|$)",       # Link
        re.IGNORECASE | re.DOTALL,
    )

    data = {}

    current_header_text = None
    current_category_key = None

    for section in sections:
        if not section.strip():
            continue

        # If this chunk is a header (e.g. "# 🚀 Developer Tools")
        header_match = re.match(r"#\s?(.+)", section.strip())
        if header_match:
            current_header_text = header_match.group(1).strip()
            current_category_key = None  # reset; we haven't decided it's a category yet
            continue

        # Non-header text: look for tool blocks in this section
        matches = list(tool_block_regex.finditer(section))

        # No tool blocks → not a tool category (could be Purpose, Disclaimer, etc.)
        if not matches:
            continue

        # If we have tool blocks and haven't created a category yet for this header,
        # treat this header as a tool category.
        if current_header_text and current_category_key is None:
            key = slugify(current_header_text)

            # Safety: if the slug is empty or collides, tweak it
            if not key:
                key = "category"
            base_key = key
            counter = 2
            while key in data:
                key = f"{base_key}-{counter}"
                counter += 1

            current_category_key = key
            data[current_category_key] = {
                "title": current_header_text,  # e.g. "🚀 Developer Tools"
                "description": "",
                "tools": [],
            }

        # If for some reason we still don't have a valid category key, skip
        if current_category_key not in data:
            continue

        # Add each tool in this section to the current category
        for match in matches:
            name = match.group(1).strip()
            short_desc = match.group(2).strip()
            benefit_raw = match.group(3).strip()
            verification = match.group(4).strip()
            cost = match.group(5).strip()
            link = match.group(6).strip()

            tool_data = {
                "name": name,
                "short_desc": short_desc,
                "benefit": benefit_raw,
                "verification": verification,
                "link": link,
                "cost": cost,
            }

            data[current_category_key]["tools"].append(tool_data)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Script assumed to live at .github/scripts/
    script_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    os.chdir(repo_root)

    parse_readme_to_json()
