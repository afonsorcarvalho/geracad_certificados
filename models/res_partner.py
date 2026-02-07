# -*- coding: utf-8 -*-
"""
Extensão de res.partner para adicionar assinatura do professor.
Usada no formulário de professores e nos certificados.
"""

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    assinatura_professor = fields.Binary(
        string='Assinatura do professor',
        help='Assinatura exibida em certificados quando o parceiro atua como instrutor ou responsável técnico.',
    )
