from app.main import app

print("All routes matching /models or /test:")
print("=" * 80)
for route in app.routes:
    if hasattr(route, 'path'):
        if '/models' in route.path or '/test' in route.path:
            methods = sorted(list(route.methods)) if hasattr(route, 'methods') and route.methods else []
            print(f"{route.path:60} {methods}")
