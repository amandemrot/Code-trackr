from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Security
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Problem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    platform: str
    difficulty: str
    topics: List[str]
    date_completed: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProblemCreate(BaseModel):
    title: str
    platform: str
    difficulty: str
    topics: List[str]
    date_completed: str

class TopicStats(BaseModel):
    topic: str
    count: int
    percentage: float

class Stats(BaseModel):
    total_solved: int
    current_streak: int
    topic_wise: List[TopicStats]

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create user
    user = User(username=user_data.username)
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['password'] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"username": user_data.username})
    if not user_doc or not verify_password(user_data.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Create user object
    user = User(
        id=user_doc['id'],
        username=user_doc['username'],
        created_at=datetime.fromisoformat(user_doc['created_at'])
    )
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

# Problem endpoints
@api_router.post("/problems", response_model=Problem)
async def create_problem(problem_data: ProblemCreate, user_id: str = Depends(get_current_user)):
    problem = Problem(
        user_id=user_id,
        title=problem_data.title,
        platform=problem_data.platform,
        difficulty=problem_data.difficulty,
        topics=problem_data.topics,
        date_completed=problem_data.date_completed
    )
    
    problem_dict = problem.model_dump()
    problem_dict['created_at'] = problem_dict['created_at'].isoformat()
    
    await db.problems.insert_one(problem_dict)
    
    return problem

@api_router.get("/problems", response_model=List[Problem])
async def get_problems(user_id: str = Depends(get_current_user)):
    problems = await db.problems.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    for problem in problems:
        if isinstance(problem['created_at'], str):
            problem['created_at'] = datetime.fromisoformat(problem['created_at'])
    
    return problems

@api_router.get("/stats", response_model=Stats)
async def get_stats(user_id: str = Depends(get_current_user)):
    problems = await db.problems.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    total_solved = len(problems)
    
    # Calculate topic-wise stats
    topic_count = {}
    for problem in problems:
        for topic in problem['topics']:
            topic_count[topic] = topic_count.get(topic, 0) + 1
    
    topic_wise = []
    for topic, count in topic_count.items():
        percentage = (count / total_solved * 100) if total_solved > 0 else 0
        topic_wise.append(TopicStats(topic=topic, count=count, percentage=round(percentage, 1)))
    
    # Sort by count descending
    topic_wise.sort(key=lambda x: x.count, reverse=True)
    
    # Calculate streak
    current_streak = 0
    if problems:
        dates = sorted(set(p['date_completed'] for p in problems), reverse=True)
        today = datetime.now(timezone.utc).date()
        
        for i, date_str in enumerate(dates):
            date = datetime.fromisoformat(date_str).date()
            expected_date = today - timedelta(days=i)
            
            if date == expected_date:
                current_streak += 1
            else:
                break
    
    return Stats(total_solved=total_solved, current_streak=current_streak, topic_wise=topic_wise)

# Seed sample data endpoint
@api_router.post("/seed-data")
async def seed_data(user_id: str = Depends(get_current_user)):
    # Check if user already has problems
    existing_count = await db.problems.count_documents({"user_id": user_id})
    if existing_count > 0:
        return {"message": "User already has problems"}
    
    sample_problems = [
        {"title": "Two Sum", "platform": "LeetCode", "difficulty": "Easy", "topics": ["Arrays", "Hash Table"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat()},
        {"title": "Reverse Linked List", "platform": "LeetCode", "difficulty": "Easy", "topics": ["Linked List"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=4)).date().isoformat()},
        {"title": "Valid Parentheses", "platform": "LeetCode", "difficulty": "Easy", "topics": ["Stack", "Strings"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()},
        {"title": "Binary Tree Inorder Traversal", "platform": "LeetCode", "difficulty": "Medium", "topics": ["Trees", "DFS"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()},
        {"title": "Longest Palindromic Substring", "platform": "LeetCode", "difficulty": "Medium", "topics": ["Strings", "DP"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()},
        {"title": "Merge Two Sorted Lists", "platform": "LeetCode", "difficulty": "Easy", "topics": ["Linked List"], "date_completed": datetime.now(timezone.utc).date().isoformat()},
        {"title": "Maximum Subarray", "platform": "LeetCode", "difficulty": "Medium", "topics": ["Arrays", "DP"], "date_completed": datetime.now(timezone.utc).date().isoformat()},
        {"title": "Climbing Stairs", "platform": "LeetCode", "difficulty": "Easy", "topics": ["DP"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=6)).date().isoformat()},
        {"title": "Roman to Integer", "platform": "Codeforces", "difficulty": "Easy", "topics": ["Strings", "Hash Table"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()},
        {"title": "Binary Search", "platform": "Codeforces", "difficulty": "Easy", "topics": ["Arrays", "Binary Search"], "date_completed": (datetime.now(timezone.utc) - timedelta(days=8)).date().isoformat()},
    ]
    
    for problem_data in sample_problems:
        problem = Problem(
            user_id=user_id,
            title=problem_data["title"],
            platform=problem_data["platform"],
            difficulty=problem_data["difficulty"],
            topics=problem_data["topics"],
            date_completed=problem_data["date_completed"]
        )
        
        problem_dict = problem.model_dump()
        problem_dict['created_at'] = problem_dict['created_at'].isoformat()
        
        await db.problems.insert_one(problem_dict)
    
    return {"message": f"Seeded {len(sample_problems)} sample problems"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()