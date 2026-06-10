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

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    logger.error("MONGO_URL not set")
    raise Exception("MONGO_URL not set")

client = AsyncIOMotorClient(
    mongo_url,
    tls=True,
    tlsAllowInvalidCertificates=True,
    serverSelectionTimeoutMS=30000,
)
db = client[os.environ.get('DB_NAME', 'smart_edu')]

# Admin credentials
ADMIN_PHONE = os.environ.get('ADMIN_PHONE', '')
ADMIN_PASSWORD1 = os.environ.get('ADMIN_PASSWORD1', '')
ADMIN_PASSWORD2 = os.environ.get('ADMIN_PASSWORD2', '')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def serialize_doc(doc):
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

def get_daily_fee(monthly_fee: float, schedule_days: List[int]) -> float:
    classes_per_month = len(schedule_days) * 4
    if classes_per_month == 0:
        return 0
    return monthly_fee / classes_per_month

# ==================== TEST ENDPOINTS ====================

@api_router.get("/test")
async def test_api():
    return {"status": "ok", "message": "API is working"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mongodb": "connected" if client else "disconnected"
    }

# ==================== ADMIN PANEL ENDPOINTS ====================

@api_router.post("/admin/login")
async def admin_login(phone: str = Body(...), password: str = Body(...)):
    if not ADMIN_PHONE or not ADMIN_PASSWORD1:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")
    if phone == ADMIN_PHONE and password == ADMIN_PASSWORD1:
        return {"success": True, "message": "First password correct"}
    raise HTTPException(status_code=401, detail="Login xato")

@api_router.post("/admin/login2")
async def admin_login2(phone: str = Body(...), password2: str = Body(...)):
    if not ADMIN_PHONE or not ADMIN_PASSWORD2:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")
    if phone == ADMIN_PHONE and password2 == ADMIN_PASSWORD2:
        return {"success": True, "token": "admin_token_secure"}
    raise HTTPException(status_code=401, detail="Ikkinchi parol xato")

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
    centers = await db.education_centers.find().to_list(1000)
    return [serialize_doc(center) for center in centers]

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

# ==================== EDU BOSS ENDPOINTS ====================

@api_router.post("/boss/login")
async def boss_login(phone: str = Body(...), password: str = Body(...)):
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
    room_dict = room.dict()
    result = await db.rooms.insert_one(room_dict)
    room_dict['id'] = str(result.inserted_id)
    return serialize_doc(room_dict)

@api_router.get("/boss/rooms/{center_id}")
async def get_rooms(center_id: str):
    rooms = await db.rooms.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(room) for room in rooms]

@api_router.delete("/boss/rooms/{room_id}")
async def delete_room(room_id: str):
    await db.rooms.delete_one({"_id": ObjectId(room_id)})
    return {"success": True}

# COURSES
@api_router.post("/boss/courses")
async def create_course(course: Course):
    course_dict = course.dict()
    result = await db.courses.insert_one(course_dict)
    course_dict['id'] = str(result.inserted_id)
    return serialize_doc(course_dict)

@api_router.get("/boss/courses/{center_id}")
async def get_courses(center_id: str):
    courses = await db.courses.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(course) for course in courses]

# GROUPS
@api_router.post("/boss/groups")
async def create_group(group: Group):
    group_dict = group.dict()
    result = await db.groups.insert_one(group_dict)
    group_dict['id'] = str(result.inserted_id)
    return serialize_doc(group_dict)

@api_router.get("/boss/groups/{center_id}")
async def get_groups(center_id: str):
    groups = await db.groups.find({"center_id": center_id}).to_list(1000)
    result = []
    for group in groups:
        group_data = serialize_doc(group)
        if group.get('teacher_id'):
            teacher = await db.teachers.find_one({"_id": ObjectId(group['teacher_id'])})
            if teacher:
                group_data['teacher_name'] = teacher['name']
        result.append(group_data)
    return result

@api_router.put("/boss/groups/{group_id}")
async def update_group(group_id: str, group: Group):
    result = await db.groups.update_one({"_id": ObjectId(group_id)}, {"$set": group.dict()})
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
    teacher_dict = teacher.dict()
    teacher_dict['password'] = hash_password(teacher.password) if teacher.password else None
    result = await db.teachers.insert_one(teacher_dict)
    teacher_dict['id'] = str(result.inserted_id)
    return serialize_doc(teacher_dict)

@api_router.get("/boss/teachers/{center_id}")
async def get_teachers(center_id: str):
    teachers = await db.teachers.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(teacher) for teacher in teachers]

@api_router.put("/boss/teachers/{teacher_id}")
async def update_teacher(teacher_id: str, teacher: Teacher):
    teacher_dict = teacher.dict()
    if teacher.password:
        teacher_dict['password'] = hash_password(teacher.password)
    result = await db.teachers.update_one({"_id": ObjectId(teacher_id)}, {"$set": teacher_dict})
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
    student_dict = student.dict()
    student_dict['password'] = hash_password(student.password) if student.password else None
    result = await db.students.insert_one(student_dict)
    await db.groups.update_one({"_id": ObjectId(student.group_id)}, {"$inc": {"students_count": 1}})
    student_dict['id'] = str(result.inserted_id)
    return serialize_doc(student_dict)

@api_router.get("/boss/students/{center_id}")
async def get_students(center_id: str):
    students = await db.students.find({"center_id": center_id}).to_list(1000)
    result = []
    for student in students:
        student_data = serialize_doc(student)
        group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
        if group:
            student_data['group_name'] = group['name']
        course = await db.courses.find_one({"_id": ObjectId(student['course_id'])})
        if course:
            student_data['course_name'] = course['name']
        result.append(student_data)
    return result

@api_router.put("/boss/students/{student_id}/status")
async def update_student_status(student_id: str, status: str = Body(..., embed=True)):
    result = await db.students.update_one({"_id": ObjectId(student_id)}, {"$set": {"status": status}})
    if result.modified_count == 0:
        raise HTTPException(404, "O'quvchi topilmadi")
    return {"success": True}

@api_router.put("/boss/students/{student_id}/balance")
async def topup_student_balance(student_id: str, amount: float = Body(..., embed=True)):
    result = await db.students.update_one({"_id": ObjectId(student_id)}, {"$inc": {"balance": amount}})
    transaction = Transaction(student_id=student_id, amount=amount, transaction_type="topup", description="Balans to'ldirildi")
    await db.transactions.insert_one(transaction.dict())
    if result.modified_count == 0:
        raise HTTPException(404, "O'quvchi topilmadi")
    return {"success": True}

@api_router.delete("/boss/students/{student_id}")
async def delete_student(student_id: str):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if student:
        await db.groups.update_one({"_id": ObjectId(student['group_id'])}, {"$inc": {"students_count": -1}})
    await db.students.delete_one({"_id": ObjectId(student_id)})
    return {"success": True}

# STORE
@api_router.post("/boss/store")
async def create_store_item(item: StoreItem):
    item_dict = item.dict()
    result = await db.store_items.insert_one(item_dict)
    item_dict['id'] = str(result.inserted_id)
    return serialize_doc(item_dict)

@api_router.get("/boss/store/{center_id}")
async def get_store_items(center_id: str):
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(item) for item in items]

@api_router.get("/boss/store/orders/{center_id}")
async def get_store_orders(center_id: str):
    orders = await db.store_orders.find().to_list(1000)
    result = []
    for order in orders:
        student = await db.students.find_one({"_id": ObjectId(order['student_id'])})
        if student and student['center_id'] == center_id:
            order_data = serialize_doc(order)
            order_data['student_name'] = student['name']
            item = await db.store_items.find_one({"_id": ObjectId(order['item_id'])})
            if item:
                order_data['item_name'] = item['name']
                order_data['coin_price'] = item['coin_price']
            result.append(order_data)
    return result

@api_router.put("/boss/store/orders/{order_id}/complete")
async def complete_order(order_id: str):
    result = await db.store_orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "completed"}})
    if result.modified_count == 0:
        raise HTTPException(404, "Buyurtma topilmadi")
    return {"success": True}

@api_router.delete("/boss/store/{item_id}")
async def delete_store_item(item_id: str):
    await db.store_items.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}

# ==================== TEACHER ENDPOINTS ====================

@api_router.post("/teacher/login")
async def teacher_login(phone: str = Body(...), password: str = Body(...)):
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
    teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not teacher:
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
    return [serialize_doc(group) for group in groups]

@api_router.get("/teacher/group/{group_id}/students")
async def teacher_get_students(group_id: str):
    students = await db.students.find({"group_id": group_id}).to_list(1000)
    return [serialize_doc(student) for student in students]

@api_router.post("/teacher/award-coin")
async def teacher_award_coin(student_id: str = Body(...), coins: int = Body(...)):
    result = await db.students.update_one({"_id": ObjectId(student_id)}, {"$inc": {"coins": coins}})
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
    attendance = Attendance(group_id=group_id, student_id=student_id, date=date, status=status, coins_awarded=0)
    await db.attendance.insert_one(attendance.dict())
    
    if status == 1:
        student = await db.students.find_one({"_id": ObjectId(student_id)})
        if student and student['status'] == 'active':
            group = await db.groups.find_one({"_id": ObjectId(group_id)})
            course = await db.courses.find_one({"_id": ObjectId(student['course_id'])})
            if group and course:
                daily_fee = get_daily_fee(course['monthly_fee'], group['schedule_days'])
                await db.students.update_one({"_id": ObjectId(student_id)}, {"$inc": {"balance": -daily_fee}})
                transaction = Transaction(student_id=student_id, amount=daily_fee, transaction_type="deduct", description=f"Dars uchun to'lov ({date})")
                await db.transactions.insert_one(transaction.dict())
    return {"success": True}

# ==================== STUDENT ENDPOINTS ====================

@api_router.post("/student/login")
async def student_login(phone: str = Body(...), password: str = Body(...)):
    student = await db.students.find_one({"phone": phone})
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
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(404, "O'quvchi topilmadi")
    group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
    attendance_records = await db.attendance.find({"student_id": student_id}).to_list(1000)
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
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(404, "O'quvchi topilmadi")
    group = await db.groups.find_one({"_id": ObjectId(student['group_id'])})
    if not group:
        return []
    teacher = None
    if group.get('teacher_id'):
        teacher = await db.teachers.find_one({"_id": ObjectId(group['teacher_id'])})
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
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(404, "O'quvchi topilmadi")
    group_students = await db.students.find({"group_id": student['group_id']}).sort("coins", -1).to_list(1000)
    group_ranking = [{"name": s['name'], "coins": s.get('coins', 0)} for s in group_students]
    center_students = await db.students.find({"center_id": student['center_id']}).sort("coins", -1).to_list(1000)
    center_ranking = [{"name": s['name'], "coins": s.get('coins', 0)} for s in center_students[:20]]
    return {
        "group_ranking": group_ranking,
        "center_ranking": center_ranking,
        "my_coins": student.get('coins', 0)
    }

@api_router.get("/student/store/{center_id}")
async def student_get_store(center_id: str):
    items = await db.store_items.find({"center_id": center_id}).to_list(1000)
    return [serialize_doc(item) for item in items]

@api_router.post("/student/store/order")
async def student_create_order(student_id: str = Body(...), item_id: str = Body(...)):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(404, "O'quvchi topilmadi")
    item = await db.store_items.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(404, "Mahsulot topilmadi")
    if student.get('coins', 0) < item['coin_price']:
        raise HTTPException(400, "Yetarli coin yo'q")
    await db.students.update_one({"_id": ObjectId(student_id)}, {"$inc": {"coins": -item['coin_price']}})
    order = StoreOrder(student_id=student_id, item_id=item_id, status="pending")
    result = await db.store_orders.insert_one(order.dict())
    return {"success": True, "order_id": str(result.inserted_id)}

@api_router.get("/student/profile/{student_id}")
async def student_profile(student_id: str):
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(404, "O'quvchi topilmadi")
    return serialize_doc(student)

# ==================== ADMIN PANEL WEB PAGE ====================

@api_router.get("/admin-panel", response_class=HTMLResponse)
async def admin_panel_page():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="uz">
<head><meta charset="UTF-8"><title>Admin Panel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh}
.login-container{display:flex;justify-content:center;align-items:center;min-height:100vh}
.login-box{background:#fff;padding:40px;border-radius:10px;width:100%;max-width:400px}
.login-box h2{text-align:center;margin-bottom:30px}
.form-group{margin-bottom:20px}
.form-group input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px}
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:5px;cursor:pointer}
.error{color:#e74c3c;margin-top:10px;text-align:center}
.dashboard{display:none}
.dashboard.active{display:block}
.header{background:#fff;padding:20px;border-radius:10px;margin-bottom:20px;display:flex;justify-content:space-between}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:30px}
.stat-card{background:#fff;padding:30px;border-radius:10px;text-align:center}
.centers-section{background:#fff;padding:30px;border-radius:10px}
.section-header{display:flex;justify-content:space-between;margin-bottom:20px}
.add-btn{padding:10px 20px;background:#2ecc71;color:#fff;border:none;border-radius:5px;cursor:pointer}
.center-card{border:1px solid #ddd;padding:20px;border-radius:5px;margin-bottom:10px;display:flex;justify-content:space-between}
.btn-edit{background:#3498db;color:#fff;padding:5px 10px;border:none;border-radius:3px}
.btn-freeze{background:#f39c12;color:#fff;padding:5px 10px;border:none;border-radius:3px}
.btn-delete{background:#e74c3c;color:#fff;padding:5px 10px;border:none;border-radius:3px}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);justify-content:center;align-items:center}
.modal.active{display:flex}
.modal-content{background:#fff;padding:30px;border-radius:10px;width:90%;max-width:500px}
.modal-actions{display:flex;gap:10px;margin-top:20px}
</style>
</head>
<body>
<div class="login-container" id="loginContainer">
<div class="login-box">
<h2>Admin Panel</h2>
<div id="step1">
<div class="form-group"><input type="text" id="phone" placeholder="Telefon"></div>
<div class="form-group"><input type="password" id="pwd1" placeholder="Parol 1"></div>
<button class="btn" onclick="login1()">Kirish</button>
<div id="err1" class="error"></div>
</div>
<div id="step2" style="display:none">
<div class="form-group"><input type="password" id="pwd2" placeholder="Parol 2"></div>
<button class="btn" onclick="login2()">Tasdiqlash</button>
<div id="err2" class="error"></div>
</div>
</div>
</div>
<div class="dashboard" id="dashboard">
<div class="header"><h1>Admin Dashboard</h1><button class="btn" onclick="logout()" style="width:auto">Chiqish</button></div>
<div class="stats"><div class="stat-card"><h3>Jami Markazlar</h3><p id="totalCenters">0</p></div><div class="stat-card"><h3>Faol Markazlar</h3><p id="activeCenters">0</p></div><div class="stat-card"><h3>Jami O'quvchilar</h3><p id="totalStudents">0</p></div></div>
<div class="centers-section"><div class="section-header"><h2>O'quv Markazlar</h2><button class="add-btn" onclick="openAddModal()">+ Yangi Markaz</button></div><div id="centersList"></div></div>
</div>
<div class="modal" id="addModal"><div class="modal-content"><h2>Yangi Markaz</h2><div class="form-group"><input type="text" id="centerName" placeholder="Nomi"></div><div class="form-group"><input type="text" id="centerPhone" placeholder="Telefon"></div><div class="form-group"><input type="password" id="centerPwd" placeholder="Parol"></div><div class="form-group"><input type="password" id="centerPwd2" placeholder="Parol takror"></div><div class="form-group"><input type="text" id="centerAddress" placeholder="Manzil"></div><div class="form-group"><select id="centerTariff"><option value="Pro">Pro</option><option value="Pro+">Pro+</option><option value="VIP">VIP</option></select></div><div class="modal-actions"><button class="btn" onclick="closeAddModal()" style="background:#95a5a6">Bekor</button><button class="btn" onclick="createCenter()" style="background:#2ecc71">Yaratish</button></div></div></div>
<script>
const API_BASE='/api';let currentPhone='';
async function login1(){const p=document.getElementById('phone').value,p1=document.getElementById('pwd1').value;if(!p||!p1){document.getElementById('err1').innerText='Ma\'lumot kiriting!';return;}try{const r=await fetch(API_BASE+'/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p,password:p1})});if(r.ok){currentPhone=p;document.getElementById('step1').style.display='none';document.getElementById('step2').style.display='block';}else{document.getElementById('err1').innerText='Xato!';}}catch(e){document.getElementById('err1').innerText='Xatolik!';}}
async function login2(){const p2=document.getElementById('pwd2').value;if(!p2){document.getElementById('err2').innerText='Parolni kiriting!';return;}try{const r=await fetch(API_BASE+'/admin/login2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:currentPhone,password2:p2})});if(r.ok){document.getElementById('loginContainer').style.display='none';document.getElementById('dashboard').classList.add('active');loadDashboard();}else{document.getElementById('err2').innerText='Xato!';}}catch(e){document.getElementById('err2').innerText='Xatolik!';}}
async function loadDashboard(){try{const r=await fetch(API_BASE+'/admin/dashboard');const d=await r.json();document.getElementById('totalCenters').innerText=d.total_centers||0;document.getElementById('activeCenters').innerText=d.active_centers||0;document.getElementById('totalStudents').innerText=d.total_students||0;loadCenters();}catch(e){}}
async function loadCenters(){try{const r=await fetch(API_BASE+'/admin/centers');const c=await r.json();const list=document.getElementById('centersList');list.innerHTML='';c.forEach(x=>{list.innerHTML+=`<div class="center-card"><div><b>${x.name}</b><br>${x.phone}<br>${x.address}</div><div><button class="btn-edit" onclick="updateTariff('${x.id}')">Tarif</button><button class="btn-freeze" onclick="toggleStatus('${x.id}','${x.status}')">${x.status=='active'?'Muzlatish':'Faollashtirish'}</button><button class="btn-delete" onclick="deleteCenter('${x.id}')">O\'chirish</button></div></div>`;})}catch(e){}}
async function toggleStatus(id,s){const ns=s=='active'?'frozen':'active';await fetch(API_BASE+'/admin/centers/'+id+'/status',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:ns})});loadDashboard();}
async function updateTariff(id){const t=prompt('Yangi tarif (Pro, Pro+, VIP):');if(t)await fetch(API_BASE+'/admin/centers/'+id+'/tariff',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({tariff:t})});loadDashboard();}
async function deleteCenter(id){if(confirm('O\'chirmoqchimisiz?')){await fetch(API_BASE+'/admin/centers/'+id,{method:'DELETE'});loadDashboard();}}
function openAddModal(){document.getElementById('addModal').classList.add('active');}
function closeAddModal(){document.getElementById('addModal').classList.remove('active');}
async function createCenter(){const c={name:document.getElementById('centerName').value,phone:document.getElementById('centerPhone').value,password:document.getElementById('centerPwd').value,password2:document.getElementById('centerPwd2').value,address:document.getElementById('centerAddress').value,tariff:document.getElementById('centerTariff').value};if(c.password!==c.password2){alert('Parollar mos emas');return;}await fetch(API_BASE+'/admin/centers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(c)});closeAddModal();loadDashboard();}
function logout(){document.getElementById('loginContainer').style.display='flex';document.getElementById('dashboard').classList.remove('active');document.getElementById('step1').style.display='block';document.getElementById('step2').style.display='none';}
</script>
</body>
</html>
    """)

# ==================== FILE RESPONSES ====================

@app.get("/moderator")
async def moderator():
    return FileResponse("moderator.html")

@app.get("/students")
async def students():
    return FileResponse("students.html")

@app.get("/teachers")
async def teachers():
    return FileResponse("teachers.html")

@app.get("/parents")
async def parents():
    return FileResponse("parents.html")

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
        await db.education_centers.create_index("phone", unique=True, sparse=True)
        await db.teachers.create_index("phone")
        await db.students.create_index("phone")
        await db.groups.create_index("center_id")
        await db.rooms.create_index("center_id")
        await db.courses.create_index("center_id")
        await db.attendance.create_index([("group_id", 1), ("date", 1)])
        await db.store_items.create_index("center_id")
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"DB init error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
