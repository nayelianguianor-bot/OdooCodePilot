import subprocess
import sys
import os
import xml.etree.ElementTree as ET

def get_changed_modules():
    """Detecta qué módulos cambiaron en el último commit"""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
        capture_output=True, text=True
    )
    changed = result.stdout.strip().split("\n")
    modules = set()
    for f in changed:
        parts = f.split("/")
        if len(parts) >= 2 and parts[0] == "addons":
            modules.add(parts[1])
    return list(filter(None, modules))

def check_python_syntax(module_path):
    """Verifica sintaxis Python en todos los .py del módulo"""
    errors = []
    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                result = subprocess.run(
                    ["python", "-m", "py_compile", path],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    errors.append(f"Error de sintaxis en {path}:\n  {result.stderr.strip()}")
    return errors

def check_xml_syntax(module_path):
    """Verifica que todos los XML estén bien formados"""
    errors = []
    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".xml"):
                path = os.path.join(root, f)
                try:
                    ET.parse(path)
                except ET.ParseError as e:
                    errors.append(f"Error de XML en {path}:\n  {e}")
    return errors

def check_manifest(module_path):
    """Verifica que __manifest__.py exista y tenga campos obligatorios"""
    errors = []
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.exists(manifest_path):
        errors.append(f"Falta __manifest__.py en {module_path}")
        return errors
    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()
    for field in ["name", "version", "depends"]:
        if f'"{field}"' not in content and f"'{field}'" not in content:
            errors.append(f"Falta campo '{field}' en __manifest__.py de {module_path}")
    return errors

def check_init(module_path):
    """Verifica que exista __init__.py"""
    errors = []
    init_path = os.path.join(module_path, "__init__.py")
    if not os.path.exists(init_path):
        errors.append(f"Falta __init__.py en {module_path}")
    return errors

def check_duplicate_models(addons_path, modules):
    """Detecta modelos con el mismo _name en diferentes módulos"""
    errors = []
    model_registry = {}
    for module in modules:
        module_path = os.path.join(addons_path, module)
        if not os.path.isdir(module_path):
            continue
        for root, _, files in os.walk(module_path):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, encoding="utf-8", errors="ignore") as file:
                        for line in file:
                            line = line.strip()
                            if "_name" in line and "=" in line and "#" not in line:
                                parts = line.split("=")
                                if len(parts) == 2:
                                    name = parts[1].strip().strip("'\"")
                                    if "." in name:
                                        if name in model_registry:
                                            errors.append(
                                                f"Modelo duplicado '{name}' en {module}/{f} "
                                                f"(también declarado en {model_registry[name]})"
                                            )
                                        else:
                                            model_registry[name] = f"{module}/{f}"
    return errors

def check_duplicate_fields(module_path):
    """Detecta campos duplicados en el mismo modelo"""
    errors = []
    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                field_names = []
                for line in content.split("\n"):
                    line = line.strip()
                    if "fields." in line and "=" in line and not line.startswith("#"):
                        field_name = line.split("=")[0].strip()
                        if field_name and " " not in field_name:
                            if field_name in field_names:
                                errors.append(f"Campo duplicado '{field_name}' en {f}")
                            else:
                                field_names.append(field_name)
    return errors

def check_view_fields(module_path):
    """Detecta si las vistas XML referencian campos que no existen en los modelos"""
    errors = []
    defined_fields = set()

    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        line = line.strip()
                        if "fields." in line and "=" in line and not line.startswith("#"):
                            field_name = line.split("=")[0].strip()
                            if field_name and " " not in field_name:
                                defined_fields.add(field_name)

    odoo_base_fields = {
        "id", "name", "display_name", "active", "create_date", "write_date",
        "create_uid", "write_uid", "company_id", "__last_update"
    }
    defined_fields.update(odoo_base_fields)

    # Tags de Odoo que contienen campos de negocio
    view_tags = {"tree", "form", "list", "kanban", "search"}

    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".xml"):
                path = os.path.join(root, f)
                try:
                    tree = ET.parse(path)
                    for elem in tree.iter():
                        # Solo revisar campos dentro de vistas de negocio
                        if elem.tag in view_tags:
                            for child in elem.iter("field"):
                                field_name = child.get("name")
                                if field_name and field_name not in defined_fields:
                                    errors.append(
                                        f"Vista '{f}' referencia campo '{field_name}' "
                                        f"que no existe en los modelos"
                                    )
                except ET.ParseError:
                    pass

    return errors
    """Detecta si las vistas XML referencian campos que no existen en los modelos"""
    errors = []
    defined_fields = set()
    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        line = line.strip()
                        if "fields." in line and "=" in line and not line.startswith("#"):
                            field_name = line.split("=")[0].strip()
                            if field_name and " " not in field_name:
                                defined_fields.add(field_name)
    odoo_base_fields = {
        "id", "name", "display_name", "active", "create_date", "write_date",
        "create_uid", "write_uid", "company_id", "__last_update"
    }
    defined_fields.update(odoo_base_fields)
    for root, _, files in os.walk(module_path):
        for f in files:
            if f.endswith(".xml"):
                path = os.path.join(root, f)
                try:
                    tree = ET.parse(path)
                    for elem in tree.iter():
                        if elem.tag == "field":
                            field_name = elem.get("name")
                            if field_name and field_name not in defined_fields:
                                errors.append(
                                    f"Vista '{f}' referencia campo '{field_name}' "
                                    f"que no existe en los modelos"
                                )
                except ET.ParseError:
                    pass
    return errors

def check_missing_dependencies(module_path):
    """Detecta si el módulo usa modelos de otros módulos sin declararlos en depends"""
    errors = []
    manifest_path = os.path.join(module_path, "__manifest__.py")
    if not os.path.exists(manifest_path):
        return errors
    with open(manifest_path, encoding="utf-8") as f:
        content = f.read()
    known_deps = {
        "sale": ["sale.order", "sale.order.line"],
        "purchase": ["purchase.order", "purchase.order.line"],
        "account": ["account.move", "account.journal"],
        "stock": ["stock.picking", "stock.move"],
        "crm": ["crm.lead"],
        "hr": ["hr.employee"],
        "project": ["project.project", "project.task"],
        "product": ["product.template", "product.product"],
        "contacts": ["res.partner"],
    }
    for dep, models in known_deps.items():
        for model in models:
            for root, _, files in os.walk(module_path):
                for file_name in files:
                    if file_name.endswith(".py"):
                        path = os.path.join(root, file_name)
                        with open(path, encoding="utf-8", errors="ignore") as file:
                            file_content = file.read()
                        if f'"{model}"' in file_content or f"'{model}'" in file_content:
                            if f'"{dep}"' not in content and f"'{dep}'" not in content:
                                errors.append(
                                    f"Usa el modelo '{model}' pero '{dep}' "
                                    f"no está en 'depends' del manifest"
                                )
    return errors

def run_validations(addons_path, modules):
    """Corre todas las validaciones sobre los módulos detectados"""
    results = {}
    cross_errors = check_duplicate_models(addons_path, modules)
    for module in modules:
        module_path = os.path.join(addons_path, module)
        if not os.path.isdir(module_path):
            continue
        print(f"\n🔍 Validando módulo: {module}")
        errors = []
        errors += check_init(module_path)
        errors += check_manifest(module_path)
        errors += check_python_syntax(module_path)
        errors += check_xml_syntax(module_path)
        errors += check_duplicate_fields(module_path)
        errors += check_view_fields(module_path)
        errors += check_missing_dependencies(module_path)
        module_cross_errors = [e for e in cross_errors if module in e]
        errors += module_cross_errors
        if errors:
            print(f"  ❌ {len(errors)} error(es) encontrado(s)")
            for e in errors:
                print(f"     → {e}")
        else:
            print(f"  ✅ Sin errores")
        results[module] = {
            "errors": errors,
            "ok": len(errors) == 0
        }
    return results

if __name__ == "__main__":
    addons_path = os.path.join(os.path.dirname(__file__), "..", "addons")
    addons_path = os.path.abspath(addons_path)
    print("=" * 50)
    print("  OdooCodePilot — Validador de módulos")
    print("=" * 50)
    modules = get_changed_modules()
    if not modules:
        print("\n⚠️  No se detectaron módulos modificados.")
        print("   Validando todos los módulos existentes...\n")
        modules = [
            d for d in os.listdir(addons_path)
            if os.path.isdir(os.path.join(addons_path, d))
        ]
    print(f"\nMódulos a validar: {modules}")
    results = run_validations(addons_path, modules)
    print("\n" + "=" * 50)
    total = len(results)
    ok = sum(1 for v in results.values() if v["ok"])
    fail = total - ok
    print(f"  Resultado: {ok}/{total} módulos sin errores")
    if fail > 0:
        print(f"  ❌ {fail} módulo(s) con errores — push bloqueado")
        print("=" * 50)
        sys.exit(1)
    else:
        print(f"  ✅ Todo limpio — listo para subir")
        print("=" * 50)
        sys.exit(0)