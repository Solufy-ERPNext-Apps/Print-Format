import frappe
import json
import os
from frappe.model.document import Document


class PrintFormatSetting(Document):

    def on_update(self):
        if self.country:
            # ❌ Do NOT delete formats (unsafe)
            # remove_other_country_formats(self.country)

            # ✅ Only load/update formats safely
            load_print_formats_for_country(self.country)

            frappe.msgprint(
                f"Print Formats loaded for {self.country}",
                indicator="green",
                alert=True
            )


# -------------------------------
# GET ALL PRINT FORMAT FIXTURES
# -------------------------------
def get_all_print_format_fixtures():
    app_path = frappe.get_app_path("print_format")
    country_formats = {}

    for root, dirs, files in os.walk(app_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
            except Exception as e:
                frappe.logger().error(f"Error reading {filepath}: {e}")
                continue

            # Handle single or list
            if isinstance(data, dict):
                data = [data]

            for pf in data:
                if pf.get("doctype") != "Print Format":
                    continue

                country = pf.get("country")
                if not country:
                    continue

                country_formats.setdefault(country, []).append(pf)

    return country_formats


# -------------------------------
# LOAD PRINT FORMATS FOR COUNTRY
# -------------------------------
def load_print_formats_for_country(country):
    if not country:
        frappe.throw("Country is required")

    all_formats = get_all_print_format_fixtures()
    formats = all_formats.get(country, [])

    if not formats:
        frappe.logger().warning(f"No print formats found for country: {country}")
        frappe.msgprint(
            f"No Print Formats found for {country}",
            indicator="orange",
            alert=True
        )
        return

    success_count = 0
    failed_count = 0

    for pf_data in formats:
        try:
            import_and_enable_print_format(pf_data)
            success_count += 1
        except Exception as e:
            failed_count += 1
            frappe.logger().error(f"Failed to import {pf_data.get('name')}: {str(e)}")

    frappe.db.commit()

    frappe.msgprint(
        f"{success_count} Print Formats loaded for {country} | Failed: {failed_count}",
        indicator="green" if failed_count == 0 else "orange"
    )


# -------------------------------
# CREATE / UPDATE PRINT FORMAT
# -------------------------------
def import_and_enable_print_format(pf_data):

    if not pf_data:
        return

    pf_name = pf_data.get("name")
    if not pf_name:
        frappe.logger().error("Print Format name missing")
        return

    try:
        # Force enable
        pf_data["disabled"] = 0
        pf_data["standard"] = "No"
        pf_data["doctype"] = "Print Format"

        if frappe.db.exists("Print Format", pf_name):
            pf = frappe.get_doc("Print Format", pf_name)

            # ✅ Preserve important fields
            preserve_fields = ["creation", "owner"]
            for field in preserve_fields:
                pf_data.pop(field, None)

            # 🔥 VERY IMPORTANT: Preserve HTML if already exists
            if pf.get("html"):
                pf_data["html"] = pf.html

            pf.update(pf_data)
            pf.save(ignore_permissions=True)

            frappe.logger().info(f"Updated: {pf_name}")

        else:
            pf = frappe.get_doc(pf_data)
            pf.insert(ignore_permissions=True)

            frappe.logger().info(f"Created: {pf_name}")

    except Exception as e:
        frappe.logger().error(f"Failed Print Format {pf_name}: {str(e)}")
