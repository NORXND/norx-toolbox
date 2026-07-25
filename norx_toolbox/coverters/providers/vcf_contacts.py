import re
from pathlib import Path

FROM_FORMATS = {"vcf"}
TO_FORMATS = {"csv"}


def parse_vcf(data: str) -> list[dict[str, str]]:
    cards = re.split(r"BEGIN:VCARD", data)[1:]
    cards = [card.split("END:VCARD")[0] for card in cards]
    cards = [c for c in cards if c]

    contacts = []
    for card in cards:
        lines = [line for line in card.split("\n") if line.strip()]
        contact: dict[str, str] = {}
        for line in lines:
            colon_index = line.find(":")
            if colon_index == -1:
                continue
            key = line[:colon_index].strip()
            value = line[colon_index + 1 :].strip()

            if key == "FN":
                contact["Full Name"] = value
            elif key == "N":
                parts = value.split(";")
                contact["Last Name"] = parts[0] if len(parts) > 0 else ""
                contact["First Name"] = parts[1] if len(parts) > 1 else ""
            elif key.startswith("TEL"):
                contact["Phone"] = value
            elif key.startswith("EMAIL"):
                contact["Email"] = value
            elif key == "ORG":
                contact["Organization"] = value.split(";")[0] if value else ""

        if contact:
            contacts.append(contact)

    return contacts


def to_csv(data: list[dict[str, str]]) -> str:
    if not data:
        return ""

    headers = list(data[0].keys())

    def escape(s: str) -> str:
        return f'"{s.replace(chr(34), chr(34) * 2)}"'

    rows = [",".join(escape(row.get(h, "")) for h in headers) for row in data]
    return "\n".join([",".join(headers), *rows])


async def convert(input_path: Path, output_path: Path) -> Path:
    vcf_data = input_path.read_text(encoding="utf-8")
    contacts = parse_vcf(vcf_data)
    csv_data = to_csv(contacts)
    output_path.write_text(csv_data, encoding="utf-8")
    return output_path
