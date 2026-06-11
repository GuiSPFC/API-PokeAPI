# API de Integração com a PokéAPI

Esta API realiza a busca assíncrona de dados na [PokéAPI](https://pokeapi.co), persiste as informações em um banco de dados relacional local (**SQLite**) via **SQLAlchemy** e disponibiliza uma interface interativa de testes através do **Swagger**.

O projeto foi desenvolvido utilizando o framework **FastAPI**, aproveitando os recursos nativos de assincronismo para otimização de requisições externas.

---

## Como Instalar e Executar o Projeto com Docker

A forma recomendada para executar esta aplicação é utilizando contêineres Docker

### Pré-requisitos
*   **Docker** instalado e em execução.
*   **Docker Compose** instalado.

### Passo a Passo

1. **Construir e Iniciar os Contêineres**
   Abra o terminal no diretório raiz do projeto (onde estão os arquivos `Dockerfile` e `docker-compose.yml`) e execute o comando abaixo:
   ```bash
   docker compose up --build
   ```
2. **Encerrar a Execução**
   Para parar o funcionamento dos contêineres, utilize o atalho `Ctrl + C` no terminal ou execute:
   ```bash
   docker compose down
   ```
---

## Documentação Automática (Swagger)

A documentação interativa baseada na especificação OpenAPI é gerada de forma 100% automática pelo FastAPI. Com a aplicação rodando, acesse os endereços abaixo no seu navegador:

*   **Interface Interativa (Swagger UI):** [http://127.0.0](http://127.0.0)
*   **Interface Alternativa (Redoc):** [http://127.0.0](http://127.0.0)

---

## Endpoints Disponíveis

As rotas da aplicação estão estruturadas e categorizadas da seguinte forma:

### Categoria: Importação
*   `POST /Pokemons/importar/{nome_ou_id}`: Consome os dados do Pokémon informado a partir da API externa. Se os dados não constarem no banco de dados local, o registro é inserido. Caso já existam, o registro atual é retornado sem duplicidade.

### Categoria: Gerenciamento de Pokémons
*   `GET /Pokemons`: Retorna a lista de Pokémons armazenados localmente. O endpoint possui paginação e suporte a ordenação através do parâmetro `ordem` (opções: nome, altura, tipo ou peso).
*   `GET /Pokemons/{id}`: Realiza a busca detalhada de um Pokémon específico na base local utilizando o ID como busca.

---

## Estrutura do Banco de Dados

O banco de dados SQLite (`atividadeawait.db`) armazena os seguintes atributos por registro:
*   `id`: Identificador único (proveniente da PokéAPI).
*   `nome_pokemon`: Nome do Pokémon.
*   `altura_pokemon`: Altura informada em formato numérico.
*   `peso_pokemon`: Peso informado em formato numérico.
*   `tipo_pokemon`: Lista de tipos consolidada em uma única string textual.
*   `sprites_pokemon`: URL com o caminho do arquivo de imagem padrão.
