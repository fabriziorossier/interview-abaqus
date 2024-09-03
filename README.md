# Abaqus
Technical Interview Project for Abaqus SpA

## Prerequisites
- **python 3.12.3 or above:** apt install python3 && apt install python3-pip
- **python3.12-venv:** apt install python3-venv
- **djangorestframework-3.15.2 or above:** pip3 install djangorestframework
- **plotly:** pip3 install plotly

## Installation
1. **Create virtual environment on project folder:** python3 -m venv .nameofvirtualenv
2. **Activate virtual environment:** source .nameofvirtualenv/bin/activate
3. **Install requirements:** pip install -r requirements.txt

## Run database migrations
1. python3 manage.py makemigrations
2. python3 manage.py migrate

## Configure database
- **Create admin user:** python3 manage.py createsuperuser

## Set permissions
1. **Change Directory Permissions:** sudo chmod 755 /path/to/abaqus
2. **Change Database File Permissions:** sudo chmod 664 /path/to/abaqus/db.sqlite3
3. **Change Ownership:** sudo chown linuxuser:linuxusergroup /path/to/abaqus -R

## Running the server
- python3 manage.py runserver 0.0.0.0:8000

# Use of this software
This software is provided solely for the technical evaluation process of Fabrizio Alexander Rossier González for Abaqus SpA and is not intended for commercial or non-commercial use without appropriate permission by the former.

# License
Copyright Fabrizio Alexander Rossier González. All rights reserved.

Licensed under the Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Chile (CC BY-NC-ND 3.0 CL) license available in https://creativecommons.org/licenses/by-nc-nd/3.0/cl/legalcode and the adjunt LICENSE file.