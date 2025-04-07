from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"
    id          : Mapped[int] = mapped_column(primary_key=True)
    username    : Mapped[str] = mapped_column(nullable=False)
    password    : Mapped[str] = mapped_column(nullable=False)
    first_name  : Mapped[str] = mapped_column(nullable=True)
    middle_name : Mapped[str] = mapped_column(nullable=True)
    last_name   : Mapped[str] = mapped_column(nullable=True)
    company     : Mapped[str] = mapped_column(nullable=True)
    job_title   : Mapped[str] = mapped_column(nullable=True)
