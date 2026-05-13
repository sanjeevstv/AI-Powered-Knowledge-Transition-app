from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    transition_manager = "transition_manager"
    sme = "sme"
    vendor_team_member = "vendor_team_member"


class KTSessionStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str = ""
    role: UserRole = Field(default=UserRole.vendor_team_member)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions_owned: list["KTSession"] = Relationship(back_populates="owner")
    assessments: list["AssessmentResult"] = Relationship(back_populates="user")


class KTSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, description="Business id e.g. KT-101")
    topic: str
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    scheduled_date: datetime = Field(default_factory=datetime.utcnow)
    status: KTSessionStatus = Field(default=KTSessionStatus.pending)
    transcript_text: str = Field(default="", sa_column=Column(Text))
    summary_text: str = Field(default="", sa_column=Column(Text))
    key_decisions: str = Field(default="", sa_column=Column(Text))
    risks: str = Field(default="", sa_column=Column(Text))
    missing_knowledge_notes: str = Field(default="", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    owner: Optional[User] = Relationship(back_populates="sessions_owned")
    action_items: list["ActionItem"] = Relationship(back_populates="session")
    faq_items: list["FAQItem"] = Relationship(back_populates="session")


class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="ktsession.id")
    text: str = Field(sa_column=Column(Text))
    is_done: bool = False

    session: KTSession = Relationship(back_populates="action_items")


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    mime_type: str = ""
    tags: str = Field(default="", description="Comma-separated tags")
    content_extracted: str = Field(default="", sa_column=Column(Text))
    storage_path: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    faq_items: list["FAQItem"] = Relationship(back_populates="document")


class FAQItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="ktsession.id")
    document_id: Optional[int] = Field(default=None, foreign_key="document.id")
    question: str
    answer: str = Field(sa_column=Column(Text))

    session: Optional[KTSession] = Relationship(back_populates="faq_items")
    document: Optional[Document] = Relationship(back_populates="faq_items")


class AssessmentResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    quiz_score: int = Field(ge=0, le=100)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="assessments")


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow)
