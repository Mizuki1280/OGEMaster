import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    total_tasks = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    completed_tasks = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    def __repr__(self):
        return f"<User> {self.id} {self.username} {self.email}"