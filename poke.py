import asyncio
from fastapi import FastAPI, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String
import os
import httpx
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL","sqlite:///./atividadeawait.db")
API_VERSION = os.getenv("API_VERSION", "1.0.0")

app = FastAPI(
    title="Projeto API",
    description="API assíncrona para buscar Pokemons da POKEAPI",
    version=API_VERSION
)

base = declarative_base()

engine = create_engine(database_url, connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PokemonDB(base):
    __tablename__ = "Pokemons"
    id = Column(Integer, index = True, primary_key = True)
    nome_pokemon = Column(String, index = True)
    altura_pokemon = Column(Integer, index = True)
    peso_pokemon = Column(Integer, index = True)
    tipo_pokemon = Column(String, index = True)
    sprites_pokemon = Column(String, index = True)

base.metadata.create_all(bind = engine)

class PokemonRespostaSwagger(BaseModel):
    id: int = Field(..., description="ID do Pokémon vindo da PokéAPI", example=25)
    nome_pokemon: str = Field(..., description="Nome do Pokémon", example="pikachu")
    altura_pokemon: int = Field(..., description="Altura do Pokémon", example=4)
    peso_pokemon: int = Field(..., description="Peso do Pokémon", example=60)
    tipo_pokemon: str = Field(..., description="Tipo do Pokémon", example="electric")
    sprites_pokemon: str = Field(..., description="URL da imagem (sprite) padrão do Pokémon", example="https://githubusercontent.com")

    class Config:
        from_attributes = True

class Atualizar_Pokemons(BaseModel):
    nome_pokemon: str = Field(..., example= "pikachu modificado")
    altura_pokemon: int = Field(..., example= 5)
    peso_pokemon: int = Field(..., example= 65)
    tipo_pokemon: str = Field(..., example="electric, steel")

class ListaPokemons(BaseModel):
    Pagina: int = Field(..., example=1)
    Size: int = Field (..., example=5)
    Total: int = Field(..., example=150)
    Pokemons: List[PokemonRespostaSwagger]

@app.post("/Pokemons/importar/{nome_ou_id}", summary="Importa um Pokémon da PokéAPI", description="Busca os dados de um Pokemon da POKEAPI", tags=["Importação"])
async def importar_pokeapi(nome_ou_id: str = Path(..., description="Nome ou ID numérico do Pokémon na PokéAPI", example="charizard"), 
    db: Session = Depends(sessao_db)):

    url = f"https://pokeapi.co/api/v2/pokemon/{nome_ou_id.lower()}"

    async with httpx.AsyncClient() as client:
        resposta = await client.get(url)

        if resposta.status_code == 404:
            raise HTTPException(status_code = 404, detail = "Pokemon não está na PokeAPI")
        
        if resposta.status_code != 200:
            raise HTTPException(status_code = 500, detail =  "Erro ao acessar API")
        
        dados = resposta.json()

    pokemon_id = dados ["id"]
    nome = dados["name"]
    altura = dados["height"]
    peso = dados["weight"]
    tipo = ", ".join([t["type"]["name"] for t in dados ["types"]])
    sprite = dados["sprites"]["front_default"]

    pokemon_existente = db.query(PokemonDB).filter(PokemonDB.id == pokemon_id).first()
    if pokemon_existente:
        return{"message": "pokemon já está cadastrado", "pokemon": pokemon_existente}
    
    novo_pokemon = PokemonDB(
        id = pokemon_id,
        nome_pokemon = nome,
        altura_pokemon = altura, 
        peso_pokemon = peso,
        tipo_pokemon = tipo,
        sprites_pokemon = sprite
    )

    db.add(novo_pokemon)
    db.commit()
    db.refresh(novo_pokemon)

    return {"message": "Pokemon pego com sucesso", "pokemon": novo_pokemon}

@app.get("/Pokemons", summary="Lista todos os Pokémons", description="Retorna os Pokémons", response_model=ListaPokemons, tags=["Gerenciamento de Pokémons"])
async def get_pokemons(db: Session = Depends(sessao_db), page: int = 1, size: int = 5, ordem: str = "nome"):
    if page < 1:
        raise HTTPException(status_code = 400, detail = "Página invalida")
    
    query = db.query(PokemonDB)

    if ordem.lower() == "altura":
        query = query.order_by(PokemonDB.altura_pokemon)
    elif ordem.lower() == "tipo":
        query = query.order_by(PokemonDB.tipo_pokemon)
    elif ordem.lower() == "peso":
        query = query.order_by(PokemonDB.peso_pokemon)
    else:
        query = query.order_by(PokemonDB.nome_pokemon)

    pokemons = query.offset((page-1)*size).limit(size).all()
    total = query.count()

    if not pokemons:
        return {
            "Pagina":page,
            "Size": size,
            "Total": total,
            "Pokemons": []
        }
    
    return{
        "Pagina": page,
        "Size": size,
        "Total": total,
        "Pokemons":[{
            "id": pkm.id,
            "nome_pokemon": pkm.nome_pokemon,
            "altura_pokemon": pkm.altura_pokemon,
            "peso_pokemon": pkm.peso_pokemon,
            "tipo_pokemon": pkm.tipo_pokemon,
            "sprites_pokemon": pkm.sprites_pokemon}
            for pkm in pokemons]
    }

@app.get("/Pokemons/{id}", 
    summary= "Busca um Pokémon por ID",
    description= "Retorna os detalhes completos de um Pokémon pelo ID.",
    response_model= PokemonRespostaSwagger,
    tags=["Gerenciamento de Pokémons"])

async def get_pokemons_id(id: int = Path(..., description="ID do Pokémon buscado", example=25), 
    db: Session = Depends(sessao_db)):
    pokemon = db.query(PokemonDB).filter(PokemonDB.id == id).first()

    if not pokemon:
        raise HTTPException(status_code = 404, detail = "Pokemon não encontrado")
    
    return pokemon

@app.put("/Pokemons/{id}")
async def put_pokemons(id:int,pokemons_input: Atualizar_Pokemons, db: Session = Depends(sessao_db)):
    pokemon = db.query(PokemonDB).filter(PokemonDB.id == id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon não encontrado")
    
    pokemon.nome_pokemon = pokemons_input.nome_pokemon
    pokemon.altura_pokemon = pokemons_input.altura_pokemon
    pokemon.peso_pokemon = pokemons_input.peso_pokemon
    pokemon.tipo_pokemon = pokemons_input.tipo_pokemon

    db.commit()
    db.refresh(pokemon)

    return {"message": "Dados do Pokemon Atualizado"}

@app.delete("/Pokemons/{id}")
async def delete_pokemons(id: int, db: Session = Depends(sessao_db)):
    pokemon = db.query(PokemonDB).filter(PokemonDB.id == id).first()

    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokemon não encontrado")
    
    db.delete(pokemon)
    db.commit()

    return{"message": "Pokemon deletado"}