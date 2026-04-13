import frappe
import json
import os


def load_json(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        frappe.log_error(f"JSON Load Error: {file_path} → {str(e)}", "JSON Load Error")
        return None


def get_all_jsons_and_create_formats():
    try:
        base_dir = frappe.get_app_path("print_format", "print_format", "print_format")
    except Exception:
        base_dir = os.path.join(frappe.get_app_path("print_format"), "print_format", "print_format")

    if not os.path.exists(base_dir):
        frappe.log_error(f"Base directory not found: {base_dir}", "Print Format Error")
        frappe.msgprint(f"⚠️ Directory not found: {base_dir}", indicator="red")
        return {}, []

    json_map = {}
    created_formats = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".json"):
                continue

            path = os.path.join(root, file)
            data = load_json(path)

            if not data:
                continue

            format_name = data.get("name") or file.replace(".json", "")
            country = data.get("country")
            doc_type = data.get("doc_type", "Purchase Invoice")

            if country:
                if country not in json_map:
                    json_map[country] = []
                json_map[country].append({
                    "name": format_name,
                    "data": data,
                    "path": path
                })

            try:
                if frappe.db.exists("Print Format", format_name):
                    pf = frappe.get_doc("Print Format", format_name)
                else:
                    pf = frappe.new_doc("Print Format")
                    pf.name = format_name
                    pf.doc_type = doc_type

                pf.html = data.get("html", pf.get("html") or "")
                pf.css = data.get("css", pf.get("css") or "")
                pf.print_format_type = data.get("print_format_type", "Jinja")
                pf.standard = data.get("standard", "No")
                pf.disabled = 1

                if country:
                    pf.country = country

                if data.get("module"):
                    pf.module = data.get("module")

                pf.save(ignore_permissions=True)
                created_formats.append(format_name)

            except Exception as e:
                frappe.log_error(
                    f"Error creating Print Format '{format_name}': {str(e)}",
                    "Print Format Creation Error"
                )

    frappe.db.commit()
    return json_map, created_formats


def apply_json(doc, json_data):
    if not json_data:
        return
    doc.html = json_data.get("html", doc.html or "")
    doc.css = json_data.get("css", doc.css or "")
    doc.print_format_type = json_data.get("print_format_type", "Jinja")
    if json_data.get("country"):
        doc.country = json_data.get("country")


def apply_print_settings_country(doc, method):
    json_map, created_formats = get_all_jsons_and_create_formats()

    if created_formats:
        frappe.msgprint(
            f"✅ {len(created_formats)} print formats loaded",
            indicator="green"
        )
    else:
        frappe.msgprint("⚠️ No JSON files found or no formats created.", indicator="orange")

    if not doc.country:
        frappe.msgprint("⚠️ No country selected. All custom print formats will be disabled.", indicator="orange")
        disable_all_formats()
        return

    selected_country = doc.country

    all_formats = frappe.get_all(
        "Print Format",
        fields=["name", "country"],
        filters={"country": ["is", "set"]}
    )

    enabled_count = 0
    disabled_count = 0

    for fmt in all_formats:
        try:
            pf = frappe.get_doc("Print Format", fmt["name"])

            if pf.country == selected_country:
                pf.disabled = 0
                for json_item in json_map.get(selected_country, []):
                    if json_item["name"] == fmt["name"]:
                        apply_json(pf, json_item["data"])
                        break
                pf.save(ignore_permissions=True)
                enabled_count += 1
            else:
                pf.disabled = 1
                pf.save(ignore_permissions=True)
                disabled_count += 1

        except Exception as e:
            frappe.log_error(
                f"Error updating Print Format '{fmt['name']}': {str(e)}",
                "Print Format Update Error"
            )

    frappe.db.commit()

    frappe.msgprint(
        f"✅ {enabled_count} print formats enabled for {selected_country}<br>"
        f"❌ {disabled_count} formats disabled",
        indicator="green"
    )


def disable_all_formats():
    all_formats = frappe.get_all(
        "Print Format",
        fields=["name"],
        filters={"country": ["is", "set"]}
    )

    for fmt in all_formats:
        try:
            pf = frappe.get_doc("Print Format", fmt["name"])
            pf.disabled = 1
            pf.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Disable error: {fmt['name']}: {str(e)}")

    frappe.db.commit()


@frappe.whitelist()
def reload_all_print_formats():
    json_map, created_formats = get_all_jsons_and_create_formats()
    return {
        "success": True,
        "message": f"{len(created_formats)} print formats successfully loaded",
        "formats": created_formats,
        "countries_found": list(json_map.keys())
    }
