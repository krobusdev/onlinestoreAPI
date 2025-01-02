# set PYTHONPATH=%PYTHONPATH%;Z:\projects\onlinestoreAPI

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional
from pydantic import BaseModel

DATABASE_URL = "postgresql://postgres:121212@localhost:5432/onlinestore"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

class GameModel(Base):  # Создаем ОРМ модель, чтобы вместо SQL запросов обращаться через объекты и классы
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True, index=True)
    game_name = Column(String, nullable=False)
    game_price = Column(Integer, nullable=False)
    game_is_in_stock = Column(Boolean, nullable=False)

Base.metadata.create_all(bind=engine)  # Если таблица не существует, то мы создаем ее с помощью engine. Наследуем столбцы с существующей.

def get_db():  # Чтобы для каждого реквеста создавалась новая сессия
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Game(BaseModel):
    id: Optional[int] = None
    name: str
    price: int
    is_in_stock: bool

    class Config:
        from_attributes = True  # Чтобы парсить атрибуты напрямую из GameModel

class GameUpdate(BaseModel):  # Класс чтобы при изменении указывать не все атрибуты, а только те, что поменять
    name: Optional[str] = None
    price: Optional[int] = None
    is_in_stock: Optional[bool] = None

@app.get("/games", response_model=list[Game])
def get_games(db: Session = Depends(get_db)):  # В скобках - создаем сессию
    games = db.query(GameModel).all()  # Создаем запрос с помощью SQLAlchemy
    return [
        Game(
            id=game.game_id,
            name=game.game_name,
            price=game.game_price,
            is_in_stock=game.game_is_in_stock
        )
        for game in games
    ]

@app.post("/games/", response_model=Game)
def add_game(game: Game, db: Session = Depends(get_db)):  # В скобках - берем данные из JSON файла из запроса и засовываем в класс. Создаем сессию
    new_game = GameModel(
        game_name=game.name,
        game_price=game.price,
        game_is_in_stock=game.is_in_stock
    )
    db.add(new_game)
    db.commit()
    db.refresh(new_game)

    return Game(
        id=new_game.game_id,
        name=new_game.game_name,
        price=new_game.game_price,
        is_in_stock=new_game.game_is_in_stock
    )

@app.put("/games/{game_id}", response_model=Game)
def update_game(game_id: int, game: GameUpdate, db: Session = Depends(get_db)):  # Из JSON файла запроса засовываем то, что нужно в класс GameUpdate. Создаем сессию.
    existing_game = db.query(GameModel).filter(GameModel.game_id == game_id).first()  # .first это берем первое попавшееся совпадение. .filter это как WHERE в SQL.
    if not existing_game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.name is not None:  # Проверяем какие данные меняем
        existing_game.game_name = game.name
    if game.price is not None:
        existing_game.game_price = game.price
    if game.is_in_stock is not None:
        existing_game.game_is_in_stock = game.is_in_stock

    db.commit()
    db.refresh(existing_game)

    return Game(
        id=existing_game.game_id,
        name=existing_game.game_name,
        price=existing_game.game_price,
        is_in_stock=existing_game.game_is_in_stock
    )

@app.delete("/games/{game_id}", response_model=dict)
def delete_game(game_id: int, db: Session = Depends(get_db)):  # Создаем сессию.
    existing_game = db.query(GameModel).filter(GameModel.game_id == game_id).first()
    if not existing_game:
        raise HTTPException(status_code=404, detail="Game not found")

    db.delete(existing_game)
    db.commit()

    return {"message": f"Game with id {game_id} deleted successfully"}