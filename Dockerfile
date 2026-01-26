FROM odoo:14

USER root
RUN pip3 install openai==0.28.1
USER odoo
