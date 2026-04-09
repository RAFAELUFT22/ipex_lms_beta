import frappe

def create_test_users():
    users = [
        {"email": "aluno_teste@ipex.edu", "first_name": "Aluno", "roles": ["LMS Student"]},
        {"email": "professor_teste@ipex.edu", "first_name": "Professor", "roles": ["Batch Evaluator", "Course Creator"]},
        {"email": "gestor_teste@ipex.edu", "first_name": "Gestor", "roles": ["Moderator"]}
    ]
    for u in users:
        if not frappe.db.exists("User", u["email"]):
            user = frappe.get_doc({
                "doctype": "User",
                "email": u["email"],
                "first_name": u["first_name"],
                "enabled": 1,
                "send_welcome_email": 0
            })
            user.insert(ignore_permissions=True)
            for role in u["roles"]:
                user.add_roles(role)
            print(f"User {u['email']} created.")
        else:
            user = frappe.get_doc("User", u["email"])
            user.enabled = 1
            # Limpar roles anteriores para evitar conflito
            user.roles = []
            for role in u["roles"]:
                user.add_roles(role)
            user.save(ignore_permissions=True)
            print(f"User {u['email']} updated.")
    
    frappe.db.commit()

if __name__ == "__main__":
    create_test_users()
