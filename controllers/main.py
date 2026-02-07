# -*- coding: utf-8 -*-
"""
Controller de verificação de autenticidade do certificado via token (QR code).
Rota pública: GET /certificados/verificar/<token>
"""

from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


class CertificadoVerificarController(http.Controller):
    """Exibe página de validação do certificado quando o token existe."""

    def _get_company_data(self):
        """Retorna dict com dados da empresa (nome, CNPJ, endereço, telefone, logo) para os templates."""
        company = request.env.company.sudo()
        partner = company.partner_id or company
        endereco_partes = []
        if getattr(partner, 'street', None):
            endereco_partes.append(partner.street)
        if getattr(partner, 'street2', None):
            endereco_partes.append(partner.street2)
        if getattr(partner, 'city', None):
            cidade_uf = partner.city
            if getattr(partner, 'state_id', None) and partner.state_id:
                cidade_uf += ' - %s' % (partner.state_id.code or partner.state_id.name)
            if getattr(partner, 'zip', None) and partner.zip:
                cidade_uf += ' - CEP %s' % partner.zip
            endereco_partes.append(cidade_uf)
        if getattr(partner, 'country_id', None) and partner.country_id:
            endereco_partes.append(partner.country_id.name)
        endereco_completo = ', '.join(endereco_partes) if endereco_partes else ''
        cnpj = company.vat or getattr(company, 'l10n_br_cnpj_cpf', None) or ''
        if not cnpj and company.partner_id:
            cnpj = company.partner_id.vat or getattr(company.partner_id, 'l10n_br_cnpj_cpf', None) or ''
        company_logo_data_uri = ''
        if company.logo:
            logo = company.logo
            if isinstance(logo, bytes):
                logo = logo.decode('ascii')
            company_logo_data_uri = 'data:image/png;base64,' + logo
        return {
            'company_nome': company.name,
            'company_cnpj': cnpj,
            'endereco_completo': endereco_completo,
            'company_telefone': company.phone or getattr(company, 'mobile', None) or (company.partner_id and (company.partner_id.phone or company.partner_id.mobile)) or '',
            'company_logo_data_uri': company_logo_data_uri,
        }

    @http.route(
        '/certificados/verificar/<string:token>',
        type='http',
        auth='public',
        csrf=False,
    )
    def verificar_certificado(self, token, **kwargs):
        """
        Busca geracad.certificados.curso.aluno pelo token.
        Se existir: renderiza template com "Certificado válido" e dados.
        Se não existir: retorna 404 com página "Não encontrado".
        """
        CertificadoCursoAluno = request.env['geracad.certificados.curso.aluno'].sudo()
        linha = CertificadoCursoAluno.search([('token', '=', token)], limit=1)
        if not linha:
            return redirect('/certificados/nao-encontrado')
        company_data = self._get_company_data()
        return request.render(
            'geracad_certificados.certificado_verificar_page',
            {
                'linha': linha,
                'curso': linha.curso_id,
                'nome_aluno': linha.nome_aluno,
                **company_data,
            },
        )

    @http.route(
        '/certificados/nao-encontrado',
        type='http',
        auth='public',
        csrf=False,
    )
    def certificado_nao_encontrado(self, **kwargs):
        """Página exibida quando o token do certificado não existe."""
        company_data = self._get_company_data()
        return request.render(
            'geracad_certificados.certificado_nao_encontrado_page',
            company_data,
        )
