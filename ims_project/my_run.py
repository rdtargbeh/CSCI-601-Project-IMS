
cd ims_project

venv\Scripts\activate

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

python manage.py makemigrations inventory
python manage.py migrate

Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

ims_user

# delete migration
rm -rf backend/inventory/migrations/*

Sql@53dTU6d 