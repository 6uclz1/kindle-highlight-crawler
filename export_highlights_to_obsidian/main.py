import os
import pandas as pd
import re
import hashlib

def sanitize_filename(filename):
    """
    Sanitizes a string to be used as a valid filename.
    """
    return re.sub(r'[\/*?:\"<>|]',"", filename)

def export_to_obsidian(input_csv_path: str, output_dir: str):
    """
    Exports highlights from a CSV file to individual Markdown files for Obsidian.

    Args:
        input_csv_path (str): The path to the input CSV file.
        output_dir (str): The path to the directory where the Markdown files will be saved.
    """
    df = pd.read_csv(input_csv_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    def _clean_location(loc):
        """Return digits-only location (remove commas/other chars) or None."""
        if pd.isna(loc):
            return None
        s = str(loc)
        # remove non-digit characters (commas, spaces, quotes etc.)
        digits = re.sub(r"\D", "", s)
        return digits or None

    def _build_kindle_link(asin, location_digits):
        if not asin and not location_digits:
            return None
        base = f"kindle://book?action=open&asin={asin}" if asin else "kindle://book?action=open"
        if location_digits:
            return f"{base}&location={location_digits}"
        return base

    def _choose_author(row):
        # try common author column names
        for col in ("Author", "Authors", "Author(s)"):
            if col in row.index and pd.notna(row.get(col)):
                return str(row.get(col))
        return None

    def _make_ref_id(text, location, asin):
        key = (str(text) + str(location or "") + str(asin or "")).encode("utf-8")
        return hashlib.md5(key).hexdigest()[:8]

    for title, group in df.groupby("Book"):
        sanitized_title = sanitize_filename(title)
        output_filepath = os.path.join(output_dir, f"{sanitized_title}.md")
        with open(output_filepath, "w", encoding="utf-8") as f:
            # Header
            f.write(f"# {title}\n")

            # Image (best-effort from ASIN)
            # Assumption: construct a m.media-amazon.com image URL from ASIN
            any_asin = None
            if "ASIN" in group.columns:
                any_asin = group["ASIN"].dropna().astype(str).iloc[0] if not group["ASIN"].dropna().empty else None

            # Metadata
            f.write("## Metadata\n")
            # Author: try to pick from first non-empty row
            any_author = None
            for _, r in group.iterrows():
                a = _choose_author(r)
                if a:
                    any_author = a
                    break
            f.write(f"* Author: {any_author or ''}\n")
            f.write(f"* ASIN: {any_asin or ''}\n")
            if any_asin:
                f.write(f"* Reference: https://www.amazon.co.jp/dp/{any_asin}\n")
            # Kindle link (top-level)
            top_kindle = _build_kindle_link(any_asin, None)
            if top_kindle:
                f.write(f"* [Kindle link]({top_kindle})\n")

            f.write("\n## Highlights\n")

            # write each highlight in requested format
            first = True
            for _, row in group.iterrows():
                highlight = row.get("Highlight", "")
                if pd.isna(highlight) or str(highlight).strip() == "":
                    continue
                location = row.get("Location", None) if "Location" in row.index else None
                asin = row.get("ASIN", None) if "ASIN" in row.index else any_asin

                loc_digits = _clean_location(location)
                kindle_link = _build_kindle_link(asin, loc_digits)

                # compute a short ref id
                ref_id = _make_ref_id(highlight, loc_digits, asin)

                # highlight text (no blockquote)
                f.write(f"{highlight} ")

                # location + kindle link
                loc_display = loc_digits if loc_digits else (str(location) if pd.notna(location) else "")
                if loc_display:
                    if kindle_link:
                        f.write(f"— location: [{loc_display}]({kindle_link}) ")
                    else:
                        f.write(f"— location: [{loc_display}] ")
                else:
                    if kindle_link:
                        f.write(f"— {kindle_link} ")

                f.write(f"^ref-{ref_id}\n\n")

                # separator between highlights
                f.write("---\n\n")
    print(f"Exported highlights to {output_dir}")

if __name__ == "__main__":
    export_to_obsidian("_out/highlights.csv", "_out/obsidian")
