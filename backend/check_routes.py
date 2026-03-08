from app.main import app

print('Routes matching /models:')
print('=' * 80)
for route in app.routes:
    if hasattr(route, 'path') and '/models' in route.path:
        methods = ','.join(sorted(route.methods)) if hasattr(route, 'methods') and route.methods else 'N/A'
        print(f'{route.path:60} {methods}')
