import frappe
from print_format.print_format.doctype.print_format_setting.print_format_setting import load_print_formats_for_country

def after_install():
    country = frappe.db.get_single_value("System Settings", "country")

    if country:
        setting = frappe.get_single("Print Format Setting")
        setting.country = country
        setting.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.logger().info(f"Print Format Setting initialized: {country}")
