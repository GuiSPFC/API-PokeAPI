import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from poke import app, base, sessao_db, PokemonDB

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

base.metadata.create_all(bind=engine_test)

#FIXTURE PARA LIMPAR OS DADOS DA TABELA ENTRE UM TESTE E OUTRO

@pytest.fixture(autouse=True)
def limpar_banco():
    yield
    db = TestingSessionLocal()
    try:
        db.query(PokemonDB).delete()
        db.commit()
    finally:
        db.close()

#SUBSTITUI A SESSÃO DA API PELA SESSÃO DE TESTES

def override_sessao_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[sessao_db] = override_sessao_db

client = TestClient(app)

#TESTES DE IMPORTAÇÃO

def test_importar_pokemon_sucesso(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 25,
        "name": "pikachu",
        "height": 4,
        "weight": 60,
        "types": [{"type": {"name": "electric"}}],
        "sprites": {"front_default": "url_link"}
    }
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    resposta = client.post("/Pokemons/importar/pikachu")
    
    assert resposta.status_code == 200
    assert resposta.json()["message"] == "Pokemon pego com sucesso"
    assert resposta.json()["pokemon"]["nome_pokemon"] == "pikachu"

def test_importar_pokemon_nao_encontrado_na_api(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    resposta = client.post("/Pokemons/importar/pokemon_falso")
    
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pokemon não está na PokeAPI"


#TESTES DE LISTAGEM E PAGINAÇÃO

def test_listar_pokemons_vazio():
    resposta = client.get("/Pokemons")
    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["Pagina"] == 1
    assert dados["Pokemons"] == []

def test_paginacao_e_ordenacao():
    db = TestingSessionLocal()
    p1 = PokemonDB(id=1, nome_pokemon="bulbasaur", altura_pokemon=7, peso_pokemon=69, tipo_pokemon="grass", sprites_pokemon="url")
    p2 = PokemonDB(id=2, nome_pokemon="charmander", altura_pokemon=6, peso_pokemon=85, tipo_pokemon="fire", sprites_pokemon="url")
    p3 = PokemonDB(id=3, nome_pokemon="squirtle", altura_pokemon=5, peso_pokemon=90, tipo_pokemon="water", sprites_pokemon="url")
    db.add_all([p1, p2, p3])
    db.commit()

    resposta = client.get("/Pokemons?page=1&size=2&ordem=nome")
    dados = resposta.json()
    
    assert resposta.status_code == 200
    assert dados["Pagina"] == 1
    assert dados["Size"] == 2
    assert dados["Total"] == 3
    assert len(dados["Pokemons"]) == 2
    assert dados["Pokemons"][0]["nome_pokemon"] == "bulbasaur"

def test_paginacao_erro_pagina_invalida():
    resposta = client.get("/Pokemons?page=0")
    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Página invalida"


#TESTES DE BUSCA POR ID

def test_buscar_por_id_sucesso():
    db = TestingSessionLocal()
    pkm = PokemonDB(id=150, nome_pokemon="mewtwo", altura_pokemon=20, peso_pokemon=1220, tipo_pokemon="psychic", sprites_pokemon="url")
    db.add(pkm)
    db.commit()

    resposta = client.get("/Pokemons/150")
    assert resposta.status_code == 200
    assert resposta.json()["nome_pokemon"] == "mewtwo"

def test_buscar_por_id_nao_encontrado():
    resposta = client.get("/Pokemons/999")
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pokemon não encontrado"

#TESTE DE ATUALIZAR POKEMON COM SUCESSO

def test_atualizar_pokemon_sucesso():
    db = TestingSessionLocal()
    pkm = PokemonDB(id=25, nome_pokemon="pikachu", altura_pokemon=4, peso_pokemon=60, tipo_pokemon="electric", sprites_pokemon="url")
    db.add(pkm)
    db.commit()

    dados_atualizados = {
        "nome_pokemon": "pikachu modificado",
        "altura_pokemon": 5,
        "peso_pokemon": 65,
        "tipo_pokemon": "electric, steel"
    }

    resposta = client.put("/Pokemons/25", json=dados_atualizados)
    assert resposta.status_code == 200
    assert resposta.json()["message"] == "Dados do Pokemon Atualizado"

#TESTE DE ATUALIZAR POKEMON COM ERRO

def test_atualizar_pokemon_nao_encontrado():
    dados_atualizados = {
        "nome_pokemon": "Ronaldo",
        "altura_pokemon": 1,
        "peso_pokemon": 1,
        "tipo_pokemon": "normal"
    }
    resposta = client.put("/Pokemons/999", json=dados_atualizados)
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pokemon não encontrado"


#TESTES DO ENDPOINT DELETE

def test_deletar_pokemon_sucesso():
    db = TestingSessionLocal()
    pkm = PokemonDB(id=4, nome_pokemon="charmander", altura_pokemon=6, peso_pokemon=85, tipo_pokemon="fire", sprites_pokemon="url")
    db.add(pkm)
    db.commit()

    resposta = client.delete("/Pokemons/4")
    assert resposta.status_code == 200
    assert resposta.json()["message"] == "Pokemon deletado"

def test_deletar_pokemon_nao_encontrado():
    resposta = client.delete("/Pokemons/999")
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Pokemon não encontrado"
