# Sparrow UI

## Description

Sparrow UI module implements UI logic for document data annotation and document data extraction. UI is implemented with Python, Django, HTML and JavaScript

## Instructions

Initial setup, these steps were used to create Sparrow UI. 

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

1. Run Sparrow UI with Debug=True

```
DJANGO_ENV=development ./manage.py runserver
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2021 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
