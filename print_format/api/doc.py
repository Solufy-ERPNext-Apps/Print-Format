import frappe
import json
import os


def _get_print_format_json_for_country(country):
    app_path = frappe.get_app_path("print_format")
    print_format_path = os.path.join(app_path, "print_format", "print_format")
    matched = []

    if not os.path.exists(print_format_path):
        return matched

    for root, dirs, files in os.walk(print_format_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                if (
                    isinstance(data, dict)
                    and data.get("doctype") == "Print Format"
                    and data.get("country") == country
                ):
                    matched.append(data)
            except Exception:
                continue

    return matched


def _get_all_print_format_jsons():
    app_path = frappe.get_app_path("print_format")
    print_format_path = os.path.join(app_path, "print_format", "print_format")
    all_formats = []

    if not os.path.exists(print_format_path):
        return all_formats

    for root, dirs, files in os.walk(print_format_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                if (
                    isinstance(data, dict)
                    and data.get("doctype") == "Print Format"
                    and data.get("name")
                ):
                    all_formats.append(data)
            except Exception:
                continue

    return all_formats


@frappe.whitelist()
def get_formats_available_for_country(country):
    if not country:
        frappe.throw("Country is required.")

    formats = _get_print_format_json_for_country(country)
    if not formats:
        return []

    result = []
    for fmt in formats:
        already_installed = bool(frappe.db.exists("Print Format", fmt.get("name")))
        result.append({
            "name":              fmt.get("name"),
            "doc_type":          fmt.get("doc_type", ""),
            "already_installed": already_installed,
            "disabled":          fmt.get("disabled", 0),
        })

    return result


@frappe.whitelist()
def install_print_formats_for_country(country):
    if not country:
        frappe.throw("Country is required.")

    # Step 1: Selected country ke formats install karo
    formats = _get_print_format_json_for_country(country)

    if not formats:
        return {
            "success": False,
            "message": f"No Print Format found for '{country}'.",
            "country": country,
        }

    installed = []
    skipped   = []

    for fmt_data in formats:
        fmt_name = fmt_data.get("name")
        if not fmt_name:
            continue

        try:
            clean_data = {k: v for k, v in fmt_data.items()
                         if k not in ["creation", "modified", "modified_by",
                                      "owner", "docstatus", "idx"]}
            clean_data["disabled"] = 0

            if frappe.db.exists("Print Format", fmt_name):
                doc = frappe.get_doc("Print Format", fmt_name)
                doc.update(clean_data)
                doc.save(ignore_permissions=True)
            else:
                doc = frappe.get_doc(clean_data)
                doc.insert(ignore_permissions=True)

            installed.append(fmt_name)

        except Exception as e:
            skipped.append(f"{fmt_name}: {str(e)}")
            continue

    # Step 2: ✅ Dusre country ke formats DELETE karo
    all_formats = _get_all_print_format_jsons()
    for fmt_data in all_formats:
        fmt_name    = fmt_data.get("name")
        fmt_country = fmt_data.get("country", "")

        # Selected country ke formats skip karo
        if fmt_country == country:
            continue

        # Dusre country ke formats delete karo
        if frappe.db.exists("Print Format", fmt_name):
            try:
                frappe.delete_doc(
                    "Print Format",
                    fmt_name,
                    ignore_permissions=True,
                    force=True
                )
            except Exception:
                # Delete na ho sake to disable karo
                frappe.db.set_value("Print Format", fmt_name, "disabled", 1)

    frappe.db.commit()

    # Step 3: Setup complete flag
    frappe.db.set_default("print_format_setup_done", "1")
    frappe.db.set_default("print_format_country", country)
    frappe.db.commit()

    if installed:
        msg = f"✅ Installed: {', '.join(installed)}"
        if skipped:
            msg += f" | ⚠️ Skipped: {', '.join(skipped)}"
        return {
            "success":   True,
            "message":   msg,
            "installed": installed,
            "skipped":   skipped,
            "country":   country,
        }
    else:
        return {
            "success": False,
            "message": f"Could not install. {', '.join(skipped)}",
            "country": country,
        }


@frappe.whitelist()
def get_print_format_by_country(country=None):
    if not country:
        country = frappe.db.get_single_value("System Settings", "country")

    if not country:
        frappe.throw("Country not detected.")

    formats = frappe.get_all(
        "Print Format",
        filters={"country": country, "disabled": 0},
        fields=["name", "doc_type"],
        limit=1,
    )

    if not formats:
        return {"country": country, "print_format": None, "exists": False}

    return {
        "country":      country,
        "print_format": formats[0].name,
        "doc_type":     formats[0].doc_type,
        "exists":       True,
    }


@frappe.whitelist()
def get_all_country_formats():
    formats = frappe.get_all(
        "Print Format",
        filters=[["country", "!=", ""]],
        fields=["name", "doc_type", "country", "disabled"],
        order_by="country asc, name asc",
    )

    grouped = {}
    for fmt in formats:
        c = fmt.country
        if c not in grouped:
            grouped[c] = []
        grouped[c].append({
            "name":     fmt.name,
            "doc_type": fmt.doc_type or "",
            "disabled": fmt.disabled or 0,
        })

    return [
        {"country": c, "formats": fmts, "total": len(fmts)}
        for c, fmts in grouped.items()
    ]
