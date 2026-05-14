import datetime as dt

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Kol(Base):
    __tablename__ = "kols"
    id: Mapped[int] = mapped_column(primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    followers: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(32), default="uncategorized")
    influence_score: Mapped[float] = mapped_column(Float, default=0.0)
    tweets: Mapped[list["Tweet"]] = relationship(back_populates="kol")


class Tweet(Base):
    __tablename__ = "tweets"
    id: Mapped[int] = mapped_column(primary_key=True)
    kol_id: Mapped[int] = mapped_column(ForeignKey("kols.id"))
    tweet_id: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    lang: Mapped[str] = mapped_column(String(8), default="en")
    posted_at: Mapped[dt.datetime] = mapped_column(DateTime)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    retweets: Mapped[int] = mapped_column(Integer, default=0)
    replies: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(32), default="")
    kol: Mapped[Kol] = relationship(back_populates="tweets")
    __table_args__ = (UniqueConstraint("tweet_id", name="uq_tweet_id"),)


class Summary(Base):
    __tablename__ = "summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    category: Mapped[str] = mapped_column(String(32))
    content_md: Mapped[str] = mapped_column(Text)
    source_tweet_ids: Mapped[str] = mapped_column(Text, default="")


class DispatchLog(Base):
    __tablename__ = "dispatch_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(String(10))
    channel: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    payload: Mapped[str] = mapped_column(Text)
