# main.py
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Path, status, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel
from contextlib import asynccontextmanager

# ----------------------------
# Database setup
# ----------------------------
DATABASE_URL = "sqlite:///./test.db"  # Local SQLite database
engine = create_engine(DATABASE_URL, echo=False)


# ----------------------------
# Models
# ----------------------------
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    author: str
    content: str


# ----------------------------
# Schemas (Pydantic models)
# ----------------------------
class TaskCreate(BaseModel):
    title: str


class TaskRead(BaseModel):
    id: int
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None


class CommentCreate(BaseModel):
    author: str
    content: str


class CommentRead(BaseModel):
    id: int
    task_id: int
    author: str
    content: str


class CommentUpdate(BaseModel):
    author: Optional[str] = None
    content: Optional[str] = None


# ----------------------------
# Lifespan (startup/shutdown)
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="Tasks + Comments API", lifespan=lifespan)


# Dependency: Database session
def get_session():
    with Session(engine) as session:
        yield session


# ----------------------------
# Task Endpoints
# ----------------------------
@app.post("/tasks/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task(title=task.title)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@app.get("/tasks/", response_model=List[TaskRead])
def list_tasks(session: Session = Depends(get_session)):
    statement = select(Task)
    tasks = session.exec(statement).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.title:
        task.title = payload.title

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return None


# ----------------------------
# Comment Endpoints
# ----------------------------
@app.get("/tasks/{task_id}/comments/", response_model=List[CommentRead])
def list_comments(task_id: int = Path(..., gt=0), session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    statement = select(Comment).where(Comment.task_id == task_id)
    comments = session.exec(statement).all()
    return comments


@app.post("/tasks/{task_id}/comments/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def add_comment(task_id: int, payload: CommentCreate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = Comment(task_id=task_id, author=payload.author, content=payload.content)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@app.get("/comments/{comment_id}", response_model=CommentRead)
def get_comment(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@app.put("/comments/{comment_id}", response_model=CommentRead)
def update_comment(comment_id: int, payload: CommentUpdate, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if payload.author:
        comment.author = payload.author
    if payload.content:
        comment.content = payload.content

    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@app.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    session.delete(comment)
    session.commit()
    return None
