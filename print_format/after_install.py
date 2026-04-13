import frappe


# --------------------------------------------
# ➕ Add Country Field in Print Settings
# --------------------------------------------
def add_country_field_to_print_settings():
    if frappe.db.exists("Custom Field", {
        "dt": "Print Settings",
        "fieldname": "country"
    }):
        return

    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": "Print Settings",
        "label": "Country",
        "fieldname": "country",
        "fieldtype": "Link",
        "options": "Country",   # 👈 Country doctype link
        "insert_after": "pdf_page_size",  # position (change if needed)
        "reqd": 0
    }).insert(ignore_permissions=True)

    frappe.db.commit()


# --------------------------------------------
# ⚙️ AFTER INSTALL
# --------------------------------------------
def after_install():
    # 1️⃣ Add country field in Print Settings
    add_country_field_to_print_settings()

    # 2️⃣ Set default country from System Settings
    country = frappe.db.get_single_value("System Settings", "country")

    if country:
        frappe.db.set_value("Print Settings", "Print Settings", "country", country)
        frappe.db.commit()

        frappe.logger().info(f"Print Settings country set: {country}")
