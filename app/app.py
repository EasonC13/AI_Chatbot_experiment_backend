# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

#from .api.api_v1.api import router as api_router
from core.config import ALLOWED_HOSTS, PROJECT_NAME, API_PORT, API_V1_STR
from core.errors import http_422_error_handler, http_error_handler
from db.mongodb_connect import close_mongo_connection, connect_to_mongo
from db.mongodb import AsyncIOMotorClient, get_database
import asyncio


# %%
app = FastAPI(title=PROJECT_NAME)

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(HTTP_422_UNPROCESSABLE_ENTITY, http_422_error_handler)


# %%
from fastapi import APIRouter
router = APIRouter()


from core.config import DATABASE_NAME, USER_COL, MSG_COL, TASKS, FORM_COL, RATE_BOT_COL
from db.mongodb import get_database


# %%



# %%
from pydantic import BaseModel
from datetime import datetime
import random
import json


class newUser(BaseModel):
    account: str


@router.post("/user")
async def user_register(user: newUser):
    col = (await get_database())[DATABASE_NAME][USER_COL]
    result = await col.find_one({"account": user.account}, {"_id": 0})
    if result:
        return {"message": "fail, already have one"}
    else:
        tasks = TASKS.copy()
        random.shuffle(tasks)
        tasks+=["intergrated_test", "debrief"]
        status = "warm_up"
        user_json = {
            "account": user.account,
            "status": status,
            "todo": tasks,
            "task_log": tasks,
            "start_time": datetime.now(),
            "end_time": None,
            "last_update": datetime.now(),
        }
        col = (await get_database())[DATABASE_NAME][USER_COL]
        await col.insert_one(user_json)
        return {"msg": "add user success"}
    


# %%
@router.get("/status/user/{account}")
async def get_user_work(account):
    col = (await get_database())[DATABASE_NAME][USER_COL]
    result = await col.find_one({"account": account}, {"_id": 0})
    
    return {"msg": "get success",
            "status": result["status"],
            "remain": result["todo"]}


# %%
@router.get("/url/form/{name}")
async def get_user_work(name):
    col = (await get_database())[DATABASE_NAME][FORM_COL]
    result = await col.find_one({"usage": name}, {"_id": 0})
    
    return {"msg": "get success",
            "url": result["form_url"]}

class newForm(BaseModel):
    usage: str
    form_url: str
    sheet_url: str
    sheet_id: str

@router.post("/form")
async def user_register(form: newForm):
    col = (await get_database())[DATABASE_NAME][FORM_COL]
    form_json = {
        "usage": form.usage,
        "form_url": form.form_url,
        "sheet_url": form.sheet_url,
        "sheet_id": form.sheet_id,
        "add_time": datetime.now(),
    }
    
    col.insert_one(form_json)
    return {"message": "add success"}


# %%
from core.config import google_credentials
import gspread

@router.get("/user/{user_id}/isfill/form/{form_name}")
async def check_user_form_status(user_id, form_name):
    gss_client = gspread.authorize(google_credentials)

    col = (await get_database())[DATABASE_NAME][FORM_COL]
    form = await col.find_one({"usage": form_name})

    sheet = gss_client.open_by_key(form["sheet_id"]).sheet1
    fillers = sheet.col_values(2)
    fillers = "<split>".join(fillers)
    fillers = fillers.replace(".", "")
    fillers = fillers.split("<split>")
    user_id = user_id.replace(".", "")
    if user_id in fillers:
        is_fill = True
    else:
        is_fill = False

    return {"message": "Check Success", "is_fill": is_fill}


# %%
class rateBot(BaseModel):
    account: str
    status: str
    displayName: str
    img_url: str
    phase: str
    IOS_Score: int
    score_100: int

@router.post("/rate/bot")
async def user_register(rate: rateBot):
    col = (await get_database())[DATABASE_NAME][RATE_BOT_COL]
    data = {"account": rate.account,
             'status': rate.status,
            'displayName': rate.displayName,
             'img_url': rate.img_url,
            "phase": rate.phase,
             'IOS_Score': rate.IOS_Score,
             'score_100': rate.score_100,
             "TimeStamp": datetime.now(),}
    
    col.insert_one(data)
    return {"message": "add success"}


# %%



# %%



# %%
@router.put("/status/user/{account}")
async def update_user_status(account):
    #todo: check the form is filled.
    col = (await get_database())[DATABASE_NAME][USER_COL]
    user = await col.find_one({"account": account}, {"_id": 0})
    current_status = user["status"]
    
    try:
        new_task = user["todo"].pop(0)
    except:
        new_task = "finish"
    user["status"] = new_task
    
    await col.update_one({"account": account},
                         {"$set": {
                             "todo": user["todo"],
                             "status": user["status"],
                             "last_update": datetime.now(),
                             }
                         })
    
    return {"msg": f"update success, new status is {user['status']}",
            "new_status": user['status']}


# %%
class Message(BaseModel):
    account: str
    status: str
    messages: str
    

@router.post("/message")
async def user_register(msg: Message):
    user_col = (await get_database())[DATABASE_NAME][USER_COL]
    user = await user_col.find_one({"account": msg.account}, {"_id": 0})
    
    try:
        current_status = user["status"]
    except:
        current_status = None

    data = {
        "account": msg.account,
        "status": msg.status,
        "message_str": msg.messages,
        "messages": json.loads(msg.messages),
        "db_user_status": current_status,
        "time": datetime.now()
    }

    msg_col = (await get_database())[DATABASE_NAME][MSG_COL]
    msg_col.insert_one(data)
    
    return {"message": "success"}


# %%



# %%



# %%
app.include_router(router, prefix=API_V1_STR, tags=["user"])


# %%

from api.api_v1.api import router as api_v1_router

app.include_router(api_v1_router, prefix=API_V1_STR, tags=["user"])


# %%
from fastapi.responses import HTMLResponse, FileResponse
import os

static_file_path = "../front-end/dist/"
@app.get("/")
def home():
    with open(f"{static_file_path}/index.html") as f:
        html = "".join(f.readlines())
    return HTMLResponse(content=html, status_code= 200)

@app.get("/{whatever:path}")
async def get_static_files_or_404(whatever):
    # try open file for path
    file_path = os.path.join(static_file_path,whatever)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(f"{static_file_path}/index.html")


# %%
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


# %%



# %%
print("讚美主")


