#!/bin/bash
python manage.py migrate
python create_admin.py
python manage.py runserver
