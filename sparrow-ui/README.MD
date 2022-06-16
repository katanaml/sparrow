# Sparrow UI

## Description

Sparrow UI module implements UI logic for document data annotation and document data extraction. UI is implemented with Python, Django, HTML and JavaScript

## Instructions

**Initial setup, these steps were used to create Sparrow UI** 

* Django site - **katanaml**
* Django app - **sparrow**

```
poetry init
poetry shell
poetry add django
django-admin startproject katanaml .
python manage.py startapp sparrow
DJANGO_ENV=development ./manage.py migrate
```

1. Create super user (sparrow/welcome1)

```
DJANGO_ENV=development ./manage.py createsuperuser
```

2. Run Sparrow UI with Debug=True

```
DJANGO_ENV=development ./manage.py runserver
```

Verify user:

```
http://127.0.0.1:8000/admin/
```

**Flowbite and Tailwind setup**

1. Add Django compressor to minimize Tailwind CSS file

```
poetry add django-compressor
```

2. Install Tailwind

```
npm init -y
npm install tailwindcss
```

3. Create Tailwind config file

```
npx tailwindcss init
```

4. Install Flowbite UI library

```
npm i flowbite
```

5. Watch for Tailwind CSS changes in development

```
npx tailwindcss -i ./sparrow/static/src/input.css -o ./sparrow/static/src/output.css --watch
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
