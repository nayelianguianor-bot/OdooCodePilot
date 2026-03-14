import subprocess
import sys
import os
import json
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
        # Solo archivos dentro de addons/
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

def run_validations(addons_path, modules):
    """Corre todas las validaciones sobre los módulos detectados"""
    results = {}
    
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
    # Ruta a la carpeta addons
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
    
    # Resumen final
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