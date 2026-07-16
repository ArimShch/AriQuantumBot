from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import (
    String, 
    Text, 
    ForeignKey, 
    Integer, 
    SmallInteger, 
    DateTime, 
    Date, 
    BigInteger, 
    CheckConstraint,
    Boolean, 
    JSON,
    Numeric,
    UniqueConstraint, 
    func, text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import List
from datetime import datetime, date 


class Base(AsyncAttrs, DeclarativeBase):
    pass 


class Role(Base):
    __tablename__ = 'role'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50), 
        CheckConstraint("name IN ('user', 'admin')"), 
        unique=True, 
    )

    users: Mapped[List["User"]] = relationship(
        back_populates='role', 
        lazy='selectin', 
    )

    def __repr__(self):
        return f'<Role(id={self.id}, name={self.name})>'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey('role.id', ondelete='RESTRICT'),
        server_default=text('1'),                  # user
        nullable=False, 
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    date_joined: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ref_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tg_locate: Mapped[str | None] = mapped_column(String(100), nullable=True)


    role: Mapped['Role'] = relationship(
        back_populates='users', 
        lazy='selectin', 
    )
    # Внешние модели
    setting: Mapped["UserSetting"] = relationship(
        back_populates='user', 
        uselist=False, 
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    user_circuits: Mapped[List['QuantumCircuit']] = relationship(
        back_populates='user', 
        lazy='selectin', 
    )
    user_simulations: Mapped[List['QuantumSimulation']] = relationship(
        back_populates='user', 
        lazy='selectin',
    )
    user_activity: Mapped[List['UserActivityLog']] = relationship(
        back_populates='user', 
        lazy='selectin', 
    )

    def __repr__(self):
        role_name = self.role.name if self.role else f"role_id={self.role_id}"
        return (
            f"<User(id={self.id}, username={self.username}, "
            f"first_name={self.first_name}, last_name={self.last_name}, "
            f"role={role_name})>"
        )

class Language(Base):
    __tablename__ = 'language'

    code: Mapped[str] = mapped_column(String(10), primary_key=True, )
    name: Mapped[str] = mapped_column(String(100))
    emoji: Mapped[str] = mapped_column(String(10))

    users_settings: Mapped[List["UserSetting"]] = relationship(
        back_populates='language', 
        lazy='selectin',  
    )

    def __repr__(self):
        return f'<Language(code={self.code}, name={self.name})>'


class ComplexityLevel(Base):
    __tablename__ = 'complexity_level'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(20), 
        CheckConstraint("name IN ('Novice', 'Student', 'Researcher')"), 
        unique=True, 
    )
    emoji: Mapped[str] = mapped_column(String(10))

    users_settings: Mapped[List["UserSetting"]] = relationship(
        back_populates='complexity_level', 
        lazy='selectin'
    )

    def __repr__(self):
        return f'<ComplexityLevel(id={self.id}, name={self.name})>'



class Backend(Base):
    __tablename__ = 'backend'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("name IN ('Qiskit', 'AriQuantum')"),
        unique=True,
    )
    max_qubits: Mapped[int] = mapped_column(
        SmallInteger, 
        CheckConstraint("max_qubits BETWEEN 1 AND 10")
    )

    # Внешние модели
    users_settings: Mapped[List["UserSetting"]] = relationship(
        back_populates='backend', 
        lazy='selectin'
    )
    quantum_circuits: Mapped[List["QuantumCircuit"]] = relationship(
        back_populates='backend', 
        lazy='selectin'
    )

    def __repr__(self):
        return f'<Backend(id={self.id}, name={self.name}, max_qubits={self.max_qubits})>'


class UserSetting(Base):
    __tablename__ = 'user_setting'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True, 
        index=True, 
    )
    language_code: Mapped[str] = mapped_column(
        ForeignKey('language.code', ondelete='RESTRICT'),
        nullable=False, 
        server_default=text("'en'"), 
        default='en', 
    )
    complexity_level_id: Mapped[int] = mapped_column(
        ForeignKey('complexity_level.id', ondelete='RESTRICT'), 
        nullable=False, 
        server_default=text('1'),                   # novice
        default=1,
    )
    automatic_name: Mapped[bool] = mapped_column(
        Boolean, 
        server_default=text('false'), 
        default=False,
    )
    qubit_input_text: Mapped[bool] = mapped_column(
        Boolean, 
        server_default=text('false'), 
        default=False,
    )
    simulation_shots: Mapped[int] = mapped_column(
        Integer, 
        CheckConstraint("simulation_shots BETWEEN 1 AND 1000"), 
        default=text('10'),
    )
    backend_id: Mapped[int] = mapped_column(
        ForeignKey('backend.id', ondelete='RESTRICT'), 
        nullable=False, 
        default=text('1')                   # ariquantum
    )

    user: Mapped["User"] = relationship(
        back_populates='setting', 
        lazy='selectin'
    )
    language: Mapped["Language"] = relationship(
        back_populates='users_settings', 
        lazy='selectin'
    )
    complexity_level: Mapped["ComplexityLevel"] = relationship(
        back_populates='users_settings', 
        lazy='selectin', 
    )
    backend: Mapped["Backend"] = relationship(
        back_populates='users_settings', 
        lazy='selectin', 
    )
    

class QuantumCircuit(Base):
    __tablename__ = 'quantum_circuit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] =  mapped_column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True, 
    )
    backend_id: Mapped[int] = mapped_column(
        ForeignKey('backend.id', ondelete='RESTRICT'), 
    )
    circuit_name: Mapped[str] = mapped_column(String(50))
    num_qubits: Mapped[int] = mapped_column(
        SmallInteger,
    )
    circuit_history: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSONB),  
        default=[],
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped['User'] = relationship(
        back_populates='user_circuits', 
        lazy='selectin', 
    )
    quantum_simulations: Mapped[List['QuantumSimulation']] = relationship(
        back_populates='quantum_circuit', 
        lazy='selectin', 
    )
    backend: Mapped['Backend'] = relationship(
        back_populates='quantum_circuits', 
        lazy='selectin'
    )


class QuantumSimulation(Base):
    __tablename__ = 'quantum_simulation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] =  mapped_column(
        BigInteger, 
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True, 
    )
    circuit_id: Mapped[int | None] = mapped_column(
        ForeignKey('quantum_circuit.id', ondelete='CASCADE'), 
        nullable=True, 
        index=True
    )
    braket_state: Mapped[str] = mapped_column(
        Text, 
    )
    counts: Mapped[dict] = mapped_column(
        JSON, 
        nullable=True, 
    )
    execution_time: Mapped[float] = mapped_column(
        Numeric(10, 6)
    )
    shots: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("shots BETWEEN 1 AND 1000")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    quantum_circuit: Mapped["QuantumCircuit"] = relationship(
        back_populates='quantum_simulations', 
        lazy='selectin', 
    )
    user: Mapped['User'] = relationship(
        back_populates='user_simulations', 
        lazy='selectin', 
    )

class UserActivityLog(Base):
    __tablename__ = 'user_activity_log'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'))
    activity_date: Mapped[date] = mapped_column(Date, default=func.current_date())
    
    circuits_created: Mapped[int] = mapped_column(Integer, default=0)
    simulations_run: Mapped[int] = mapped_column(Integer, default=0)
    
    user: Mapped['User'] = relationship(
        back_populates='user_activity', 
        lazy='selectin', 
    )


    __table_args__ = (UniqueConstraint('user_id', 'activity_date', name='uq_user_date'),)


