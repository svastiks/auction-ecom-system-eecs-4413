from sqlalchemy import Column, String, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class EventLog(Base):
    __tablename__ = "event_log"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "aggregate_type IN ('USER','ITEM','AUCTION','BID','ORDER','PAYMENT','SHIPMENT')",
            name='ck_aggregate_type'
        ),
        Index('idx_event_log_aggregate', 'aggregate_type', 'aggregate_id'),
        Index('idx_event_log_created', 'created_at'),
    )
