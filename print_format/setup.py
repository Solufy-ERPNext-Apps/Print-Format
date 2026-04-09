import frappe
import os
import json


def _get_country_map_from_fixtures():
    country_map = {}
    app_path = frappe.get_app_path("print_format")
    print_format_path = os.path.join(app_path, "print_format", "print_format")

    if not os.path.exists(print_format_path):
        return country_map

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
                    and data.get("country")
                ):
                    country_map[data["name"]] = data["country"]
            except Exception:
                continue

    return country_map


def after_install():
    frappe.db.set_default("print_format_setup_done", "0")
    frappe.db.set_default("print_format_country", "")
    frappe.db.commit()


def on_setup_wizard_complete(args):
    country_map = _get_country_map_from_fixtures()
    for fmt_name, country in country_map.items():
        if frappe.db.exists("Print Format", fmt_name):
            frappe.db.set_value("Print Format", fmt_name, "country", country)

    country = args.get("country") or frappe.db.get_single_value(
        "System Settings", "country"
    ) or ""

    frappe.db.set_default("print_format_setup_done", "0")
    frappe.db.set_default("print_format_country", country)
    frappe.db.commit()


def on_login(login_manager):
    setup_done = frappe.db.get_default("print_format_setup_done")
    if setup_done != "1":
        frappe.local.response["redirect_to"] = "/app/country-print-select"


def get_boot_info(bootinfo):
    setup_done = frappe.db.get_default("print_format_setup_done")
    country    = frappe.db.get_default("print_format_country")

    bootinfo.print_format_setup_done = (setup_done == "1")
    bootinfo.print_format_country    = country or ""
