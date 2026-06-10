from fastapi import FastAPI, APIRouter, HTTPException, Body
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timedelta
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
from pathlib import Path
import random
import string
import re
from telegram import Bot
from telegram.error import TelegramError

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    logger.error("MONGO_URL not set")
    raise Exception("MONGO_URL not set")

client = AsyncIOMotorClient(
    mongo_url,
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
)
db = client[os.environ.get('DB_NAME', 'smart_edu')]

# Admin
ADMIN_PHONE = os.environ.get('ADMIN_PHONE', '')
ADMIN_PASSWORD1 = os.environ.get('ADMIN_PASSWORD1', '')
ADMIN_PASSWORD2 = os.environ.get('ADMIN_PASSWORD2', '')

# Password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

# Storage
verification_codes = {}

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================
class EducationCenter(BaseModel):
    name: str
    phone: str
    password: str
    password2: str
    address: str
    tariff: str
    status: str = "active"
    created_date: datetime = Field(default_factory=datetime.utcnow)

class Teacher(BaseModel):
    center_id: str
    name: str
    phone: str
    password: Optional[str] = None
    groups: List[str] = []

class Group(BaseModel):
    center_id: str
    name: str
    subject: str
    room: str
    time_start: str
    time_end: str
    schedule_days: List[int]
    teacher_id: Optional[str] = None
    students_count: int = 0

class Room(BaseModel):
    center_id: str
    name: str

class Course(BaseModel):
    center_id: str
    name: str
    monthly_fee: float

class Student(BaseModel):
    center_id: str
    group_id: str
    course_id: str
    name: str
    phone: str
    parent_phone: str
    balance: float = 0.0
    coins: int = 0
    status: str = "active"
    password: Optional[str] = None
    created_date: datetime = Field(default_factory=datetime.utcnow)

class StoreItem(BaseModel):
    center_id: str
    name: str
    image_base64: str
    coin_price: int

class StoreOrder(BaseModel):
    student_id: str
    item_id: str
    status: str = "pending"
    created_date: datetime = Field(default_factory=datetime.utcnow)

class Attendance(BaseModel):
    group_id: str
    student_id: str
    date: str
    status: int
    coins_awarded: int = 0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class Transaction(BaseModel):
    student_id: str
    amount: float
    transaction_type: str
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)

# ==================== HELPERS ====================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

def normalize_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 12 and digits.startswith('998'):
        return f"+{digits}"
    if len(digits) == 13 and digits.startswith('998'):
        return f"+{digits[1:]}"
    return phone

def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == '_id':
                result['id'] = str(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, dict):
                result[k] = serialize_doc(v)
            elif isinstance(v, list):
                result[k] = [serialize_doc(i) if isinstance(i, dict) else i for i in v]
            else:
                result[k] = v
        return result
    return doc

def get_daily_fee(monthly_fee: float, days: List[int]) -> float:
    classes = len(days) * 4
    return monthly_fee / classes if classes > 0 else 0

async def send_telegram_code(phone: str, code: str) -> bool:
    try:
        phone = normalize_phone(phone)
        verification_codes[phone] = {
            'code': code,
            'expires': datetime.utcnow() + timedelta(minutes=5)
        }
        
        if not telegram_bot:
            return True
        
        link = await db.telegram_links.find_one({"phone": phone})
        if link and link.get('chat_id'):
            await telegram_bot.send_message(
                chat_id=link['chat_id'],
                text=f"🔐 Tasdiqlash kodingiz: {code}\n\n✅ Kod 5 daqiqada eskiradi."
            )
            return True
        return True
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

# ==================== TEST ENDPOINTS ====================
@api_router.get("/test")
async def test():
    return {"status": "ok", "message": "API is working"}

@api_router.get("/health")
async def health():
    return {
        "status": "healthy",
        "telegram_bot": "configured" if telegram_bot else "not configured",
        "mongodb": "connected"
    }

# ==================== ADMIN ====================
@api_router.post("/admin/login")
async def admin_login(phone: str = Body(...), password: str = Body(...)):
    if not ADMIN_PHONE or not ADMIN_PASSWORD1:
        raise HTTPException(500, "Admin credentials not configured")
    if phone == ADMIN_PHONE and password == ADMIN_PASSWORD1:
        return {"success": True, "message": "First password correct"}
    raise HTTPException(401, "Login xato")

@api_router.post("/admin/login2")
async def admin_login2(phone: str = Body(...), password2: str = Body(...)):
    if not ADMIN_PHONE or not ADMIN_PASSWORD2:
        raise HTTPException(500, "Admin credentials not configured")
    if phone == ADMIN_PHONE and password2 == ADMIN_PASSWORD2:
        return {"success": True, "token": "admin_token_secure"}
    raise HTTPException(401, "Ikkinchi parol xato")

@api_router.get("/admin/dashboard")
async def admin_dashboard():
    total_centers = await db.education_centers.count_documents({})
    active_centers = await db.education_centers.count_documents({"status": "active"})
    total_students = await db.students.count_documents({})
    return {
        "total_centers": total_centers,
        "active_centers": active_centers,
        "total_students": total_students,
        "monthly_revenue": 0
    }

@api_router.post("/admin/centers")
async def create_center(center: EducationCenter):
    if center.tariff == "Pro":
        max_students, max_groups, max_teachers = 100, 5, 5
    elif center.tariff == "Pro+":
        max_students, max_groups, max_teachers = 300, 50, 50
    else:
        max_students, max_groups, max_teachers = -1, -1, -1
    
    data = center.dict()
    data['phone'] = normalize_phone(data['phone'])
    data['password'] = hash_password(data['password'])
    data['password2'] = hash_password(data['password2'])
    data['max_students'] = max_students
    data['max_groups'] = max_groups
    data['max_teachers'] = max_teachers
    
    result = await db.education_centers.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/admin/centers")
async def get_centers():
    centers = await db.education_centers.find().to_list(1000)
    return [serialize_doc(c) for c in centers]

@api_router.put("/admin/centers/{center_id}/status")
async def update_center_status(center_id: str, status: str = Body(..., embed=True)):
    result = await db.education_centers.update_one(
        {"_id": ObjectId(center_id)},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Center topilmadi")
    return {"success": True}

@api_router.put("/admin/centers/{center_id}/tariff")
async def update_center_tariff(center_id: str, tariff: str = Body(..., embed=True)):
    if tariff == "Pro":
        max_students, max_groups, max_teachers = 100, 5, 5
    elif tariff == "Pro+":
        max_students, max_groups, max_teachers = 300, 50, 50
    else:
        max_students, max_groups, max_teachers = -1, -1, -1
    
    result = await db.education_centers.update_one(
        {"_id": ObjectId(center_id)},
        {"$set": {
            "tariff": tariff,
            "max_students": max_students,
            "max_groups": max_groups,
            "max_teachers": max_teachers
        }}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Center topilmadi")
    return {"success": True}

@api_router.delete("/admin/centers/{center_id}")
async def delete_center(center_id: str):
    result = await db.education_centers.delete_one({"_id": ObjectId(center_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Center topilmadi")
    return {"success": True}

# ==================== BOSS ====================
@api_router.post("/boss/login")
async def boss_login(phone: str = Body(...), password: str = Body(...)):
    phone = normalize_phone(phone)
    center = await db.education_centers.find_one({"phone": phone})
    if not center:
        raise HTTPException(404, "Telefon raqam topilmadi")
    if center['status'] == 'frozen':
        raise HTTPException(403, "Hisobingiz muzlatilgan")
    if not verify_password(password, center['password']):
        raise HTTPException(401, "Parol xato")
    return {
        "success": True,
        "center_id": str(center['_id']),
        "center_name": center['name'],
        "tariff": center['tariff']
    }

@api_router.get("/boss/dashboard/{center_id}")
async def boss_dashboard(center_id: str):
    students_count = await db.students.count_documents({"center_id": center_id})
    groups_count = await db.groups.count_documents({"center_id": center_id})
    teachers_count = await db.teachers.count_documents({"center_id": center_id})
    students = await db.students.find({"center_id": center_id}).to_list(1000)
    total_revenue = sum([s.get('balance', 0) for s in students])
    return {
        "students_count": students_count,
        "groups_count": groups_count,
        "teachers_count": teachers_count,
        "monthly_revenue": total_revenue
    }

# ROOMS
@api_router.post("/boss/rooms")
async def create_room(room: Room):
    data = room.dict()
    result = await db.rooms.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/rooms/{center_id}")
async def get_rooms(center_id: str):
    rooms = await db.rooms.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(r) for r in rooms]

@api_router.delete("/boss/rooms/{room_id}")
async def delete_room(room_id: str):
    await db.rooms.delete_one({"_id": ObjectId(room_id)})
    return {"success": True}

# COURSES
@api_router.post("/boss/courses")
async def create_course(course: Course):
    data = course.dict()
    result = await db.courses.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/courses/{center_id}")
async def get_courses(center_id: str):
    courses = await db.courses.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(c) for c in courses]

# GROUPS
@api_router.post("/boss/groups")
async def create_group(group: Group):
    data = group.dict()
    result = await db.groups.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/groups/{center_id}")
async def get_groups(center_id: str):
    groups = await db.groups.find({"center_id": center_id}).to_list(1000)
    result = []
    for g in groups:
        gd = serialize_doc(g)
        if g.get('teacher_id'):
            t = await db.teachers.find_one({"_id": ObjectId(g['teacher_id'])})
            if t:
                gd['teacher_name'] = t['name']
        result.append(gd)
    return result

@api_router.put("/boss/groups/{group_id}")
async def update_group(group_id: str, group: Group):
    result = await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": group.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Guruh topilmadi")
    return {"success": True}

@api_router.delete("/boss/groups/{group_id}")
async def delete_group(group_id: str):
    await db.groups.delete_one({"_id": ObjectId(group_id)})
    return {"success": True}

# TEACHERS
@api_router.post("/boss/teachers")
async def create_teacher(teacher: Teacher):
    data = teacher.dict()
    data['phone'] = normalize_phone(data['phone'])
    if data.get('password'):
        data['password'] = hash_password(data['password'])
    result = await db.teachers.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/teachers/{center_id}")
async def get_teachers(center_id: str):
    teachers = await db.teachers.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(t) for t in teachers]

@api_router.put("/boss/teachers/{teacher_id}")
async def update_teacher(teacher_id: str, teacher: Teacher):
    data = teacher.dict()
    if data.get('password'):
        data['password'] = hash_password(data['password'])
    result = await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$set": data}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Ustoz topilmadi")
    return {"success": True}

@api_router.delete("/boss/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str):
    await db.teachers.delete_one({"_id": ObjectId(teacher_id)})
    return {"success": True}

# STUDENTS
@api_router.post("/boss/students")
async def create_student(student: Student):
    data = student.dict()
    data['phone'] = normalize_phone(data['phone'])
    data['parent_phone'] = normalize_phone(data['parent_phone'])
    if data.get('password'):
        data['password'] = hash_password(data['password'])
    result = await db.students.insert_one(data)
    await db.groups.update_one(
        {"_id": ObjectId(student.group_id)},
        {"$inc": {"students_count": 1}}
    )
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/students/{center_id}")
async def get_students(center_id: str):
    students = await db.students.find({"center_id": center_id}).to_list(1000)
    result = []
    for s in students:
        sd = serialize_doc(s)
        g = await db.groups.find_one({"_id": ObjectId(s['group_id'])})
        if g:
            sd['group_name'] = g['name']
        c = await db.courses.find_one({"_id": ObjectId(s['course_id'])})
        if c:
            sd['course_name'] = c['name']
        result.append(sd)
    return result

@api_router.put("/boss/students/{student_id}/status")
async def update_student_status(student_id: str, status: str = Body(..., embed=True)):
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "O'quvchi topilmadi")
    return {"success": True}

@api_router.put("/boss/students/{student_id}/balance")
async def topup_student_balance(student_id: str, amount: float = Body(..., embed=True)):
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"balance": amount}}
    )
    t = Transaction(
        student_id=student_id,
        amount=amount,
        transaction_type="topup",
        description="Balans to'ldirildi"
    )
    await db.transactions.insert_one(t.dict())
    if result.modified_count == 0:
        raise HTTPException(404, "O'quvchi topilmadi")
    return {"success": True}

@api_router.delete("/boss/students/{student_id}")
async def delete_student(student_id: str):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if s:
        await db.groups.update_one(
            {"_id": ObjectId(s['group_id'])},
            {"$inc": {"students_count": -1}}
        )
    await db.students.delete_one({"_id": ObjectId(student_id)})
    return {"success": True}

# STORE
@api_router.post("/boss/store")
async def create_store_item(item: StoreItem):
    data = item.dict()
    result = await db.store_items.insert_one(data)
    data['id'] = str(result.inserted_id)
    return serialize_doc(data)

@api_router.get("/boss/store/{center_id}")
async def get_store_items(center_id: str):
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(i) for i in items]

@api_router.get("/boss/store/orders/{center_id}")
async def get_store_orders(center_id: str):
    orders = await db.store_orders.find().to_list(1000)
    result = []
    for o in orders:
        s = await db.students.find_one({"_id": ObjectId(o['student_id'])})
        if s and s['center_id'] == center_id:
            od = serialize_doc(o)
            od['student_name'] = s['name']
            i = await db.store_items.find_one({"_id": ObjectId(o['item_id'])})
            if i:
                od['item_name'] = i['name']
                od['coin_price'] = i['coin_price']
            result.append(od)
    return result

@api_router.put("/boss/store/orders/{order_id}/complete")
async def complete_order(order_id: str):
    result = await db.store_orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "completed"}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Buyurtma topilmadi")
    return {"success": True}

@api_router.delete("/boss/store/{item_id}")
async def delete_store_item(item_id: str):
    await db.store_items.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}

# ==================== TEACHER ====================
@api_router.post("/teacher/request-code")
async def teacher_request_code(phone: str = Body(..., embed=True)):
    phone = normalize_phone(phone)
    t = await db.teachers.find_one({"phone": phone})
    if not t:
        raise HTTPException(404, "Telefon raqam topilmadi")
    code = generate_code()
    await send_telegram_code(phone, code)
    return {
        "success": True,
        "message": "Telegram botimizga o'ting va kodni oling"
    }

@api_router.post("/teacher/verify-code")
async def teacher_verify_code(phone: str = Body(...), code: str = Body(...)):
    phone = normalize_phone(phone)
    stored = verification_codes.get(phone)
    if not stored:
        raise HTTPException(400, "Kod topilmadi yoki muddati tugagan")
    if stored['code'] != code:
        raise HTTPException(400, "Kod noto'g'ri")
    if datetime.utcnow() > stored['expires']:
        raise HTTPException(400, "Kod muddati tugagan")
    del verification_codes[phone]
    t = await db.teachers.find_one({"phone": phone})
    return {
        "success": True,
        "teacher_id": str(t['_id']),
        "name": t['name'],
        "has_password": t.get('password') is not None
    }

@api_router.post("/teacher/set-password")
async def teacher_set_password(teacher_id: str = Body(...), password: str = Body(...)):
    result = await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$set": {"password": hash_password(password)}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Ustoz topilmadi")
    return {"success": True}

@api_router.post("/teacher/login")
async def teacher_login(phone: str = Body(...), password: str = Body(...)):
    phone = normalize_phone(phone)
    t = await db.teachers.find_one({"phone": phone})
    if not t or not t.get('password'):
        raise HTTPException(404, "Telefon raqam topilmadi")
    if not verify_password(password, t['password']):
        raise HTTPException(401, "Parol xato")
    return {
        "success": True,
        "teacher_id": str(t['_id']),
        "name": t['name']
    }

@api_router.get("/teacher/dashboard/{teacher_id}")
async def teacher_dashboard(teacher_id: str):
    t = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    groups = await db.groups.find({"teacher_id": teacher_id}).to_list(1000)
    today = datetime.utcnow().weekday() + 1
    today_groups = [g for g in groups if today in g.get('schedule_days', [])]
    return {
        "total_groups": len(groups),
        "today_classes": len(today_groups),
        "groups": [serialize_doc(g) for g in today_groups]
    }

@api_router.get("/teacher/groups/{teacher_id}")
async def teacher_get_groups(teacher_id: str):
    groups = await db.groups.find({"teacher_id": teacher_id}).to_list(1000)
    return [serialize_doc(g) for g in groups]

@api_router.get("/teacher/group/{group_id}/students")
async def teacher_get_students(group_id: str):
    students = await db.students.find({"group_id": group_id}).to_list(1000)
    return [serialize_doc(s) for s in students]

@api_router.post("/teacher/award-coin")
async def teacher_award_coin(student_id: str = Body(...), coins: int = Body(...)):
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"coins": coins}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "O'quvchi topilmadi")
    return {"success": True}

@api_router.post("/teacher/attendance")
async def mark_attendance(
    group_id: str = Body(...),
    student_id: str = Body(...),
    status: int = Body(...),
    date: str = Body(...)
):
    a = Attendance(
        group_id=group_id,
        student_id=student_id,
        date=date,
        status=status,
        coins_awarded=0
    )
    await db.attendance.insert_one(a.dict())
    
    if status == 1:
        s = await db.students.find_one({"_id": ObjectId(student_id)})
        if s and s['status'] == 'active':
            g = await db.groups.find_one({"_id": ObjectId(group_id)})
            c = await db.courses.find_one({"_id": ObjectId(s['course_id'])})
            if g and c:
                daily_fee = get_daily_fee(c['monthly_fee'], g['schedule_days'])
                await db.students.update_one(
                    {"_id": ObjectId(student_id)},
                    {"$inc": {"balance": -daily_fee}}
                )
                t = Transaction(
                    student_id=student_id,
                    amount=daily_fee,
                    transaction_type="deduct",
                    description=f"Dars uchun to'lov ({date})"
                )
                await db.transactions.insert_one(t.dict())
    return {"success": True}

# ==================== STUDENT ====================
@api_router.post("/student/request-code")
async def student_request_code(phone: str = Body(...), user_type: str = Body(...)):
    logger.info(f"Student request-code called: phone={phone}, type={user_type}")
    phone = normalize_phone(phone)
    
    if user_type == "student":
        user = await db.students.find_one({"phone": phone})
    else:
        user = await db.students.find_one({"parent_phone": phone})
    
    if not user:
        raise HTTPException(404, "Telefon raqam topilmadi")
    
    code = generate_code()
    success = await send_telegram_code(phone, code)
    
    return {
        "success": success,
        "message": "Telegram botimizga o'ting va kodni oling"
    }

@api_router.post("/student/verify-code")
async def student_verify_code(phone: str = Body(...), code: str = Body(...), user_type: str = Body(...)):
    phone = normalize_phone(phone)
    stored = verification_codes.get(phone)
    if not stored:
        raise HTTPException(400, "Kod topilmadi")
    if stored['code'] != code:
        raise HTTPException(400, "Kod noto'g'ri")
    if datetime.utcnow() > stored['expires']:
        raise HTTPException(400, "Kod muddati tugagan")
    del verification_codes[phone]
    
    if user_type == "student":
        student = await db.students.find_one({"phone": phone})
    else:
        student = await db.students.find_one({"parent_phone": phone})
    
    if not student:
        raise HTTPException(404, "Student topilmadi")
    
    return {
        "success": True,
        "student_id": str(student['_id']),
        "name": student['name'],
        "has_password": student.get('password') is not None
    }

@api_router.post("/student/set-password")
async def student_set_password(student_id: str = Body(...), password: str = Body(...)):
    await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"password": hash_password(password)}}
    )
    return {"success": True}

@api_router.post("/student/login")
async def student_login(phone: str = Body(...), password: str = Body(...), user_type: str = Body(...)):
    phone = normalize_phone(phone)
    
    if user_type == "student":
        student = await db.students.find_one({"phone": phone})
    else:
        student = await db.students.find_one({"parent_phone": phone})
    
    if not student or not student.get('password'):
        raise HTTPException(404, "Telefon raqam topilmadi")
    if not verify_password(password, student['password']):
        raise HTTPException(401, "Parol xato")
    
    return {
        "success": True,
        "student_id": str(student['_id']),
        "name": student['name']
    }

@api_router.get("/student/dashboard/{student_id}")
async def student_dashboard(student_id: str):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    
    g = await db.groups.find_one({"_id": ObjectId(s['group_id'])})
    attendance_records = await db.attendance.find({"student_id": student_id}).to_list(1000)
    
    today = datetime.utcnow().weekday() + 1
    upcoming_classes = []
    if g:
        for day in g.get('schedule_days', []):
            if day >= today:
                upcoming_classes.append({
                    "day": day,
                    "time": f"{g['time_start']} - {g['time_end']}",
                    "subject": g['subject'],
                    "room": g['room']
                })
    
    return {
        "name": s['name'],
        "balance": s.get('balance', 0),
        "coins": s.get('coins', 0),
        "group_name": g['name'] if g else "",
        "attendance_count": len([a for a in attendance_records if a['status'] == 1]),
        "upcoming_classes": upcoming_classes
    }

@api_router.get("/student/calendar/{student_id}")
async def student_calendar(student_id: str):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    
    g = await db.groups.find_one({"_id": ObjectId(s['group_id'])})
    if not g:
        return []
    
    t = None
    if g.get('teacher_id'):
        t = await db.teachers.find_one({"_id": ObjectId(g['teacher_id'])})
    
    attendance_records = await db.attendance.find({"student_id": student_id}).to_list(1000)
    
    return {
        "schedule_days": g.get('schedule_days', []),
        "time": f"{g['time_start']} - {g['time_end']}",
        "subject": g['subject'],
        "room": g['room'],
        "teacher_name": t['name'] if t else "",
        "attendance": [serialize_doc(a) for a in attendance_records]
    }

@api_router.get("/student/ranking/{student_id}")
async def student_ranking(student_id: str):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    
    group_students = await db.students.find({"group_id": s['group_id']}).sort("coins", -1).to_list(1000)
    group_ranking = [{"name": st['name'], "coins": st.get('coins', 0)} for st in group_students]
    
    center_students = await db.students.find({"center_id": s['center_id']}).sort("coins", -1).to_list(1000)
    center_ranking = [{"name": st['name'], "coins": st.get('coins', 0)} for st in center_students[:20]]
    
    return {
        "group_ranking": group_ranking,
        "center_ranking": center_ranking,
        "my_coins": s.get('coins', 0)
    }

@api_router.get("/student/store/{center_id}")
async def student_get_store(center_id: str):
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(i) for i in items]

@api_router.post("/student/store/order")
async def student_create_order(student_id: str = Body(...), item_id: str = Body(...)):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    
    i = await db.store_items.find_one({"_id": ObjectId(item_id)})
    if not i:
        raise HTTPException(404, "Mahsulot topilmadi")
    
    if s.get('coins', 0) < i['coin_price']:
        raise HTTPException(400, "Yetarli coin yo'q")
    
    await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"coins": -i['coin_price']}}
    )
    
    order = StoreOrder(student_id=student_id, item_id=item_id, status="pending")
    result = await db.store_orders.insert_one(order.dict())
    
    return {"success": True, "order_id": str(result.inserted_id)}

@api_router.get("/student/profile/{student_id}")
async def student_profile(student_id: str):
    s = await db.students.find_one({"_id": ObjectId(student_id)})
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    return serialize_doc(s)

# ==================== TELEGRAM WEBHOOK ====================
@api_router.post("/telegram/webhook")
async def telegram_webhook(update: dict = Body(...)):
    try:
        if not telegram_bot:
            logger.error("Telegram bot not configured")
            return {"ok": False}
        
        message = update.get('message', {})
        chat = message.get('chat', {})
        text = message.get('text', '')
        chat_id = chat.get('id')
        
        if not chat_id:
            return {"ok": False}
        
        logger.info(f"TG message from {chat_id}: {text[:50] if text else 'empty'}")
        
        # Check if already registered
        existing = await db.telegram_links.find_one({"chat_id": chat_id})
        if existing:
            await telegram_bot.send_message(
                chat_id=chat_id,
                text=f"✅ Siz allaqachon ro'yxatdan o'tgansiz!\n📞 Raqamingiz: {existing['phone']}\n\n❌ Yangi raqam kiritish mumkin emas."
            )
            return {"ok": True}
        
        if text == '/start':
            await telegram_bot.send_message(
                chat_id=chat_id,
                text="👋 Salom! EDU TIZIM botiga xush kelibsiz.\n\n📱 Telefon raqamingizni +998XXXXXXXXX formatida yuboring.\n\n⚠️ Bu raqam faqat bir marta ro'yxatdan o'tkaziladi."
            )
        elif text.startswith('+998') and len(text) == 13:
            phone = text
            # Check if phone already linked
            phone_exists = await db.telegram_links.find_one({"phone": phone})
            if phone_exists:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Bu telefon raqam ({phone}) allaqachon ro'yxatdan o'tgan!"
                )
                return {"ok": True}
            
            # Save new registration
            await db.telegram_links.update_one(
                {"chat_id": chat_id},
                {"$set": {"phone": phone, "chat_id": chat_id, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            
            # Check for pending code
            stored = verification_codes.get(phone)
            if stored:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Telefon raqamingiz {phone} saqlandi!\n\n🔐 Tasdiqlash kodingiz: {stored['code']}\n\n⚠️ Kod 5 daqiqada eskiradi."
                )
            else:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Telefon raqamingiz {phone} saqlandi!\n\nEndi ilovada login qiling."
                )
        else:
            await telegram_bot.send_message(
                chat_id=chat_id,
                text="❌ Noto'g'ri format!\n\nIltimos, telefon raqamingizni +998XXXXXXXXX formatida yuboring.\nMasalan: +998901234567"
            )
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False}

@api_router.get("/telegram/setup")
async def setup_telegram_webhook(url: str):
    try:
        if not telegram_bot:
            return {"success": False, "error": "Bot not configured"}
        webhook_url = f"{url}/api/telegram/webhook"
        await telegram_bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
        return {"success": True, "message": f"Webhook set to {webhook_url}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== ADMIN PANEL ====================
@api_router.get("/admin-panel", response_class=HTMLResponse)
async def admin_panel_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            width: 100%;
            max-width: 400px;
        }
        .login-box h2 { text-align: center; margin-bottom: 30px; color: #333; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; color: #555; }
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .error { color: #e74c3c; margin-top: 10px; text-align: center; }
        .dashboard { display: none; }
        .dashboard.active { display: block; }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { color: #333; }
        .logout-btn {
            padding: 10px 20px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
        }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card p { font-size: 32px; font-weight: bold; color: #333; }
        .centers-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .add-btn {
            padding: 10px 20px;
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .centers-list { display: grid; gap: 15px; }
        .center-card {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .center-info h3 { margin-bottom: 5px; }
        .center-actions button {
            margin-left: 10px;
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn-edit { background: #3498db; color: white; }
        .btn-freeze { background: #f39c12; color: white; }
        .btn-delete { background: #e74c3c; color: white; }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            width: 90%;
            max-width: 500px;
        }
        .modal-actions { display: flex; gap: 10px; margin-top: 20px; }
        .btn-cancel { background: #95a5a6; color: white; padding: 12px; border: none; border-radius: 5px; cursor: pointer; flex: 1; }
        .btn-submit { background: #2ecc71; color: white; padding: 12px; border: none; border-radius: 5px; cursor: pointer; flex: 1; }
    </style>
</head>
<body>
    <div id="loginContainer" class="login-container">
        <div class="login-box">
            <h2>🔐 Admin Panel</h2>
            <div id="loginStep1">
                <div class="form-group">
                    <label>Telefon raqam</label>
                    <input type="text" id="phone" placeholder="+998901234567">
                </div>
                <div class="form-group">
                    <label>Parol 1</label>
                    <input type="password" id="password1">
                </div>
                <button class="btn" id="loginBtn1">Kirish</button>
                <div id="error1" class="error"></div>
            </div>
            <div id="loginStep2" style="display:none;">
                <div class="form-group">
                    <label>Parol 2</label>
                    <input type="password" id="password2">
                </div>
                <button class="btn" id="loginBtn2">Tasdiqlash</button>
                <div id="error2" class="error"></div>
            </div>
        </div>
    </div>
    <div id="dashboard" class="dashboard">
        <div class="container">
            <div class="header">
                <h1>📊 Admin Dashboard</h1>
                <button class="logout-btn" id="logoutBtn">Chiqish</button>
            </div>
            <div class="stats">
                <div class="stat-card"><h3>Jami Markazlar</h3><p id="totalCenters">0</p></div>
                <div class="stat-card"><h3>Faol Markazlar</h3><p id="activeCenters">0</p></div>
                <div class="stat-card"><h3>Jami O'quvchilar</h3><p id="totalStudents">0</p></div>
            </div>
            <div class="centers-section">
                <div class="section-header">
                    <h2>O'quv Markazlar</h2>
                    <button class="add-btn" id="addCenterBtn">+ Yangi Markaz</button>
                </div>
                <div id="centersList" class="centers-list"></div>
            </div>
        </div>
    </div>
    <div id="addModal" class="modal">
        <div class="modal-content">
            <h2>Yangi Markaz</h2>
            <div class="form-group"><input type="text" id="centerName" placeholder="Nomi"></div>
            <div class="form-group"><input type="text" id="centerPhone" placeholder="Telefon (+998...)" value="+998"></div>
            <div class="form-group"><input type="password" id="centerPassword" placeholder="Parol"></div>
            <div class="form-group"><input type="password" id="centerPassword2" placeholder="Parol (takroran)"></div>
            <div class="form-group"><input type="text" id="centerAddress" placeholder="Manzil"></div>
            <div class="form-group">
                <select id="centerTariff">
                    <option value="Pro">Pro</option>
                    <option value="Pro+">Pro+</option>
                    <option value="VIP">VIP</option>
                </select>
            </div>
            <div class="modal-actions">
                <button class="btn-cancel" id="cancelModalBtn">Bekor</button>
                <button class="btn-submit" id="submitCenterBtn">Yaratish</button>
            </div>
        </div>
    </div>
    <script>
        const API_BASE = '/api';
        let currentPhone = '';
        
        async function login1() {
            const phone = document.getElementById('phone').value;
            const pwd = document.getElementById('password1').value;
            if(!phone||!pwd){document.getElementById('error1').textContent='Ma\'lumotlarni kiriting!';return;}
            try{
                const res=await fetch(API_BASE+'/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone,pwd})});
                if(res.ok){
                    currentPhone=phone;
                    document.getElementById('loginStep1').style.display='none';
                    document.getElementById('loginStep2').style.display='block';
                }else{document.getElementById('error1').textContent='Login xato!';}
            }catch(e){document.getElementById('error1').textContent='Xatolik!';}
        }
        async function login2(){
            const pwd=document.getElementById('password2').value;
            if(!pwd){document.getElementById('error2').textContent='Parolni kiriting!';return;}
            try{
                const res=await fetch(API_BASE+'/admin/login2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:currentPhone,password2:pwd})});
                if(res.ok){
                    document.getElementById('loginContainer').style.display='none';
                    document.getElementById('dashboard').classList.add('active');
                    loadDashboard();
                }else{document.getElementById('error2').textContent='Parol xato!';}
            }catch(e){document.getElementById('error2').textContent='Xatolik!';}
        }
        async function loadDashboard(){
            try{
                const res=await fetch(API_BASE+'/admin/dashboard');
                const d=await res.json();
                document.getElementById('totalCenters').textContent=d.total_centers||0;
                document.getElementById('activeCenters').textContent=d.active_centers||0;
                document.getElementById('totalStudents').textContent=d.total_students||0;
                loadCenters();
            }catch(e){console.error(e);}
        }
        async function loadCenters(){
            try{
                const res=await fetch(API_BASE+'/admin/centers');
                const centers=await res.json();
                const list=document.getElementById('centersList');
                list.innerHTML='';
                for(let c of centers){
                    const card=document.createElement('div');
                    card.className='center-card';
                    card.innerHTML=`<div><h3>${c.name} <span style="background:#3498db;color:white;padding:2px 8px;border-radius:3px;">${c.tariff}</span> <span style="background:${c.status=='active'?'#2ecc71':'#e74c3c'};color:white;padding:2px 8px;border-radius:3px;">${c.status=='active'?'Faol':'Muzlatilgan'}</span></h3><p>📞 ${c.phone} | 📍 ${c.address}</p></div>
                        <div><button class="btn-edit" onclick="updateTariff('${c.id}')">Tarif</button><button class="btn-freeze" onclick="toggleStatus('${c.id}','${c.status}')">${c.status=='active'?'Muzlatish':'Faollashtirish'}</button><button class="btn-delete" onclick="deleteCenter('${c.id}')">O\'chirish</button></div>`;
                    list.appendChild(card);
                }
            }catch(e){}
        }
        async function toggleStatus(id,status){
            const newStatus=status=='active'?'frozen':'active';
            if(!confirm(`Markazni ${newStatus=='active'?'faollashtirmoqchi':'muzlatmoqchi'}misiz?`))return;
            await fetch(API_BASE+'/admin/centers/'+id+'/status',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:newStatus})});
            loadDashboard();
        }
        async function updateTariff(id){
            const tariff=prompt('Yangi tarif (Pro, Pro+, VIP):');
            if(tariff&&['Pro','Pro+','VIP'].includes(tariff)){
                await fetch(API_BASE+'/admin/centers/'+id+'/tariff',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({tariff})});
                loadDashboard();
            }
        }
        async function deleteCenter(id){
            if(!confirm('O\'chirmoqchimisiz?'))return;
            await fetch(API_BASE+'/admin/centers/'+id,{method:'DELETE'});
            loadDashboard();
        }
        function openAddModal(){
            document.getElementById('addModal').classList.add('active');
            document.getElementById('centerName').value='';
            document.getElementById('centerPhone').value='+998';
            document.getElementById('centerPassword').value='';
            document.getElementById('centerPassword2').value='';
            document.getElementById('centerAddress').value='';
        }
        function closeAddModal(){document.getElementById('addModal').classList.remove('active');}
        async function createCenter(){
            const center={
                name:document.getElementById('centerName').value,
                phone:document.getElementById('centerPhone').value,
                password:document.getElementById('centerPassword').value,
                password2:document.getElementById('centerPassword2').value,
                address:document.getElementById('centerAddress').value,
                tariff:document.getElementById('centerTariff').value
            };
            if(!center.name||!center.phone||!center.password||!center.password2||!center.address){alert('Barcha maydonlarni to\'ldiring!');return;}
            if(center.password!==center.password2){alert('Parollar mos kelmadi!');return;}
            await fetch(API_BASE+'/admin/centers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(center)});
            closeAddModal();
            loadDashboard();
        }
        function logout(){
            document.getElementById('loginContainer').style.display='flex';
            document.getElementById('dashboard').classList.remove('active');
            document.getElementById('loginStep1').style.display='block';
            document.getElementById('loginStep2').style.display='none';
        }
        document.getElementById('loginBtn1').onclick=login1;
        document.getElementById('loginBtn2').onclick=login2;
        document.getElementById('logoutBtn').onclick=logout;
        document.getElementById('addCenterBtn').onclick=openAddModal;
        document.getElementById('cancelModalBtn').onclick=closeAddModal;
        document.getElementById('submitCenterBtn').onclick=createCenter;
    </script>
</body>
</html>
    """)

# ==================== FILE RESPONSES ====================
@app.get("/moderator")
async def moderator():
    if os.path.exists("moderator.html"):
        return FileResponse("moderator.html")
    return HTMLResponse("moderator.html not found")

@app.get("/students")
async def students():
    if os.path.exists("students.html"):
        return FileResponse("students.html")
    return HTMLResponse("students.html not found")

@app.get("/teachers")
async def teachers():
    if os.path.exists("teachers.html"):
        return FileResponse("teachers.html")
    return HTMLResponse("teachers.html not found")

@app.get("/parents")
async def parents():
    if os.path.exists("parents.html"):
        return FileResponse("parents.html")
    return HTMLResponse("parents.html not found")

# ==================== MIDDLEWARE & STARTUP ====================
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_init():
    try:
        await db.telegram_links.create_index("phone", unique=True, sparse=True)
        await db.telegram_links.create_index("chat_id", unique=True, sparse=True)
        await db.education_centers.create_index("phone", unique=True, sparse=True)
        await db.teachers.create_index("phone")
        await db.students.create_index("phone")
        await db.students.create_index("center_id")
        await db.groups.create_index("center_id")
        await db.rooms.create_index("center_id")
        await db.courses.create_index("center_id")
        await db.attendance.create_index([("group_id", 1), ("date", 1)])
        await db.store_items.create_index("center_id")
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"Database init error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
