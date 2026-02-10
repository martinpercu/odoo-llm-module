# Contexto del Proyecto: Chatbot IA Odoo 2

Este es un módulo de Odoo ubicado en `/addons/chatbot_ia_2`. Su función es actuar como un mini-agente que consulta la base de datos de Odoo mediante KPIs predefinidos.

## Restricciones de Alcance
- **Solo analizar:** La carpeta `/addons/chatbot_ia_2`.
- **Ignorar:** El core de Odoo, carpetas `__pycache__`, y otros módulos estándar.
- **Enfoque:** Lógica de `chatbot.ia2` (modelos), integración con la API de OpenAI (vía library `openai`) y los modelos de KPI en `models/kpi_*.py`.

## Estructura del Módulo
- `models/chatbot_ia2.py`: Lógica principal, loop de OpenAI y manejo de mensajes.
- `models/kpi_*.py`: Abstracciones para consultas SQL/ORM (Ventas, Facturación, Productos).
- `views/`: Interfaz de chat personalizada en Odoo.

## Stack Tecnológico
- **Backend:** Python (Odoo 14.0+ Framework).
- **IA:** OpenAI SDK (Model: gpt-4o-mini).
- **Frontend:** Odoo XML Views + HTML/CSS in-line para las burbujas de chat.

## Guía de Desarrollo
- Al modificar KPIs, siempre respetar el patrón de retorno: `{'ids': [...], 'data': [...], 'mensaje': "..."}`.
- El chatbot usa un sistema de mensajes ocultos (`visible=False`) para guardar el historial de llamadas a funciones y respuestas de la API sin ensuciar la vista del usuario.
- Siempre usar `OdooJSONEncoder` para serializar datos que van a la IA.