import re
import json
import os

# Map actual README category headers → keys used in JSON
CATEGORY_MAP = {
    "🚀 Developer Tools": "dev-tools",
    "☁️ Cloud Platforms & Compute Credits": "cloud",
    "🧠 AI/ML Tools & Free GPU Access": "ai-ml",
    "🗄️ Databases & Storage": "databases",
    "🔧 DevOps Monitoring & Deployment": "devops",
    "📚 Learning Platforms & Certifications": "learning-cert",
    "🎨 Design / Creative Tools": "design",
    "🔐 Cybersecurity Tools": "cybersecurity",
    "🧰 Productivity & Research Tools": "productivity",
}


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
        r'\*\s+(.+?)\n'                                     # Tool Name
        r'\s*\*\s+\*\*Short Description:\*\*\s+(.+?)\n'     # Short Description
        r'\s*\*\s+\*\*Benefit:\*\*\s+(.+?)\n'              # Benefit
        r'\s*\*\s+\*\*Verification:\*\*\s+(.+?)\n'         # Verification
        r'\s*\*\s+\*\*Cost:\*\*\s+(.+?)\n'                 # Cost
        r'\s*\*\s+\*\*Link:\*\*\s+(.+?)(?:\n|$)',          # Link
        re.IGNORECASE | re.DOTALL
    )

    data = {}
    current_category_key = None

    for section in sections:
        if not section.strip():
            continue

        # Header like "# 🚀 Developer Tools"
        header_match = re.match(r"#\s?(.+)", section.strip())
        if header_match:
            header_text = header_match.group(1).strip()
            category_key = CATEGORY_MAP.get(header_text)

            if category_key:
                current_category_key = category_key
                data[current_category_key] = {
                    "title": header_text,
                    "description": "",
                    "tools": [],
                }
            else:
                current_category_key = None

            continue

        if current_category_key and current_category_key in data:
            for match in tool_block_regex.finditer(section):
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
