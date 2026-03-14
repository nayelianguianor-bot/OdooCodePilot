from odoo import models, fields

class PilotRegistro(models.Model):
    _name = 'pilot.registro'
    _description = 'Registro de OdooCodePilot'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('activo', 'Activo'),
        ('cerrado', 'Cerrado'),
    ], string='Estado', default='borrador')
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    activo = fields.Boolean(string='Activo', default=True)
