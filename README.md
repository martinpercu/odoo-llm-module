# Odoo 14 - Chatbot IA

> Modulos de Odoo que permiten consultar KPIs del ERP usando lenguaje natural, potenciados por OpenAI

[![Odoo](https://img.shields.io/badge/Odoo-14.0-714B67.svg)](https://www.odoo.com/)
[![Python](https://img.shields.io/badge/Python-3.6+-3776AB.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12-336791.svg)](https://www.postgresql.org/)

## Descripcion

Entorno dockerizado de Odoo 14 con **dos modulos custom de chatbot IA** que permiten a los usuarios consultar datos del negocio (ventas, compras, facturacion, productos) mediante lenguaje natural. Los modulos usan **OpenAI Function Calling** para traducir preguntas en consultas ORM/SQL y devolver respuestas formateadas.

El proyecto incluye dos versiones del chatbot, cada una con un enfoque diferente:

- **Chatbot IA v1** - Consulta simple de pregunta/respuesta con 13 KPIs predefinidos
- **Chatbot IA v2** - Agente conversacional multi-turno con function chaining y filtros avanzados

## Arquitectura

### Stack Tecnologico

| Capa | Tecnologia |
|------|------------|
| **ERP** | Odoo 14 Community |
| **Base de datos** | PostgreSQL 12 |
| **IA** | OpenAI GPT-4o-mini (Function Calling) |
| **Infraestructura** | Docker Compose |
| **SDK** | OpenAI Python v0.28.1 |

### Infraestructura Docker

```
┌─────────────────────────────────────────────────┐
│              Docker Compose                      │
│                                                  │
│  ┌──────────────┐       ┌────────────────────┐  │
│  │  PostgreSQL   │       │      Odoo 14       │  │
│  │    :5432      │◄─────►│      :8069         │  │
│  │              │       │                    │  │
│  │  db-grande   │       │  OPENAI_API_KEY    │  │
│  └──────────────┘       └────────────────────┘  │
│                                │                 │
│                         ┌──────┴──────┐          │
│                         │   /addons   │          │
│                         ├─────────────┤          │
│                         │ chatbot_ia  │          │
│                         │ chatbot_ia_2│          │
│                         └─────────────┘          │
└─────────────────────────────────────────────────┘
```

### Estructura del Proyecto

```
odoo14-docker/
  docker-compose.yml          # Orquestacion de servicios
  Dockerfile                  # Imagen Odoo 14 + openai SDK
  config/
    odoo.conf                 # Configuracion de Odoo
  addons/
    chatbot_ia/               # Modulo v1 - Consulta simple
      models/
        chatbot.py            # Logica principal (single-turn)
        kpi/
          ventas.py           # KPIs de ventas (5 funciones)
          compras.py          # KPIs de compras (2 funciones)
          facturacion.py      # KPIs de facturacion (3 funciones)
          helpers.py          # Utilidades de fechas y calculos
      views/
        chatbot_view.xml      # Vista formulario simple
    chatbot_ia_2/             # Modulo v2 - Agente multi-turno
      models/
        chatbot.py            # Logica principal (loop multi-turno)
        message.py            # Modelo de mensajes del chat
        kpi/
          productos.py        # Busqueda de productos con filtros
          ventas.py           # Consulta de ventas con agrupacion
          facturacion.py      # Consulta de facturas por estado
          helpers.py          # Utilidades compartidas
      views/
        chatbot_view.xml      # Vista chat con burbujas estilizadas
        assets.xml            # CSS custom del chat
```

## Modulo 1: Chatbot IA (v1.2)

Chatbot simple de pregunta/respuesta. El usuario escribe una consulta y obtiene una respuesta directa.

### Flujo

```
Usuario escribe pregunta ──► OpenAI elige funcion ──► KPI ejecuta query ──► GPT formatea respuesta
```

### KPIs Disponibles (13)

| Area | Funcion | Descripcion |
|------|---------|-------------|
| Ventas | `get_ventas_mes_actual` | Total de ventas del mes con comparacion mensual |
| Ventas | `get_top_productos` | Productos mas vendidos por monto |
| Ventas | `get_pedidos_pendientes` | Pedidos en estado borrador/pendiente |
| Ventas | `get_top_clientes` | Clientes con mayor volumen de compra |
| Ventas | `get_ticket_promedio` | Valor promedio por orden de venta |
| Compras | `get_compras_mes_actual` | Total de compras del mes con comparacion |
| Compras | `get_top_proveedores` | Proveedores con mayor volumen |
| Facturacion | `get_cuentas_por_cobrar_vencidas` | Facturas de clientes vencidas |
| Facturacion | `get_cuentas_por_pagar_vencidas` | Facturas de proveedores vencidas |
| Facturacion | `get_por_cobrar_proximos_dias` | Cobranzas por vencer en N dias |
| RRHH | `get_cantidad_empleados` | Cantidad total de empleados activos |

### Dependencias Odoo

`base`, `hr`, `sale`, `purchase`, `account`

---

## Modulo 2: Chatbot IA v2 (v2.0)

Agente conversacional avanzado con chat multi-turno, historial de sesiones y function chaining.

### Flujo

```
┌─────────┐     mensaje      ┌──────────┐    function call    ┌─────────┐
│ Usuario │ ───────────────► │  OpenAI  │ ──────────────────► │   KPI   │
│  Chat   │                  │   Loop   │ ◄────────────────── │  Query  │
│         │ ◄─────────────── │ (max 10) │    resultado         │         │
└─────────┘   respuesta       └──────────┘                     └─────────┘
              formateada          │
                                 ▼
                          Puede encadenar
                        multiples funciones
                        antes de responder
```

### KPIs Disponibles (3 flexibles)

| Funcion | Filtros | Descripcion |
|---------|---------|-------------|
| `get_productos` | nombre, rango de precio, categoria, orden, limite | Busqueda avanzada de productos |
| `get_ventas` | producto, vendedor, cliente, agrupacion, periodo, orden | Ventas con agrupacion y periodos |
| `get_facturas` | tipo (AR/AP), estado, vencimiento, cliente, limite | Facturas con filtros de estado |

### Caracteristicas Avanzadas

- **Multi-turno**: Conversaciones con contexto completo entre mensajes
- **Function chaining**: GPT puede encadenar multiples consultas (ej: buscar productos → consultar sus ventas)
- **Proteccion de volumen**: Umbral de 50 registros para evitar respuestas masivas
- **Mensajes ocultos**: Las llamadas a funciones se guardan como mensajes invisibles, manteniendo el chat limpio
- **Chat con burbujas**: Interfaz estilizada con CSS (usuario en azul, asistente en verde)
- **Sesiones**: Historial de conversaciones pasadas con timestamps

### Dependencias Odoo

`base`, `sale`, `account`, `product`, `stock`

## Setup

### Requisitos

- **Docker** y **Docker Compose**
- **API Key de OpenAI** con acceso a `gpt-4o-mini`

### Instalacion

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd odoo14-docker

# 2. Crear archivo .env con la API key
echo "OPENAI_API_KEY=sk-tu-api-key" > .env

# 3. Levantar los servicios
docker compose up -d

# 4. Restaurar la base de datos
#    Ir a http://localhost:8069/web/database/manager
#    Click en "Restore Database" y subir el archivo .dump.zip incluido
```

Acceder a Odoo en `http://localhost:8069`

### Credenciales por defecto

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Password | `uXFjHB42yXfFfkk` |

## Patron de Retorno de KPIs

Todos los KPIs siguen el mismo formato de respuesta:

```python
{
    'ids': [1, 2, 3],          # IDs de registros de Odoo
    'data': [...],              # Datos estructurados
    'mensaje': "Texto legible"  # Resumen en lenguaje natural
}
```

## Autor

**Martin Mendez**
