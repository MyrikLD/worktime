from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import Session


@as_declarative()
class Base:
    session: Session

    id = Column(Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def save(self):
        self.session.commit()

    def delete(self):
        self.session.delete(self)

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        """
        Get or create a model instance while preserving integrity.
        """
        s = cls.session

        try:
            return s.query(cls).filter_by(**kwargs).one(), False
        except NoResultFound:
            if defaults is not None:
                kwargs.update(defaults)
            try:
                with s.begin_nested():
                    instance = cls(**kwargs)
                    s.add(instance)
                    s.commit()
                    return instance, True
            except IntegrityError:
                return s.query(cls).filter_by(**kwargs).one(), False


class States:
    UNKNOWN = 'UNKNOWN'
    WORK = 'WORK'
    HOME = 'HOME'
    REST = 'REST'

    @classmethod
    def keys(cls):
        return cls.UNKNOWN, cls.WORK, cls.HOME, cls.REST
