from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum
import os

# declarative base class
Base = declarative_base()


# Define el modelo de Club
class Club(Base):
    __tablename__ = "club"

    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    provincia = Column(String)
    direccion = Column(String)
    telefono = Column(String)
    miembros = Column(Integer)
    url = Column(String)

    # Relación con los usuarios
    users = relationship("User", back_populates="club")


class ClubCreate(BaseModel):
    nombre: str
    provincia: str
    direccion: str
    telefono: str
    miembros: int
    url: str


# Define el modelo de roles de usuario
class UserRole(Enum):
    referee = "referee"
    swimmer = "swimmer"
    coach = "coach"


# Define el modelo de Usuario
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    telefono = Column(String)
    fecha_nacimiento = Column(Date)
    role = Column(SQLAlchemyEnum(UserRole))
    club_id = Column(Integer, ForeignKey("club.id"))

    # Relación con el club
    club = relationship("Club", back_populates="users")


class UserCreate(BaseModel):
    name: str
    surname: str
    telefono: str
    fecha_nacimiento: str
    role: UserRole
    club_id: int


# Define la clase Tournament
class Tournament(Base):
    __tablename__ = "tournament"

    id = Column(Integer, primary_key=True)
    tipo = Column(String)
    nombre = Column(String)
    fecha = Column(Date)
    num_participantes = Column(Integer)
    lugar = Column(String)
    races = relationship("Race", back_populates="tournament")


class TournamentCreate(BaseModel):
    tipo: str
    nombre: str
    fecha: str
    num_participantes: int
    lugar: str


# Define la clase Race
class Race(Base):
    __tablename__ = "race"

    id = Column(Integer, primary_key=True)
    hora_aprox = Column(Time)
    estilo = Column(String)
    distancia = Column(String)
    tournament_id = Column(Integer, ForeignKey("tournament.id"))
    tournament = relationship("Tournament", back_populates="races")


class RaceCreate(BaseModel):
    hora_aprox: str
    estilo: str
    distancia: str


# Elimina la base de datos existente si existe
if os.path.exists("swimchrono.db"):
    os.remove("swimchrono.db")
# Crea la base de datos SQLite
engine = create_engine("sqlite:///swimchrono.db", echo=True, future=True)
Base.metadata.create_all(engine)


# Crea la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Datos de torneos
torneos_data = [
    {
        "tipo": "Local",
        "nombre": "Torneo de natación sincronizada 2024",
        "fecha": "15 Apr 2024",
        "num_participantes": 50,
        "lugar": "Piscina Municipal de Madrid",
    },
    {
        "tipo": "Regional",
        "nombre": "Campeonato de waterpolo 2024",
        "fecha": "20 May 2024",
        "num_participantes": 30,
        "lugar": "Piscina Olímpica de Barcelona",
    },
    {
        "tipo": "Local",
        "nombre": "Gran Premio de Natación 2024",
        "fecha": "10 Jun 2024",
        "num_participantes": 100,
        "lugar": "Piscina Nacional de Londres",
    },
]

# Itera sobre los datos del torneo y agrégalos a la base de datos
for torneo_data in torneos_data:
    parsed_date = datetime.strptime(torneo_data["fecha"], "%d %b %Y").date()
    tournament = Tournament(
        tipo=torneo_data["tipo"],
        nombre=torneo_data["nombre"],
        fecha=parsed_date,
        num_participantes=torneo_data["num_participantes"],
        lugar=torneo_data["lugar"],
    )
    session.add(tournament)

# Realiza la confirmación para guardar los cambios en la base de datos
session.commit()


app = FastAPI()


# Ruta para crear un nuevo club
@app.post("/clubs")
async def create_club(club_data: ClubCreate):
    club = Club(**club_data.dict())
    session.add(club)
    session.commit()
    return {"Club added": club.id}


# Ruta para obtener todos los clubes con sus usuarios
@app.get("/clubs")
async def get_all_clubs():
    clubs = session.query(Club).all()
    formatted_clubs = []
    for club in clubs:
        # Obtener los usuarios asociados al club
        users = [
            {
                "ID": user.id,
                "NOMBRE": user.name,
                "SURNAME": user.surname,
                "TELEFONO": user.telefono,
                "FECHA NACIMIENTO": user.fecha_nacimiento,
                "ROL": user.role,
            }
            for user in club.users
        ]

        formatted_clubs.append(
            {
                "ID": club.id,
                "NOMBRE": club.nombre,
                "PROVINCIA": club.provincia,
                "DIRECCIÓN": club.direccion,
                "TELÉFONO": club.telefono,
                "MIEMBROS": club.miembros,
                "URL": club.url,
                "USUARIOS": users,
            }
        )
    return formatted_clubs


# Ruta para crear un nuevo usuario
@app.post("/users")
async def create_user(user_data: UserCreate):
    club = session.query(Club).get(user_data.club_id)
    if not club:
        return {"error": "Club not found"}
    parsed_date = datetime.strptime(user_data.fecha_nacimiento, "%d %b %Y").date()
    user_data_dict = user_data.dict()
    user_data_dict["fecha_nacimiento"] = parsed_date
    user = User(**user_data_dict)
    session.add(user)
    session.commit()
    return {"User added": user.id}


# Ruta para obtener todos los nadadores
@app.get("/users")
async def get_all_users():
    users = session.query(User).all()
    return users


# Ruta para obtener todos los torneos
@app.get("/tournaments")
async def get_all_tournaments():
    tournaments = session.query(Tournament).all()
    formatted_tournaments = []
    for tournament in tournaments:
        # Obtener las carreras asociadas al torneo
        races = [
            {
                "ID": race.id,
                "HORA APROXIMADA": race.hora_aprox.strftime("%H:%M"),
                "ESTILO": race.estilo,
                "DISTANCIA": race.distancia,
            }
            for race in tournament.races
        ]

        formatted_tournaments.append(
            {
                "ID": tournament.id,
                "TIPO": tournament.tipo,
                "NOMBRE": tournament.nombre,
                "FECHA": tournament.fecha.strftime("%d %b %Y"),
                "NÚMERO PARTICIPANTES": tournament.num_participantes,
                "LUGAR": tournament.lugar,
                "CARRERAS": races,
            }
        )
    return formatted_tournaments


# Ruta para crear un nuevo torneo
@app.post("/tournaments")
async def create_tournament(tournament_data: TournamentCreate):
    # Parsea la fecha en formato de cadena a objeto de fecha
    parsed_date = datetime.strptime(tournament_data.fecha, "%d %b %Y").date()
    tournament_data_dict = tournament_data.dict()
    tournament_data_dict["fecha"] = parsed_date
    tournament = Tournament(**tournament_data_dict)
    session.add(tournament)
    session.commit()
    return {"Tournament added": tournament.id}


# Ruta para obtener todas las carreras de un torneo específico
@app.get("/tournaments/{tournament_id}/races")
async def get_tournament_races(tournament_id: int):
    tournament = session.query(Tournament).get(tournament_id)
    if not tournament:
        return {"error": "Tournament not found"}
    races = [
        {
            "ID": race.id,
            "HORA APROXIMADA": race.hora_aprox.strftime("%H:%M"),
            "ESTILO": race.estilo,
            "DISTANCIA": race.distancia,
        }
        for race in tournament.races
    ]
    return {"tournament_id": tournament_id, "races": races}


# Ruta para crear una nueva carrera asociada a un torneo
@app.post("/tournaments/{tournament_id}/races")
async def create_race(tournament_id: int, race_data: RaceCreate):
    tournament = session.query(Tournament).get(tournament_id)
    if not tournament:
        return {"error": "Tournament not found"}
    parsed_time = datetime.strptime(race_data.hora_aprox, "%H:%M").time()
    race = Race(
        hora_aprox=parsed_time,
        estilo=race_data.estilo,
        distancia=race_data.distancia,
        tournament=tournament,
    )
    session.add(race)
    session.commit()
    return {"Race added": race.id, "tournament_id": tournament_id}