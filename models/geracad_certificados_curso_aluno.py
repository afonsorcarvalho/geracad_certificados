# -*- coding: utf-8 -*-
"""
Modelo geracad.certificados.curso.aluno: nome do aluno e token por certificado.
Sem vínculo com res.partner nem com a tabela de alunos do geracad_curso.
Apenas: curso (relação com o curso), nome do aluno (Char) e token (único).
"""

import base64
import os
import uuid

from odoo import api, fields, models


class GeracadCertificadosCursoAluno(models.Model):
    _name = 'geracad.certificados.curso.aluno'
    _description = 'Aluno do curso (certificação) - nome e token'

    curso_id = fields.Many2one(
        'geracad.certificados.curso',
        string='Curso',
        required=True,
        ondelete='cascade',
    )
    nome_aluno = fields.Char(
        string='Nome do aluno',
        required=True,
    )
    token = fields.Char(
        string='Token',
        readonly=True,
        copy=False,
        index=True,
        help='Token único gerado automaticamente para verificação do certificado (QR code).',
    )

    _sql_constraints = [
        ('token_unique', 'UNIQUE(token)', 'O token deve ser único.'),
    ]

    @api.model
    def create(self, vals):
        """Gera token único automaticamente para cada aluno inserido no curso."""
        if not vals.get('token'):
            vals['token'] = uuid.uuid4().hex
        return super().create(vals)

    def _get_module_static_path(self, *parts):
        """Retorna o caminho absoluto para um arquivo em static/ do módulo."""
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(module_dir, 'static', *parts)

    def _get_static_image_data_uri(self, *path_parts, mime='image/png'):
        """
        Lê imagem do static do módulo e retorna data URI (base64).
        Garante que o PDF mostre a imagem sem depender de URL (wkhtmltopdf não acessa URLs em alguns ambientes).
        """
        try:
            path = self._get_module_static_path(*path_parts)
            if not os.path.isfile(path):
                return ''
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
            return 'data:%s;base64,%s' % (mime, data)
        except Exception:
            return ''

    def _get_certificado_fundo_data_uri(self):
        """Data URI da imagem de fundo do certificado (embed no HTML para o PDF)."""
        return self._get_static_image_data_uri('img', 'certificado_fundo.png')

    def _get_canto_tl_data_uri(self):
        """Data URI do ornamento de canto (SVG)."""
        return self._get_static_image_data_uri('img', 'certificado_canto_tl.svg', mime='image/svg+xml')

    def _get_selo_data_uri(self):
        """Data URI do selo (PNG – selo tipo fita/medalha no certificado)."""
        return self._get_static_image_data_uri('img', 'certificado_selo.png', mime='image/png')

    def _get_base_url(self):
        """URL base do sistema (para link de verificação do QR)."""
        return (self.env['ir.config_parameter'].sudo().get_param('web.base.url') or '').rstrip('/')

    def _get_verification_url(self):
        """
        Retorna a URL absoluta para verificação do certificado.
        """
        self.ensure_one()
        base = self._get_base_url()
        return '%s/certificados/verificar/%s' % (base, self.token or '')

    def get_company_logo_data_uri(self):
        """Retorna o logo da empresa como data URI (string) para uso em img src. Evita erro ao concatenar bytes."""
        self.ensure_one()
        logo = self.env.company.logo
        if not logo:
            return ''
        if isinstance(logo, bytes):
            logo = logo.decode('ascii')
        return 'data:image/png;base64,' + logo

    def get_qrcode_base64(self):
        """Gera QR code com a URL de verificação; retorna PNG em base64."""
        self.ensure_one()
        try:
            import qrcode
            from io import BytesIO
        except ImportError:
            return ''
        url = self._get_verification_url()
        buffer = BytesIO()
        img = qrcode.make(url)
        img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('ascii')

    def action_gerar_certificado(self):
        """Abre o relatório PDF do certificado para o registro atual."""
        self.ensure_one()
        return self.env.ref('geracad_certificados.action_report_certificado').report_action(self)
