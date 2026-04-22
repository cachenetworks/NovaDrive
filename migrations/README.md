# Migrations

This scaffold includes `Flask-Migrate` for future database evolution, but it does not ship with an initial generated migration.

To create migrations after installing dependencies:

```bash
flask --app novadrive.app:create_app db init
flask --app novadrive.app:create_app db migrate -m "Initial schema"
flask --app novadrive.app:create_app db upgrade
```

For a quick local bootstrap without generating migrations first, you can use:

```bash
flask --app novadrive.app:create_app init-db
```
