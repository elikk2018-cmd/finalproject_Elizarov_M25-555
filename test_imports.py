#!/usr/bin/env python3
"""Тест всех импортов для проверки корректности"""

print("🧪 ТЕСТИРОВАНИЕ ИМПОРТОВ")
print("=" * 40)

modules_to_test = [
    "valutatrade_hub.core.currencies",
    "valutatrade_hub.core.exceptions", 
    "valutatrade_hub.core.models",
    "valutatrade_hub.core.session",
    "valutatrade_hub.core.utils",
    "valutatrade_hub.core.usecases",
    "valutatrade_hub.infra.settings",
    "valutatrade_hub.infra.database",
    "valutatrade_hub.decorators",
    "valutatrade_hub.cli.interface",
    "valutatrade_hub.cli.interactive",
]

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
    except Exception as e:
        print(f"⚠️  {module_name}: {e}")

print("\n" + "=" * 40)
print("🎯 ТЕСТ ЗАВЕРШЕН")
