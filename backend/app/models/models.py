import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
import enum

from app.database.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RESEARCHING = "RESEARCHING"
    RESEARCH_COMPLETE = "RESEARCH_COMPLETE"
    BRIEF_GENERATING = "BRIEF_GENERATING"
    BRIEF_COMPLETE = "BRIEF_COMPLETE"
    WRITING = "WRITING"
    DRAFT_COMPLETE = "DRAFT_COMPLETE"
    QUALITY_CHECK = "QUALITY_CHECK"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    FINAL_READY = "FINAL_READY"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class BatchStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Website(Base):
    __tablename__ = "websites"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    brand_voice = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    strapi_url = Column(String(255), nullable=True)
    strapi_api_token = Column(Text, nullable=True)
    strapi_content_type = Column(String(255), default="articles")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContentBatch(Base):
    __tablename__ = "content_batches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    jobs = relationship("ContentJob", back_populates="batch", cascade="all, delete-orphan")

class ContentJob(Base):
    __tablename__ = "content_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), ForeignKey("content_batches.id"), nullable=False)
    topic = Column(Text, nullable=False)
    primary_keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, nullable=True)
    keyword_difficulty = Column(Integer, nullable=True)
    target_density = Column(String(50), nullable=True)
    category = Column(String(255), nullable=True)
    audience = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED)
    current_step = Column(String(100), default="QUEUED")
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    batch = relationship("ContentBatch", back_populates="jobs")
    articles = relationship("Article", back_populates="job", cascade="all, delete-orphan")
    publishing_jobs = relationship("PublishingJob", back_populates="job", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="job", cascade="all, delete-orphan")

class ResearchProject(Base):
    __tablename__ = "research_projects"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    summary = Column(Text, nullable=True)
    search_intent = Column(String(255), nullable=True)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_projects.id"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    source_type = Column(String(100), nullable=True)
    publication_date = Column(String(100), nullable=True)

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    research_id = Column(String(36), ForeignKey("research_projects.id"), nullable=False)
    claim = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    confidence = Column(String(50), nullable=True)

class ContentBrief(Base):
    __tablename__ = "content_briefs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    recommended_title = Column(String(500), nullable=False)
    target_audience = Column(Text, nullable=True)
    article_objective = Column(Text, nullable=True)
    unique_angle = Column(Text, nullable=True)
    structure_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=True)
    meta_description = Column(Text, nullable=True)
    current_version = Column(Integer, default=1)
    status = Column(String(50), default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = relationship("ContentJob", back_populates="articles")
    versions = relationship("ArticleVersion", back_populates="article", cascade="all, delete-orphan")

class ArticleVersion(Base):
    __tablename__ = "article_versions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    article_id = Column(String(36), ForeignKey("articles.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content_body = Column(Text, nullable=False)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    article = relationship("Article", back_populates="versions")

class QualityReport(Base):
    __tablename__ = "quality_reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    version_number = Column(Integer, default=1)
    fact_check_score = Column(Float, default=0.0)
    seo_score = Column(Float, default=0.0)
    editorial_score = Column(Float, default=0.0)
    overall_status = Column(String(50), nullable=False) # PASSED / REVISION_REQUIRED
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PublishingJob(Base):
    __tablename__ = "publishing_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    cms = Column(String(50), default="strapi")
    cms_entry_id = Column(String(255), nullable=True)
    published_url = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING")
    error_message = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("ContentJob", back_populates="publishing_jobs")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    content_job_id = Column(String(36), ForeignKey("content_jobs.id"), nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("ContentJob", back_populates="activity_logs")
