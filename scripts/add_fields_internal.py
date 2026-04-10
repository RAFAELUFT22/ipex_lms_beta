import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# This script is meant to be run via:
# bench --site [site] execute scripts.add_fields_internal.run

def run():
    print("Starting custom fields injection...")
    custom_fields = {
        "TDS Aluno": [
            {"fieldname": "whatsapp_group_jid", "label": "WhatsApp Group JID", "fieldtype": "Data", "insert_after": "whatsapp"},
            {"fieldname": "whatsapp_invite_link", "label": "WhatsApp Invite Link", "fieldtype": "Data", "insert_after": "whatsapp_group_jid"}
        ]
    }
    create_custom_fields(custom_fields)
    frappe.db.commit()
    print("✅ Custom fields injected successfully.")
