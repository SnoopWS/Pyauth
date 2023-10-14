import random
import string
import logging
import datetime
import fastapi
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi import File, UploadFile, Form
from pydantic import BaseModel
import sqlite3
import re
from typing import Optional
from starlette.responses import FileResponse
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
import re
from typing import List
from pydantic import BaseModel

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()
SECRET_KEYS = {
    "app1": "secretkey",
    "app2": "secretkey2"
}

class LicenseKey(BaseModel):
    key: str
    plan: str
    expiry_days: int
    hwid: str

class LicenseKeyResponse(BaseModel):
    key: str
    plan: str
    expiry_days: int
    application: str
    hwid: Optional[str]  

class AdminLicenseKeysResponse(BaseModel):
    application: str
    username: str
    license_keys: List[LicenseKeyResponse]

class LicenseKeyResponseWithDuration(BaseModel):
    key: str
    plan: str
    expiry_days: int
    application: str
    hwid: str
    duration: int    

def generate_license_key(length=32):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.datetime.now()
    response = await call_next(request)
    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time

    logger.info(
        f"Method: {request.method}, Path: {request.url.path}, Status Code: {response.status_code}, "
        f"Elapsed Time: {elapsed_time.total_seconds()} seconds"
    )

    return response
    
alpha_pattern = r'^[a-zA-Z]+$'
admin_secret_key = "sa231jkczxcjsdsakd2121"


@app.get("/edit_license_key_expiry/{application}")
async def edit_license_key_expiry(
    application: str,
    admin_key: str = Query(..., description="Administrator secret key"),
    username: str = Query(..., description="Username for the application"),
    license_key: str = Query(..., description="License key to edit"),
    new_expiry_days: int = Query(..., description="New number of days until expiry"),
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if SECRET_KEYS[application]['username'] != username:
        raise HTTPException(status_code=401, detail="Username does not match the application")

    query = "SELECT key, expiry_date FROM license_keys WHERE application = ? AND key = ?"
    cursor.execute(query, (application, license_key))
    result = cursor.fetchone()

    if result:
        stored_key, expiry_date_str = result
        current_date = datetime.datetime.today().date()
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        if current_date <= expiry_date:
            new_expiry_date = current_date + datetime.timedelta(days=new_expiry_days)

            update_query = (
                "UPDATE license_keys SET expiry_date = ? "
                "WHERE application = ? AND key = ?"
            )
            cursor.execute(
                update_query,
                (new_expiry_date.strftime("%Y-%m-%d"), application, license_key),
            )
            conn.commit()

            return {
                "message": "License key expiry updated successfully",
                "key": license_key,
                "new_expiry_date": new_expiry_date.strftime("%Y-%m-%d"),
            }
        else:
            raise HTTPException(status_code=400, detail="License key has expired")
    else:
        raise HTTPException(status_code=401, detail="Invalid License Key")


@app.get("/list_user_license_keys")
async def list_user_license_keys(
    username: str = Query(..., description="Username for the user"),
    admin_key: str = Query(..., description="Administrator secret key"),
    page: int = Query(1, description="Page number", ge=1),
    items_per_page: int = 100,
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if page < 1:
        raise HTTPException(status_code=400, detail="Page number should be greater than or equal to 1")

    start_index = (page - 1) * items_per_page
    end_index = page * items_per_page

    query = (
        "SELECT key, plan, expiry_date, application FROM license_keys "
        "WHERE username = ? "
        "LIMIT ? OFFSET ?"
    )
    cursor.execute(query, (username, items_per_page, start_index))
    results = cursor.fetchall()

    license_key_list = []
    for row in results:
        key, plan, expiry_date, application = row
        license_key_list.append(LicenseKeyResponse(
            key=key,
            plan=plan,
            expiry_days=(expiry_date - datetime.datetime.date.today()).days,
            application=application,
            hwid=None,
        ))

    return license_key_list

@app.get("/delete_license_key")
async def delete_license_key(
    application: str,
    admin_key: str = Query(..., description="Administrator secret key"),
    username: str = Query(..., description="Username for the application"),
    license_key: str = Query(..., description="License key to delete"),
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.info(f"Deleting license key for application: {application}")
    logger.info(f"SECRET_KEYS: {SECRET_KEYS}")

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if SECRET_KEYS[application]['username'] != username:
        raise HTTPException(status_code=401, detail="Username does not match the application")

    query = "SELECT key, expiry_date FROM license_keys WHERE application = ? AND key = ?"
    cursor.execute(query, (application, license_key))
    result = cursor.fetchone()

    if result:
        stored_key, expiry_date_str = result
        current_date = datetime.datetime.today().date()
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        if current_date <= expiry_date:
            delete_query = "DELETE FROM license_keys WHERE application = ? AND key = ?"
            cursor.execute(delete_query, (application, license_key))
            conn.commit()

            return {
                "message": "License key deleted successfully",
                "key": license_key,
            }
        else:
            raise HTTPException(status_code=400, detail="License key has expired")
    else:
        raise HTTPException(status_code=401, detail="Invalid License Key")

@app.get("/admin/license_keys/{application}", response_model=AdminLicenseKeysResponse)
async def get_admin_license_keys_for_application(
    application: str,
    admin_key: str = Query(..., description="Administrator secret key"),
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if SECRET_KEYS[application]['username']:
        username = SECRET_KEYS[application]['username']
    else:
        username = "N/A"

    query = "SELECT key, plan, expiry_date FROM license_keys WHERE application = ?"
    cursor.execute(query, (application,))
    results = cursor.fetchall()

    license_key_list = []
    current_date = datetime.datetime.today().date()
    for row in results:
        key, plan, expiry_date = row
        expiry_days = (expiry_date - current_date).days
        license_key_list.append(LicenseKeyResponseWithDuration(
            key=key,
            plan=plan,
            expiry_days=expiry_days,
            application=application,
            hwid=None,
            duration=expiry_days
        ))

    return AdminLicenseKeysResponse(
        application=application,
        username=username,
        license_keys=license_key_list
    )


@app.get("/list_user_applications")
async def list_user_applications(
    username: str = Query(..., description="Username for the user"),
    admin_key: str = Query(..., description="Administrator secret key"),
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    query = "SELECT app_name FROM app_secrets WHERE username = ?"
    cursor.execute(query, (username,))
    results = cursor.fetchall()

    applications = [row[0] for row in results]

    return {"username": username, "applications": applications}

@app.get("/add_application", response_model=dict)
async def add_application(
    admin_key: str = fastapi.Query(..., description="Administrator secret key"),
    secret_key: str = fastapi.Query(..., description="Secret key for the application"),
    username: str = fastapi.Query(..., description="Username for the application"),
):
    if admin_key != admin_secret_key:
        raise fastapi.HTTPException(status_code=401, detail="Unauthorized")
    if not re.match("^[a-zA-Z]+$", secret_key):
        raise fastapi.HTTPException(status_code=400, detail="Secret key should contain only alphabetic characters (a-Z).")

    app_name = str(uuid.uuid4())
    query = "INSERT INTO app_secrets (app_name, secret_key, username) VALUES (?, ?, ?)"
    cursor = conn.cursor()
    cursor.execute(query, (app_name, secret_key, username))
    conn.commit()
    SECRET_KEYS[app_name] = {"secret_key": secret_key, "username": username}

    return {
        "app_name": app_name,
        "secret_key": secret_key,
        "username": username
    }

@app.get("/list_application_license_keys")
async def list_application_license_keys(
    username: str = Query(..., description="Username for the user"),
    admin_key: str = Query(..., description="Administrator secret key"),
    application: str = Query(..., description="Name of the application"),
):
    if admin_key != admin_secret_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if SECRET_KEYS[application]["username"] != username:
        raise HTTPException(status_code=401, detail="Username does not match the application")

    query = "SELECT key, plan, expiry_date FROM license_keys WHERE application = ?"
    cursor.execute(query, (application,))
    results = cursor.fetchall()

    license_key_list = []
    current_date = datetime.datetime.today().date()
    
    for row in results:
        key, plan, expiry_date = row
        expiry_days = (datetime.datetime.strptime(expiry_date, "%Y-%m-%d").date() - current_date).days
        license_key_list.append(LicenseKeyResponse(
            key=key,
            plan=plan,
            expiry_days=expiry_days,
            application=application,
            hwid=None,
        ))

    return license_key_list


@app.post("/secret/add_license_key", response_model=LicenseKeyResponse)
async def add_license_key(
    application: str = Query(..., description="Name of the application"),
    secret_key: str = Query(..., description="Administrator secret key"),
    plan: str = Query(..., description="License plan"),
    expiry_days: int = Query(..., description="Number of days until expiry"),
    hwid: Optional[str] = Query(None, description="New HWID"),  
):

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if secret_key != SECRET_KEYS[application]:
        raise HTTPException(status_code=401, detail="Unauthorized")

    ip_address = "N/A"  

    random_key = generate_license_key()
    
    expiry_date = datetime.date.today() + datetime.timedelta(days=expiry_days)


    query = "INSERT INTO license_keys (key, plan, expiry_date, application) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (random_key, plan, expiry_date, application))
    conn.commit()

    user_agent = "N/A"  
    logger.info(
        f"User added a license key for application '{application}' with random key: {random_key}."
    )

    return {
        "key": random_key,
        "plan": plan,
        "expiry_days": expiry_days,
        "application": application,
        "hwid": hwid,  
    }

@app.post("/license_keys/{application}")
async def get_license_keys_for_application(
    application: str,
    secret_key: str = Query(..., description="Administrator secret key for the application"),
):
    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    if secret_key != SECRET_KEYS[application]:
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = "SELECT key, plan, expiry_date FROM license_keys WHERE application = ?"
    cursor.execute(query, (application,))
    results = cursor.fetchall()

    license_key_list = []
    for row in results:
        key, plan, expiry_date = row
        license_key_list.append({
            "key": key,
            "plan": plan,
            "expiry_date": expiry_date,
        })

    return license_key_list

@app.post("/license_keys/{application}/apiv1")
async def retrieve_license_key(
    application: str,
    license_key: str = Query(..., description="Client's license key"),
    hwid: str = Query(..., description="Client's HWID"),  
):
    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    query = "SELECT key, plan, expiry_date, hwid FROM license_keys WHERE application = ? AND key = ?"
    cursor.execute(query, (application, license_key))
    result = cursor.fetchone()

    if result:
        stored_key, plan, expiry_date_str, stored_hwid = result
        current_date = datetime.datetime.today().date()
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        if current_date <= expiry_date:
            if hwid == stored_hwid:  

                logger.info(f"HWID matched for license key: {license_key}")
                return {
                    "message": "License key is valid",
                    "key": stored_key,
                    "plan": plan,
                    "expiry_date": expiry_date_str,
                    "authentication": "Successful",
                }
            else:

                logger.info(f"HWID mismatch for license key: {license_key}")
                return {
                    "message": "HWID Mismatch"
                }
        else:

            logger.info(f"License key has expired for key: {license_key}")
            return {
                "message": "License key has expired"
            }
    else:

        logger.info(f"Invalid license key: {license_key}")
        raise HTTPException(status_code=401, detail="Invalid License Key")

hwid_pattern = r'^S-\d+-\d+(?:-\d+)+$'

def is_valid_hwid(hwid):
    return re.match(hwid_pattern, hwid) is not None

@app.post("/license_keys/{application}/assign_hwid")
async def assign_hwid_to_license_key(
    application: str,
    license_key: str = Query(..., description="Client's license key"),
    hwid: str = Query(..., description="New HWID"),
):
    logger.info(f"Assign HWID request for application: {application}, license_key: {license_key}, hwid: {hwid}")

    if application not in SECRET_KEYS:
        raise HTTPException(status_code=404, detail="Application not found")

    query = "SELECT key, plan, expiry_date, hwid, hwid_last_updated FROM license_keys WHERE application = ? AND key = ?"
    cursor.execute(query, (application, license_key))
    result = cursor.fetchone()

    if result:
        stored_key, plan, expiry_date_str, stored_hwid, stored_hwid_last_updated_str = result
        current_date = datetime.datetime.today().date()

        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        if current_date <= expiry_date:

            if stored_hwid_last_updated_str:
                stored_hwid_last_updated = datetime.datetime.strptime(
                    stored_hwid_last_updated_str, "%Y-%m-%d").date()
            else:
                stored_hwid_last_updated = None

            if (
                stored_hwid_last_updated is None
                or (current_date - stored_hwid_last_updated).days >= 30
            ):

                if is_valid_hwid(hwid):

                    update_query = (
                        "UPDATE license_keys SET hwid = ?, hwid_last_updated = ? "
                        "WHERE application = ? AND key = ?"
                    )
                    cursor.execute(
                        update_query,
                        (hwid, current_date.strftime("%Y-%m-%d"), application, license_key),
                    )
                    conn.commit()

                    return {
                        "message": "HWID updated successfully",
                        "key": stored_key,
                        "plan": plan,
                        "expiry_date": expiry_date_str,
                        "authentication": "Successful",
                    }
                else:

                    raise HTTPException(
                        status_code=400,
                        detail="Invalid HWID format. HWID should match the expected pattern.",
                    )
            else:

                raise HTTPException(
                    status_code=400, detail="HWID change is allowed every 30 days"
                )
        else:

            raise HTTPException(
                status_code=400, detail="License key has expired"
            )
    else:

        raise HTTPException(status_code=401, detail="Invalid License Key")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="YOURIPADDRESS", port=80)
