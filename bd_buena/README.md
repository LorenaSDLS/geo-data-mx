🗂 Proyecto FLE – Base de Datos PostGIS (Docker)

Este proyecto contiene la base de datos fle_db con PostGIS ya configurada y cargada usando Docker.

Incluye:
- PostGIS (PostgreSQL 16 + extensión espacial)
- Adminer para visualización
- Script `mi_base.sql` que inicializa todas las tablas, relaciones y datos.

🚀 Requisitos
- Docker
- Docker Compose

▶️ Cómo iniciar la base de datos
1. Crear un archivo `.env` en la raíz del proyecto con las variables:

POSTGRES_USER=tu_usuario 
POSTGRES_PASSWORD=tu_contraseña 
POSTGRES_DB=fle_db


En la raíz del proyecto ejecutar:

docker compose up -d


Esto va a:
- Crear el contenedor de PostGIS
- Crear la base `fle_db`
- Ejecutar automáticamente `mi_base.sql`
- Levantar Adminer

🌐 Acceso a la base de datos
Adminer (recomendado para ver tablas y datos)

Abrir en el navegador:

http://localhost:8080


Credenciales:
- Sistema: PostgreSQL
- Servidor: `postgres_fle`
- Usuario: el definido en `.env`
- Contraseña: la definida en `.env`
- Base de datos: `fle_db`

🛠 Acceso desde terminal
docker exec -it postgres_fle psql -U $POSTGRES_USER -d $POSTGRES_DB


🔁 Reinicializar la base de datos

Si necesitas borrar todo y recrearlo:

docker compose down -v
docker compose up -d

📁 Estructura del proyecto
/ 
├── docker-compose.yml 
├── mi_base.sql 
├── README.md 
└── .gitignore
