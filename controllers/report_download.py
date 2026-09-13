# -*- coding: utf-8 -*-
"""
Nome do arquivo PDF do certificado.

O controller do core (web) só avalia `print_report_name` quando há um único
registro (`not len(obj) > 1`); em lote o arquivo sai como "Certificado.pdf".
Aqui esse caso é tratado apenas para o relatório de certificado: com mais de um
aluno o nome passa a ser o do curso com a data.
"""

import json
import logging

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import ReportController

_logger = logging.getLogger(__name__)

REPORT_CERTIFICADO = 'geracad_certificados.report_certificado_template'


class ReportControllerCertificado(ReportController):
    """Ajusta o Content-Disposition do certificado quando o PDF é um lote."""

    @http.route()
    def report_download(self, data, token, context=None):
        response = super(ReportControllerCertificado, self).report_download(
            data, token, context=context)
        try:
            nome = self._nome_arquivo_certificado_lote(data)
            if nome:
                response.headers.set('Content-Disposition', content_disposition(nome))
        except Exception:  # nunca impedir o download por causa do nome
            _logger.warning('Falha ao nomear o PDF de certificados em lote', exc_info=True)
        return response

    def _nome_arquivo_certificado_lote(self, data):
        """Retorna o nome do arquivo, ou False se não for lote de certificados."""
        url, tipo = json.loads(data)[:2]
        if tipo != 'qweb-pdf' or '/report/pdf/' not in url:
            return False
        reportname = url.split('/report/pdf/')[1].split('?')[0]
        if '/' not in reportname:
            return False
        reportname, docids = reportname.split('/', 1)
        if reportname != REPORT_CERTIFICADO:
            return False
        ids = [int(x) for x in docids.split(',') if x.strip().isdigit()]
        if len(ids) <= 1:
            # um só aluno: o core já nomeia pelo print_report_name
            return False
        alunos = request.env['geracad.certificados.curso.aluno'].browse(ids)
        return '%s.pdf' % alunos._get_nome_arquivo_lote()
