from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
import asyncio
from telegram import Bot
from telegram.error import TelegramError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Admin credentials from Railway environment variables
ADMIN_PHONE = os.environ.get('ADMIN_PHONE', '')
ADMIN_PASSWORD1 = os.environ.get('ADMIN_PASSWORD1', '')
ADMIN_PASSWORD2 = os.environ.get('ADMIN_PASSWORD2', '')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

# In-memory storage for verification codes
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
    tariff: str  # Pro, Pro+, VIP
    status: str = "active"  # active, frozen
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
    schedule_days: List[int]  # 1-6 (Monday-Saturday)
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
    status: str = "active"  # active, frozen
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
    status: str = "pending"  # pending, completed
    created_date: datetime = Field(default_factory=datetime.utcnow)

class Attendance(BaseModel):
    group_id: str
    student_id: str
    date: str
    status: int  # 1 = present, 0 = absent
    coins_awarded: int = 0
    created_date: datetime = Field(default_factory=datetime.utcnow)

class Transaction(BaseModel):
    student_id: str
    amount: float
    transaction_type: str  # deduct, topup
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

async def send_telegram_code(phone: str, code: str):
    """Send verification code via Telegram bot - stores phone->chat_id mapping"""
    try:
        # Store code with phone number
        verification_codes[phone] = {
            'code': code,
            'expires': datetime.utcnow() + timedelta(minutes=5)
        }
        
        if not telegram_bot:
            logger.warning("Telegram bot not configured (TELEGRAM_BOT_TOKEN missing)")
            return True  # Still allow login without telegram in dev
        
        # Check if user already has telegram chat_id linked
        user_link = await db.telegram_links.find_one({"phone": phone})
        if user_link:
            try:
                await telegram_bot.send_message(
                    chat_id=user_link['chat_id'],
                    text=f"🔐 Tasdiqlash kodi: {code}\n\n✅ Ushbu kodni ilovaga kiriting.\n\nKod 5 daqiqada eskirsadi."
                )
                return True
            except Exception as e:
                logging.error(f"Telegram send error: {e}")
        return True  # Still return true even if not linked yet (code is stored)
    except Exception as e:
        logging.error(f"Telegram error: {e}")
        return False

def get_daily_fee(monthly_fee: float, schedule_days: List[int]) -> float:
    """Calculate daily fee based on monthly fee and schedule"""
    classes_per_month = len(schedule_days) * 4  # Approximate
    if classes_per_month == 0:
        return 0
    return monthly_fee / classes_per_month

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                result['id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = [serialize_doc(item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        return result
    return doc

# ==================== ADMIN PANEL ENDPOINTS ====================

@api_router.post("/admin/login")
async def admin_login(phone: str = Body(...), password: str = Body(...)):
    """Admin first login - phone + password from Railway env variables"""
    if not ADMIN_PHONE or not ADMIN_PASSWORD1:
        raise HTTPException(status_code=500, detail="Admin credentials not configured in Railway environment variables")
    if phone == ADMIN_PHONE and password == ADMIN_PASSWORD1:
        return {"success": True, "message": "First password correct"}
    raise HTTPException(status_code=401, detail="Login xato")

@api_router.post("/admin/login2")
async def admin_login2(phone: str = Body(...), password2: str = Body(...)):
    """Admin second login - second password from Railway env variables"""
    if not ADMIN_PHONE or not ADMIN_PASSWORD2:
        raise HTTPException(status_code=500, detail="Admin credentials not configured in Railway environment variables")
    if phone == ADMIN_PHONE and password2 == ADMIN_PASSWORD2:
        return {
            "success": True,
            "token": "admin_token_secure",
            "message": "Login successful"
        }
    raise HTTPException(status_code=401, detail="Ikkinchi parol xato")

@api_router.get("/admin/dashboard")
async def admin_dashboard():
    """Admin dashboard statistics"""
    total_centers = await db.education_centers.count_documents({})
    active_centers = await db.education_centers.count_documents({"status": "active"})
    total_students = await db.students.count_documents({})
    
    return {
        "total_centers": total_centers,
        "active_centers": active_centers,
        "total_students": total_students,
        "monthly_revenue": 0  # Calculate from payments
    }

@api_router.post("/admin/centers")
async def create_center(center: EducationCenter):
    """Create new education center"""
    # Check tariff limits
    if center.tariff == "Pro":
        max_students = 100
        max_groups = 5
        max_teachers = 5
    elif center.tariff == "Pro+":
        max_students = 300
        max_groups = 50
        max_teachers = 50
    else:  # VIP
        max_students = -1  # Unlimited
        max_groups = -1
        max_teachers = -1
    
    center_dict = center.dict()
    center_dict['password'] = hash_password(center.password)
    center_dict['password2'] = hash_password(center.password2)
    center_dict['max_students'] = max_students
    center_dict['max_groups'] = max_groups
    center_dict['max_teachers'] = max_teachers
    
    result = await db.education_centers.insert_one(center_dict)
    center_dict['id'] = str(result.inserted_id)
    
    return serialize_doc(center_dict)

@api_router.get("/admin/centers")
async def get_centers():
    """Get all education centers"""
    centers = await db.education_centers.find().to_list(1000)
    return [serialize_doc(center) for center in centers]

@api_router.put("/admin/centers/{center_id}/status")
async def update_center_status(center_id: str, status: str = Body(..., embed=True)):
    """Freeze or activate education center"""
    result = await db.education_centers.update_one(
        {"_id": ObjectId(center_id)},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Center topilmadi")
    return {"success": True, "message": f"Status {status} ga o'zgartirildi"}

@api_router.put("/admin/centers/{center_id}/tariff")
async def update_center_tariff(center_id: str, tariff: str = Body(..., embed=True)):
    """Update center tariff"""
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
        raise HTTPException(status_code=404, detail="Center topilmadi")
    return {"success": True, "message": "Tariff o'zgartirildi"}

@api_router.delete("/admin/centers/{center_id}")
async def delete_center(center_id: str):
    """Delete education center"""
    result = await db.education_centers.delete_one({"_id": ObjectId(center_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Center topilmadi")
    return {"success": True, "message": "Center o'chirildi"}

# ==================== EDU BOSS ENDPOINTS ====================

@api_router.post("/boss/login")
async def boss_login(phone: str = Body(...), password: str = Body(...)):
    """Boss login"""
    center = await db.education_centers.find_one({"phone": phone})
    if not center:
        raise HTTPException(status_code=404, detail="Telefon raqam topilmadi")
    
    if center['status'] == 'frozen':
        raise HTTPException(status_code=403, detail="Hisobingiz muzlatilgan")
    
    if not verify_password(password, center['password']):
        raise HTTPException(status_code=401, detail="Parol xato")
    
    return {
        "success": True,
        "center_id": str(center['_id']),
        "center_name": center['name'],
        "tariff": center['tariff']
    }

@api_router.get("/boss/dashboard/{center_id}")
async def boss_dashboard(center_id: str):
    """Boss dashboard"""
    students_count = await db.students.count_documents({"center_id": center_id})
    groups_count = await db.groups.count_documents({"center_id": center_id})
    teachers_count = await db.teachers.count_documents({"center_id": center_id})
    
    # Calculate monthly revenue
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
    """Create room"""
    room_dict = room.dict()
    result = await db.rooms.insert_one(room_dict)
    room_dict['id'] = str(result.inserted_id)
    return serialize_doc(room_dict)

@api_router.get("/boss/rooms/{center_id}")
async def get_rooms(center_id: str):
    """Get rooms"""
    rooms = await db.rooms.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(room) for room in rooms]

@api_router.delete("/boss/rooms/{room_id}")
async def delete_room(room_id: str):
    """Delete room"""
    await db.rooms.delete_one({"_id": ObjectId(room_id)})
    return {"success": True}

# COURSES
@api_router.post("/boss/courses")
async def create_course(course: Course):
    """Create course"""
    course_dict = course.dict()
    result = await db.courses.insert_one(course_dict)
    course_dict['id'] = str(result.inserted_id)
    return serialize_doc(course_dict)

@api_router.get("/boss/courses/{center_id}")
async def get_courses(center_id: str):
    """Get courses"""
    courses = await db.courses.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(course) for course in courses]

# GROUPS
@api_router.post("/boss/groups")
async def create_group(group: Group):
    """Create group"""
    group_dict = group.dict()
    result = await db.groups.insert_one(group_dict)
    group_dict['id'] = str(result.inserted_id)
    return serialize_doc(group_dict)

@api_router.get("/boss/groups/{center_id}")
async def get_groups(center_id: str):
    """Get groups"""
    groups = await db.groups.find({"center_id": center_id}).to_list(1000)
    result = []
    for group in groups:
        group_data = serialize_doc(group)
        # Get teacher info
        if group.get('teacher_id'):
            teacher = await db.teachers.find_one({"_id": ObjectId(group['teacher_id'])})
            if teacher:
                group_data['teacher_name'] = teacher['name']
        result.append(group_data)
    return result

@api_router.put("/boss/groups/{group_id}")
async def update_group(group_id: str, group: Group):
    """Update group"""
    result = await db.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": group.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    return {"success": True}

@api_router.delete("/boss/groups/{group_id}")
async def delete_group(group_id: str):
    """Delete group"""
    await db.groups.delete_one({"_id": ObjectId(group_id)})
    return {"success": True}

# TEACHERS
@api_router.post("/boss/teachers")
async def create_teacher(teacher: Teacher):
    """Create teacher"""
    teacher_dict = teacher.dict()
    teacher_dict['password'] = hash_password(teacher.password) if teacher.password else None
    result = await db.teachers.insert_one(teacher_dict)
    teacher_dict['id'] = str(result.inserted_id)
    return serialize_doc(teacher_dict)

@api_router.get("/boss/teachers/{center_id}")
async def get_teachers(center_id: str):
    """Get teachers"""
    teachers = await db.teachers.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(teacher) for teacher in teachers]

@api_router.put("/boss/teachers/{teacher_id}")
async def update_teacher(teacher_id: str, teacher: Teacher):
    """Update teacher"""
    teacher_dict = teacher.dict()
    if teacher.password:
        teacher_dict['password'] = hash_password(teacher.password)
    result = await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$set": teacher_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ustoz topilmadi")
    return {"success": True}

@api_router.delete("/boss/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str):
    """Delete teacher"""
    await db.teachers.delete_one({"_id": ObjectId(teacher_id)})
    return {"success": True}

# STUDENTS
@api_router.post("/boss/students")
async def create_student(student: Student):
    """Create student"""
    student_dict = student.dict()
    student_dict['password'] = hash_password(student.password) if student.password else None
    result = await db.students.insert_one(student_dict)
    
    # Update group students count
    await db.groups.update_one(
        {"_id": ObjectId(student.group_id)},
        {"$inc": {"students_count": 1}}
    )
    
    student_dict['id'] = str(result.inserted_id)
    return serialize_doc(student_dict)

@api_router.get("/boss/students/{center_id}")
async def get_students(center_id: str):
    """Get students"""
    students = await db.students.find({"center_id": center_id}).to_list(1000)
    result = []
    for student in students:
        student_data = serialize_doc(student)
        # Get group info
        group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
        if group:
            student_data['group_name'] = group['name']
        # Get course info
        course = await db.courses.find_one({"_id": ObjectId(student['course_id'])})
        if course:
            student_data['course_name'] = course['name']
        result.append(student_data)
    return result

@api_router.put("/boss/students/{student_id}/status")
async def update_student_status(student_id: str, status: str = Body(..., embed=True)):
    """Freeze or activate student"""
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return {"success": True}

@api_router.put("/boss/students/{student_id}/balance")
async def topup_student_balance(student_id: str, amount: float = Body(..., embed=True)):
    """Top up student balance"""
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"balance": amount}}
    )
    
    # Record transaction
    transaction = Transaction(
        student_id=student_id,
        amount=amount,
        transaction_type="topup",
        description="Balans to'ldirildi"
    )
    await db.transactions.insert_one(transaction.dict())
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return {"success": True}

@api_router.delete("/boss/students/{student_id}")
async def delete_student(student_id: str):
    """Delete student"""
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if student:
        await db.groups.update_one(
            {"_id": ObjectId(student['group_id'])},
            {"$inc": {"students_count": -1}}
        )
    await db.students.delete_one({"_id": ObjectId(student_id)})
    return {"success": True}

# STORE
@api_router.post("/boss/store")
async def create_store_item(item: StoreItem):
    """Create store item"""
    item_dict = item.dict()
    result = await db.store_items.insert_one(item_dict)
    item_dict['id'] = str(result.inserted_id)
    return serialize_doc(item_dict)

@api_router.get("/boss/store/{center_id}")
async def get_store_items(center_id: str):
    """Get store items"""
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(item) for item in items]

@api_router.get("/boss/store/orders/{center_id}")
async def get_store_orders(center_id: str):
    """Get store orders"""
    orders = await db.store_orders.find().to_list(1000)
    result = []
    for order in orders:
        # Check if student belongs to this center
        student = await db.students.find_one({"_id": ObjectId(order['student_id'])})
        if student and student['center_id'] == center_id:
            order_data = serialize_doc(order)
            order_data['student_name'] = student['name']
            # Get item info
            item = await db.store_items.find_one({"_id": ObjectId(order['item_id'])})
            if item:
                order_data['item_name'] = item['name']
                order_data['coin_price'] = item['coin_price']
            result.append(order_data)
    return result

@api_router.put("/boss/store/orders/{order_id}/complete")
async def complete_order(order_id: str):
    """Complete store order"""
    result = await db.store_orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "completed"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    return {"success": True}

@api_router.delete("/boss/store/{item_id}")
async def delete_store_item(item_id: str):
    """Delete store item"""
    await db.store_items.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}

# ==================== TEACHER ENDPOINTS ====================

@api_router.post("/teacher/request-code")
async def teacher_request_code(phone: str = Body(..., embed=True)):
    """Request verification code"""
    teacher = await db.teachers.find_one({"phone": phone})
    if not teacher:
        raise HTTPException(status_code=404, detail="Telefon raqam topilmadi")
    
    code = generate_verification_code()
    success = await send_telegram_code(phone, code)
    
    return {
        "success": success,
        "message": "Telegram botimizga o'ting va kodni oling",
        "bot_link": f"https://t.me/YourBotUsername"
    }

@api_router.post("/teacher/verify-code")
async def teacher_verify_code(phone: str = Body(...), code: str = Body(...)):
    """Verify code"""
    stored = verification_codes.get(phone)
    if not stored:
        raise HTTPException(status_code=400, detail="Kod topilmadi yoki muddati tugagan")
    
    if stored['code'] != code:
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")
    
    if datetime.utcnow() > stored['expires']:
        raise HTTPException(status_code=400, detail="Kod muddati tugagan")
    
    # Remove used code
    del verification_codes[phone]
    
    teacher = await db.teachers.find_one({"phone": phone})
    return {
        "success": True,
        "teacher_id": str(teacher['_id']),
        "name": teacher['name'],
        "has_password": teacher.get('password') is not None
    }

@api_router.post("/teacher/set-password")
async def teacher_set_password(teacher_id: str = Body(...), password: str = Body(...)):
    """Set teacher password"""
    result = await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$set": {"password": hash_password(password)}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ustoz topilmadi")
    return {"success": True}

@api_router.post("/teacher/login")
async def teacher_login(phone: str = Body(...), password: str = Body(...)):
    """Teacher login with password"""
    teacher = await db.teachers.find_one({"phone": phone})
    if not teacher or not teacher.get('password'):
        raise HTTPException(status_code=404, detail="Telefon raqam topilmadi")
    
    if not verify_password(password, teacher['password']):
        raise HTTPException(status_code=401, detail="Parol xato")
    
    return {
        "success": True,
        "teacher_id": str(teacher['_id']),
        "name": teacher['name']
    }

@api_router.get("/teacher/dashboard/{teacher_id}")
async def teacher_dashboard(teacher_id: str):
    """Teacher dashboard"""
    teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Ustoz topilmadi")
    
    # Get groups
    groups = await db.groups.find({"teacher_id": teacher_id}).to_list(1000)
    
    # Get today's classes
    today = datetime.utcnow().weekday() + 1  # 1-7
    today_groups = [g for g in groups if today in g.get('schedule_days', [])]
    
    return {
        "total_groups": len(groups),
        "today_classes": len(today_groups),
        "groups": [serialize_doc(g) for g in today_groups]
    }

@api_router.get("/teacher/groups/{teacher_id}")
async def teacher_get_groups(teacher_id: str):
    """Get teacher's groups"""
    groups = await db.groups.find({"teacher_id": teacher_id}).to_list(1000)
    return [serialize_doc(group) for group in groups]

@api_router.get("/teacher/group/{group_id}/students")
async def teacher_get_students(group_id: str):
    """Get students in group"""
    students = await db.students.find({"group_id": group_id}).to_list(1000)
    return [serialize_doc(student) for student in students]

@api_router.post("/teacher/award-coin")
async def teacher_award_coin(student_id: str = Body(...), coins: int = Body(...)):
    """Award coins to student"""
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"coins": coins}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return {"success": True}

@api_router.post("/teacher/attendance")
async def mark_attendance(
    group_id: str = Body(...),
    student_id: str = Body(...),
    status: int = Body(...),
    date: str = Body(...)
):
    """Mark student attendance"""
    attendance = Attendance(
        group_id=group_id,
        student_id=student_id,
        date=date,
        status=status,
        coins_awarded=0
    )
    await db.attendance.insert_one(attendance.dict())
    
    # Deduct balance if present
    if status == 1:
        student = await db.students.find_one({"_id": ObjectId(student_id)})
        if student and student['status'] == 'active':
            group = await db.groups.find_one({"_id": ObjectId(group_id)})
            course = await db.courses.find_one({"_id": ObjectId(student['course_id'])})
            
            if group and course:
                daily_fee = get_daily_fee(course['monthly_fee'], group['schedule_days'])
                
                # Deduct from balance
                await db.students.update_one(
                    {"_id": ObjectId(student_id)},
                    {"$inc": {"balance": -daily_fee}}
                )
                
                # Record transaction
                transaction = Transaction(
                    student_id=student_id,
                    amount=daily_fee,
                    transaction_type="deduct",
                    description=f"Dars uchun to'lov ({date})"
                )
                await db.transactions.insert_one(transaction.dict())
    
    return {"success": True}

# ==================== STUDENT ENDPOINTS ====================

@api_router.post("/student/request-code")
async def student_request_code(phone: str = Body(...), user_type: str = Body(...)):
    """Request verification code for student or parent"""
    # Check if phone exists
    if user_type == "student":
        user = await db.students.find_one({"phone": phone})
    else:  # parent
        user = await db.students.find_one({"parent_phone": phone})
    
    if not user:
        raise HTTPException(status_code=404, detail="Telefon raqam topilmadi")
    
    code = generate_verification_code()
    success = await send_telegram_code(phone, code)
    
    return {
        "success": success,
        "message": "Telegram botimizga o'ting va kodni oling",
        "bot_link": f"https://t.me/YourBotUsername"
    }

@api_router.post("/student/verify-code")
async def student_verify_code(phone: str = Body(...), code: str = Body(...), user_type: str = Body(...)):
    """Verify code for student"""
    stored = verification_codes.get(phone)
    if not stored:
        raise HTTPException(status_code=400, detail="Kod topilmadi")
    
    if stored['code'] != code:
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")
    
    if datetime.utcnow() > stored['expires']:
        raise HTTPException(status_code=400, detail="Kod muddati tugagan")
    
    del verification_codes[phone]
    
    if user_type == "student":
        student = await db.students.find_one({"phone": phone})
    else:
        student = await db.students.find_one({"parent_phone": phone})
    
    if not student:
        raise HTTPException(status_code=404, detail="Student topilmadi")
    
    return {
        "success": True,
        "student_id": str(student['_id']),
        "name": student['name'],
        "has_password": student.get('password') is not None
    }

@api_router.post("/student/set-password")
async def student_set_password(student_id: str = Body(...), password: str = Body(...)):
    """Set student password"""
    result = await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"password": hash_password(password)}}
    )
    return {"success": True}

@api_router.post("/student/login")
async def student_login(phone: str = Body(...), password: str = Body(...), user_type: str = Body(...)):
    """Student login with password"""
    if user_type == "student":
        student = await db.students.find_one({"phone": phone})
    else:
        student = await db.students.find_one({"parent_phone": phone})
    
    if not student or not student.get('password'):
        raise HTTPException(status_code=404, detail="Telefon raqam topilmadi")
    
    if not verify_password(password, student['password']):
        raise HTTPException(status_code=401, detail="Parol xato")
    
    return {
        "success": True,
        "student_id": str(student['_id']),
        "name": student['name']
    }

@api_router.get("/student/dashboard/{student_id}")
async def student_dashboard(student_id: str):
    """Student dashboard"""
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    
    # Get group info
    group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
    
    # Get attendance
    attendance_records = await db.attendance.find({"student_id": student_id}).to_list(1000)
    
    # Get upcoming classes
    today = datetime.utcnow().weekday() + 1
    upcoming_classes = []
    if group:
        for day in group.get('schedule_days', []):
            if day >= today:
                upcoming_classes.append({
                    "day": day,
                    "time": f"{group['time_start']} - {group['time_end']}",
                    "subject": group['subject'],
                    "room": group['room']
                })
    
    return {
        "name": student['name'],
        "balance": student.get('balance', 0),
        "coins": student.get('coins', 0),
        "group_name": group['name'] if group else "",
        "attendance_count": len([a for a in attendance_records if a['status'] == 1]),
        "upcoming_classes": upcoming_classes
    }

@api_router.get("/student/calendar/{student_id}")
async def student_calendar(student_id: str):
    """Get student calendar"""
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    
    # Get group
    group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
    if not group:
        return []
    
    # Get teacher
    teacher = None
    if group.get('teacher_id'):
        teacher = await db.teachers.find_one({"_id": ObjectId(group['teacher_id'])})
    
    # Get attendance records
    attendance_records = await db.attendance.find({"student_id": student_id}).to_list(1000)
    
    return {
        "schedule_days": group.get('schedule_days', []),
        "time": f"{group['time_start']} - {group['time_end']}",
        "subject": group['subject'],
        "room": group['room'],
        "teacher_name": teacher['name'] if teacher else "",
        "attendance": [serialize_doc(a) for a in attendance_records]
    }

@api_router.get("/student/ranking/{student_id}")
async def student_ranking(student_id: str):
    """Get student rankings"""
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    
    # Group ranking
    group_students = await db.students.find({"group_id": student['group_id']}).sort("coins", -1).to_list(1000)
    group_ranking = [{"name": s['name'], "coins": s.get('coins', 0)} for s in group_students]
    
    # Center ranking
    center_students = await db.students.find({"center_id": student['center_id']}).sort("coins", -1).to_list(1000)
    center_ranking = [{"name": s['name'], "coins": s.get('coins', 0)} for s in center_students[:20]]
    
    return {
        "group_ranking": group_ranking,
        "center_ranking": center_ranking,
        "my_coins": student.get('coins', 0)
    }

@api_router.get("/student/store/{center_id}")
async def student_get_store(center_id: str):
    """Get store items for student"""
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(item) for item in items]

@api_router.post("/student/store/order")
async def student_create_order(student_id: str = Body(...), item_id: str = Body(...)):
    """Create store order"""
    # Get student
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    
    # Get item
    item = await db.store_items.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    
    # Check coins
    if student.get('coins', 0) < item['coin_price']:
        raise HTTPException(status_code=400, detail="Yetarli coin yo'q")
    
    # Deduct coins
    await db.students.update_one(
        {"_id": ObjectId(student_id)},
        {"$inc": {"coins": -item['coin_price']}}
    )
    
    # Create order
    order = StoreOrder(
        student_id=student_id,
        item_id=item_id,
        status="pending"
    )
    result = await db.store_orders.insert_one(order.dict())
    
    return {"success": True, "order_id": str(result.inserted_id)}

@api_router.get("/student/profile/{student_id}")
async def student_profile(student_id: str):
    """Get student profile"""
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    
    return serialize_doc(student)

# ==================== ADMIN PANEL WEB PAGE ====================

@api_router.get("/admin-panel", response_class=HTMLResponse)
async def admin_panel_page():
    """Admin panel web page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Katta Admin Panel</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
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
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                width: 100%;
                max-width: 400px;
            }
            .login-box h2 {
                margin-bottom: 30px;
                color: #333;
                text-align: center;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            .btn {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .error {
                color: #e74c3c;
                font-size: 14px;
                margin-top: 10px;
                text-align: center;
            }
            .dashboard {
                display: none;
            }
            .dashboard.active {
                display: block;
            }
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header h1 {
                color: #333;
            }
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
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .stat-card h3 {
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }
            .stat-card p {
                color: #333;
                font-size: 32px;
                font-weight: bold;
            }
            .centers-section {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .section-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .section-header h2 {
                color: #333;
            }
            .add-btn {
                padding: 10px 20px;
                background: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .centers-list {
                display: grid;
                gap: 15px;
            }
            .center-card {
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .center-info h3 {
                color: #333;
                margin-bottom: 5px;
            }
            .center-info p {
                color: #666;
                font-size: 14px;
            }
            .center-actions button {
                margin-left: 10px;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-edit {
                background: #3498db;
                color: white;
            }
            .btn-freeze {
                background: #f39c12;
                color: white;
            }
            .btn-delete {
                background: #e74c3c;
                color: white;
            }
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
            .modal.active {
                display: flex;
            }
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
            }
            .modal-content h2 {
                margin-bottom: 20px;
                color: #333;
            }
            .modal-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .modal-actions button {
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn-cancel {
                background: #95a5a6;
                color: white;
            }
            .btn-submit {
                background: #2ecc71;
                color: white;
            }
            .tariff-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            .tariff-pro {
                background: #3498db;
                color: white;
            }
            .tariff-proplus {
                background: #9b59b6;
                color: white;
            }
            .tariff-vip {
                background: #f39c12;
                color: white;
            }
            .status-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            .status-active {
                background: #2ecc71;
                color: white;
            }
            .status-frozen {
                background: #e74c3c;
                color: white;
            }
        </style>
    </head>
    <body>
        <div id="loginContainer" class="login-container">
            <div class="login-box">
                <h2>🔐 Katta Admin Panel</h2>
                <div id="loginStep1">
                    <div class="form-group">
                        <label>Telefon raqam</label>
                        <input type="text" id="phone" placeholder="+998 90 123 45 67">
                    </div>
                    <div class="form-group">
                        <label>Parol 1</label>
                        <input type="password" id="password1" placeholder="Birinchi parol">
                    </div>
                    <button class="btn" onclick="login1()">Kirish</button>
                    <div id="error1" class="error"></div>
                </div>
                <div id="loginStep2" style="display:none;">
                    <div class="form-group">
                        <label>Parol 2</label>
                        <input type="password" id="password2" placeholder="Ikkinchi parol">
                    </div>
                    <button class="btn" onclick="login2()">Tasdiqlash</button>
                    <div id="error2" class="error"></div>
                </div>
            </div>
        </div>

        <div id="dashboard" class="dashboard">
            <div class="container">
                <div class="header">
                    <h1>📊 Admin Dashboard</h1>
                    <button class="logout-btn" onclick="logout()">Chiqish</button>
                </div>

                <div class="stats">
                    <div class="stat-card">
                        <h3>Jami O'quv Markazlar</h3>
                        <p id="totalCenters">0</p>
                    </div>
                    <div class="stat-card">
                        <h3>Faol Markazlar</h3>
                        <p id="activeCenters">0</p>
                    </div>
                    <div class="stat-card">
                        <h3>Jami O'quvchilar</h3>
                        <p id="totalStudents">0</p>
                    </div>
                </div>

                <div class="centers-section">
                    <div class="section-header">
                        <h2>O'quv Markazlar</h2>
                        <button class="add-btn" onclick="openAddModal()">+ Yangi Markaz</button>
                    </div>
                    <div id="centersList" class="centers-list"></div>
                </div>
            </div>
        </div>

        <!-- Add Center Modal -->
        <div id="addModal" class="modal">
            <div class="modal-content">
                <h2>Yangi O'quv Markaz</h2>
                <div class="form-group">
                    <label>Nomi</label>
                    <input type="text" id="centerName" placeholder="Masalan: HDP Academy">
                </div>
                <div class="form-group">
                    <label>Telefon</label>
                    <input type="text" id="centerPhone" placeholder="+998 90 123 45 67">
                </div>
                <div class="form-group">
                    <label>Parol (Boss login uchun)</label>
                    <input type="password" id="centerPassword" placeholder="Parol">
                </div>
                <div class="form-group">
                    <label>Ikkinchi Parol</label>
                    <input type="password" id="centerPassword2" placeholder="Ikkinchi parol">
                </div>
                <div class="form-group">
                    <label>Manzil</label>
                    <input type="text" id="centerAddress" placeholder="Manzil">
                </div>
                <div class="form-group">
                    <label>Tarif</label>
                    <select id="centerTariff" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;">
                        <option value="Pro">Pro - 200,000 so'm (100 o'quvchi, 5 guruh, 5 ustoz)</option>
                        <option value="Pro+">Pro+ - 500,000 so'm (300 o'quvchi, 50 guruh, 50 ustoz)</option>
                        <option value="VIP">VIP - Cheksiz</option>
                    </select>
                </div>
                <div class="modal-actions">
                    <button class="btn-cancel" onclick="closeAddModal()">Bekor qilish</button>
                    <button class="btn-submit" onclick="createCenter()">Yaratish</button>
                </div>
            </div>
        </div>

        <script>
            const API_BASE = '/api';
            let currentPhone = '';

            async function login1() {
                const phone = document.getElementById('phone').value;
                const password1 = document.getElementById('password1').value;
                
                try {
                    const response = await fetch(`${API_BASE}/admin/login`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone, password: password1})
                    });
                    
                    if (response.ok) {
                        currentPhone = phone;
                        document.getElementById('loginStep1').style.display = 'none';
                        document.getElementById('loginStep2').style.display = 'block';
                    } else {
                        document.getElementById('error1').textContent = 'Login xato!';
                    }
                } catch (error) {
                    document.getElementById('error1').textContent = 'Xatolik yuz berdi!';
                }
            }

            async function login2() {
                const password2 = document.getElementById('password2').value;
                
                try {
                    const response = await fetch(`${API_BASE}/admin/login2`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({phone: currentPhone, password2})
                    });
                    
                    if (response.ok) {
                        document.getElementById('loginContainer').style.display = 'none';
                        document.getElementById('dashboard').classList.add('active');
                        loadDashboard();
                    } else {
                        document.getElementById('error2').textContent = 'Ikkinchi parol xato!';
                    }
                } catch (error) {
                    document.getElementById('error2').textContent = 'Xatolik yuz berdi!';
                }
            }

            function logout() {
                document.getElementById('loginContainer').style.display = 'flex';
                document.getElementById('dashboard').classList.remove('active');
                document.getElementById('loginStep1').style.display = 'block';
                document.getElementById('loginStep2').style.display = 'none';
            }

            async function loadDashboard() {
                try {
                    const response = await fetch(`${API_BASE}/admin/dashboard`);
                    const data = await response.json();
                    
                    document.getElementById('totalCenters').textContent = data.total_centers;
                    document.getElementById('activeCenters').textContent = data.active_centers;
                    document.getElementById('totalStudents').textContent = data.total_students;
                    
                    loadCenters();
                } catch (error) {
                    console.error('Error loading dashboard:', error);
                }
            }

            async function loadCenters() {
                try {
                    const response = await fetch(`${API_BASE}/admin/centers`);
                    const centers = await response.json();
                    
                    const centersList = document.getElementById('centersList');
                    centersList.innerHTML = '';
                    
                    centers.forEach(center => {
                        const card = document.createElement('div');
                        card.className = 'center-card';
                        
                        const tariffClass = center.tariff ? center.tariff.toLowerCase().replace('+', 'plus') : '';
                        const statusText = center.status === 'active' ? 'Faol' : 'Muzlatilgan';
                        const freezeText = center.status === 'active' ? 'Muzlatish' : 'Faollashtirish';
                        
                        const infoDiv = document.createElement('div');
                        infoDiv.className = 'center-info';
                        
                        const h3 = document.createElement('h3');
                        h3.textContent = center.name + ' ';
                        
                        const tariffBadge = document.createElement('span');
                        tariffBadge.className = 'tariff-badge tariff-' + tariffClass;
                        tariffBadge.textContent = center.tariff;
                        h3.appendChild(tariffBadge);
                        h3.appendChild(document.createTextNode(' '));
                        
                        const statusBadge = document.createElement('span');
                        statusBadge.className = 'status-badge status-' + center.status;
                        statusBadge.textContent = statusText;
                        h3.appendChild(statusBadge);
                        
                        const p = document.createElement('p');
                        p.textContent = '📞 ' + center.phone + ' | 📍 ' + center.address;
                        
                        infoDiv.appendChild(h3);
                        infoDiv.appendChild(p);
                        
                        const actionsDiv = document.createElement('div');
                        actionsDiv.className = 'center-actions';
                        
                        const editBtn = document.createElement('button');
                        editBtn.className = 'btn-edit';
                        editBtn.textContent = "Tarif o'zgartirish";
                        editBtn.onclick = function() { updateTariff(center.id); };
                        
                        const freezeBtn = document.createElement('button');
                        freezeBtn.className = 'btn-freeze';
                        freezeBtn.textContent = freezeText;
                        freezeBtn.onclick = function() { toggleStatus(center.id, center.status); };
                        
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'btn-delete';
                        deleteBtn.textContent = "O'chirish";
                        deleteBtn.onclick = function() { deleteCenter(center.id); };
                        
                        actionsDiv.appendChild(editBtn);
                        actionsDiv.appendChild(freezeBtn);
                        actionsDiv.appendChild(deleteBtn);
                        
                        card.appendChild(infoDiv);
                        card.appendChild(actionsDiv);
                        centersList.appendChild(card);
                    });
                } catch (error) {
                    console.error('Error loading centers:', error);
                }
            }

            function openAddModal() {
                document.getElementById('addModal').classList.add('active');
            }

            function closeAddModal() {
                document.getElementById('addModal').classList.remove('active');
            }

            async function createCenter() {
                const center = {
                    name: document.getElementById('centerName').value,
                    phone: document.getElementById('centerPhone').value,
                    password: document.getElementById('centerPassword').value,
                    password2: document.getElementById('centerPassword2').value,
                    address: document.getElementById('centerAddress').value,
                    tariff: document.getElementById('centerTariff').value
                };
                
                try {
                    const response = await fetch(`${API_BASE}/admin/centers`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(center)
                    });
                    
                    if (response.ok) {
                        closeAddModal();
                        loadDashboard();
                        alert('Markaz muvaffaqiyatli yaratildi!');
                    }
                } catch (error) {
                    alert('Xatolik yuz berdi!');
                }
            }

            async function toggleStatus(centerId, currentStatus) {
                const newStatus = currentStatus === 'active' ? 'frozen' : 'active';
                
                try {
                    const response = await fetch(`${API_BASE}/admin/centers/${centerId}/status`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({status: newStatus})
                    });
                    
                    if (response.ok) {
                        loadDashboard();
                    }
                } catch (error) {
                    alert('Xatolik yuz berdi!');
                }
            }

            async function updateTariff(centerId) {
                const tariff = prompt('Yangi tarif (Pro, Pro+, VIP):');
                if (tariff && ['Pro', 'Pro+', 'VIP'].includes(tariff)) {
                    try {
                        const response = await fetch(`${API_BASE}/admin/centers/${centerId}/tariff`, {
                            method: 'PUT',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({tariff})
                        });
                        
                        if (response.ok) {
                            loadDashboard();
                        }
                    } catch (error) {
                        alert('Xatolik yuz berdi!');
                    }
                }
            }

            async function deleteCenter(centerId) {
                if (confirm('Rostdan ham o\'chirmoqchimisiz?')) {
                    try {
                        const response = await fetch(`${API_BASE}/admin/centers/${centerId}`, {
                            method: 'DELETE'
                        });
                        
                        if (response.ok) {
                            loadDashboard();
                        }
                    } catch (error) {
                        alert('Xatolik yuz berdi!');
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ==================== TELEGRAM BOT WEBHOOK ====================

@api_router.post("/telegram/webhook")
async def telegram_webhook(update: dict = Body(...)):
    """Telegram bot webhook for receiving messages"""
    try:
        message = update.get('message', {})
        chat = message.get('chat', {})
        text = message.get('text', '')
        chat_id = chat.get('id')
        
        if text == '/start':
            await telegram_bot.send_message(
                chat_id=chat_id,
                text="👋 Salom! EDU TIZIM botiga xush kelibsiz.\n\n"
                     "Iltimos, telefon raqamingizni yuboring:\n"
                     "Misol: 998901234567\n\n"
                     "Bu raqam orqali tasdiqlash kodi olasiz."
            )
        elif text and text.startswith('998') and len(text) == 12:
            # Phone number received
            phone = text
            await db.telegram_links.update_one(
                {"phone": phone},
                {"$set": {"phone": phone, "chat_id": chat_id, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            
            # Check if there's pending verification code
            stored = verification_codes.get(phone)
            if stored:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"🔐 Tasdiqlash kodingiz: {stored['code']}\n\n✅ Ushbu kodni ilovaga kiriting."
                )
            else:
                await telegram_bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Telefon raqamingiz ({phone}) saqlandi.\n\nEndi ilovada login qiling, kod sizga avtomatik yuboriladi."
                )
        else:
            await telegram_bot.send_message(
                chat_id=chat_id,
                text="❓ Tushunmadim. Iltimos telefon raqamingizni yuboring:\nMisol: 998901234567"
            )
        
        return {"ok": True}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"ok": False}

@api_router.get("/telegram/setup")
async def setup_telegram_webhook(url: str):
    """Setup telegram webhook URL"""
    try:
        await telegram_bot.set_webhook(url=f"{url}/api/telegram/webhook")
        return {"success": True, "message": f"Webhook set to {url}/api/telegram/webhook"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_init():
    """Initialize DB collections and indexes on startup"""
    try:
        # Create collections if they don't exist by creating indexes
        await db.education_centers.create_index("phone", unique=True, sparse=True)
        await db.education_centers.create_index("status")
        
        await db.teachers.create_index("phone")
        await db.teachers.create_index("center_id")
        
        await db.students.create_index("phone")
        await db.students.create_index("center_id")
        await db.students.create_index("group_id")
        
        await db.groups.create_index("center_id")
        await db.rooms.create_index("center_id")
        await db.courses.create_index("center_id")
        
        await db.attendance.create_index([("group_id", 1), ("date", 1)])
        await db.attendance.create_index("student_id")
        
        await db.transactions.create_index("student_id")
        await db.store_items.create_index("center_id")
        await db.store_orders.create_index("student_id")
        await db.telegram_links.create_index("phone", unique=True, sparse=True)
        
        logger.info("✅ MongoDB collections and indexes initialized successfully")
    except Exception as e:
        logger.error(f"❌ DB initialization error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
