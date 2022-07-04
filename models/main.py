from sqlalchemy import Column, Enum
from sqlmodel import Field, Relationship, SQLModel, create_engine

from settings import DATABASE_URI
from typings.enums import UserRole

engine = create_engine(DATABASE_URI, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


class UserAlertLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    alert_id: int = Field(foreign_key="alert.id", primary_key=True)

    def __repr__(self):
        return f"{{user_id: {self.user_id}, alert_id: {self.alert_id}}}"


class User(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    username: str = Field(index=True, sa_column_kwargs={"unique": True})
    role: UserRole = Field(sa_column=Column(Enum(UserRole)))

    alerts: list["Alert"] = Relationship(
        back_populates="users", link_model=UserAlertLink
    )

    def __repr__(self):
        return f"{{id: {self.id}, username: {self.username}, role: {self.role}}}"


class Alert(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    key: str = Field(index=True, sa_column_kwargs={"unique": True})
    exchange: str
    symbol: str
    timeframe: str
    candle_len: int
    delta: int

    users: list["User"] = Relationship(
        back_populates="alerts", link_model=UserAlertLink
    )

    def __repr__(self):
        return (
            f"{{id: {self.id}, key: {self.key}, exchange: {self.exchange}, symbol: {self.symbol}, "
            f"timeframe: {self.timeframe}, candle_len: {self.candle_len}, delta: {self.delta}}}"
        )
