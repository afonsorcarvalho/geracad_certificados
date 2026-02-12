# -*- coding: utf-8 -*-
"""
Modelo geracad.certificados.curso: edição de curso para certificação.
Campos: nome, data início/fim (período), carga horária, instrutor (res.partner),
conteúdo programático (HTML), alunos (One2many).
Ao enviar assinatura pelo formulário, o fundo claro é removido (PIL: soma R+G+B > 700)
e a imagem é gravada em PNG; o relatório usa esse valor diretamente.
"""

import base64
import io

from odoo import api, fields, models


class GeracadCertificadosCurso(models.Model):
    _name = 'geracad.certificados.curso'
    _description = 'Curso (edição) para certificação'

    name = fields.Char(string='Nome do curso', required=True)
    date_inicio = fields.Date(
        string='Data de início',
        required=True,
        help='Data de início do curso.',
    )
    date_fim = fields.Date(
        string='Data de fim',
        help='Opcional. Se não preenchido, considera-se que o curso foi em um só dia (data de início).',
    )
    carga_horaria = fields.Integer(
        string='Carga horária (horas)',
        help='Carga horária total do curso em horas.',
    )
    instrutor_id = fields.Many2one(
        'res.partner',
        string='Instrutor',
        required=True,
        ondelete='restrict',
        domain=[('e_professor', '=', True)],
        help='Parceiro professor; assinatura no certificado usa image_1920.',
    )
    responsavel_tecnico_id = fields.Many2one(
        'res.partner',
        string='Responsável técnico',
        ondelete='restrict',
        domain=[('e_professor', '=', True)],
        help='Parceiro professor responsável técnico; assinatura exibida ao lado do instrutor no certificado.',
    )
    # Detalhes do instrutor no certificado (Instrutor Técnico)
    instrutor_cargo_funcao = fields.Char(
        string='Cargo/Função (Instrutor)',
        help='Ex.: Instrutor de Trânsito Cat. A/D',
    )
    instrutor_registro = fields.Char(
        string='Registro Nº (Instrutor)',
        help='Número de registro do instrutor (ex.: 03219659910).',
    )
    instrutor_renach = fields.Char(
        string='RENACH (Instrutor)',
        help='Ex.: MA044511469',
    )
    # Detalhes do responsável técnico no certificado
    responsavel_tecnico_cargo_funcao = fields.Char(
        string='Cargo/Função (Responsável técnico)',
        help='Ex.: Eng. Eletricista/ Eng. de Segurança do Trabalho',
    )
    responsavel_tecnico_crea = fields.Char(
        string='CREA (Responsável técnico)',
        help='Ex.: CREA-MA Nº3627D',
    )
    # Assinaturas (imagens) usadas no PDF do certificado; se preenchidas, substituem a foto do parceiro
    assinatura_instrutor = fields.Binary(
        string='Assinatura do instrutor',
        help='Imagem da assinatura (ao enviar, o fundo é removido e gravado em PNG). Se vazio, usa a foto do Instrutor.',
    )
    assinatura_responsavel_tecnico = fields.Binary(
        string='Assinatura do responsável técnico',
        help='Imagem da assinatura (ao enviar, o fundo é removido e gravado em PNG). Se vazio, usa a foto do responsável.',
    )
    conteudo_programatico = fields.Html(string='Conteúdo programático')
    aluno_ids = fields.One2many(
        'geracad.certificados.curso.aluno',
        'curso_id',
        string='Alunos',
        help='Linhas de aluno por curso; cada uma gera um certificado com token único.',
    )

    def get_periodo_display(self):
        """
        Retorna o período formatado para exibição (ex.: certificado).
        Se date_fim estiver preenchida: "dd/mm/yyyy a dd/mm/yyyy".
        Caso contrário (curso em um só dia): "dd/mm/yyyy".
        """
        self.ensure_one()
        if not self.date_inicio:
            return ''
        fmt = '%d/%m/%Y'
        inicio_str = self.date_inicio.strftime(fmt)
        if self.date_fim:
            return '%s a %s' % (inicio_str, self.date_fim.strftime(fmt))
        return inicio_str

    def get_data_conclusao_display(self):
        """Retorna a data de conclusão formatada (dd/mm/yyyy) para o certificado."""
        self.ensure_one()
        if not self.date_inicio:
            return ''
        return self.date_inicio.strftime('%d/%m/%Y')

    @api.onchange('instrutor_id')
    def _onchange_instrutor_id(self):
        """Ao mudar o instrutor, copia assinatura_professor do parceiro para assinatura_instrutor."""
        if self.instrutor_id and getattr(self.instrutor_id, 'assinatura_professor', None):
            self.assinatura_instrutor = self.instrutor_id.assinatura_professor

    @api.onchange('responsavel_tecnico_id')
    def _onchange_responsavel_tecnico_id(self):
        """Ao mudar o responsável técnico, copia assinatura_professor do parceiro para assinatura_responsavel_tecnico."""
        if self.responsavel_tecnico_id and getattr(self.responsavel_tecnico_id, 'assinatura_professor', None):
            self.assinatura_responsavel_tecnico = self.responsavel_tecnico_id.assinatura_professor

    @api.model_create_multi
    def create(self, vals_list):
        """Ao criar, copia assinaturas do parceiro se existirem; depois processa e remove fundo."""
        for vals in vals_list:
            if vals.get('instrutor_id'):
                partner = self.env['res.partner'].browse(vals['instrutor_id'])
                if partner and getattr(partner, 'assinatura_professor', None):
                    vals.setdefault('assinatura_instrutor', partner.assinatura_professor)
            if vals.get('responsavel_tecnico_id'):
                partner = self.env['res.partner'].browse(vals['responsavel_tecnico_id'])
                if partner and getattr(partner, 'assinatura_professor', None):
                    vals.setdefault('assinatura_responsavel_tecnico', partner.assinatura_professor)
            for field in ('assinatura_instrutor', 'assinatura_responsavel_tecnico'):
                if vals.get(field):
                    processed = self._processar_imagem_assinatura_para_png(vals[field])
                    if processed:
                        vals[field] = processed
        return super().create(vals_list)

    def write(self, vals):
        """Ao salvar, copia assinaturas do parceiro se instrutor/responsável mudou; depois processa."""
        # if vals.get('instrutor_id'):
        #     partner = self.env['res.partner'].browse(vals['instrutor_id'])
        #     if partner and getattr(partner, 'assinatura_professor', None):
        #         vals.setdefault('assinatura_instrutor', partner.assinatura_professor)
        # if vals.get('responsavel_tecnico_id'):
        #     partner = self.env['res.partner'].browse(vals['responsavel_tecnico_id'])
        #     if partner and getattr(partner, 'assinatura_professor', None):
        #         vals.setdefault('assinatura_responsavel_tecnico', partner.assinatura_professor)
        for field in ('assinatura_instrutor', 'assinatura_responsavel_tecnico'):
            if vals.get(field):
                processed = self._processar_imagem_assinatura_para_png(vals[field])
                if processed:
                    vals[field] = processed
        return super().write(vals)

    def _processar_imagem_assinatura_para_png(self, image_binary):
        """
        Remove o fundo (rembg ou PIL soma>700) e converte para PNG.
        Retorna a string base64 para gravar no campo Binary (ou None para manter o valor).
        """
        if not image_binary:
            return None
        uri = self._assinatura_to_data_uri(image_binary)
        if not uri or not uri.startswith('data:'):
            return None
        idx = uri.find('base64,')
        if idx >= 0:
            return uri[idx + 7:]
        return None

    def _binary_to_bytes(self, image_binary):
        """Converte valor do campo Binary (base64 ou bytes ou data URI) em bytes."""
        if not image_binary:
            return None
        if isinstance(image_binary, bytes):
            return image_binary
        s = image_binary if isinstance(image_binary, str) else str(image_binary)
        if s.startswith('data:'):
            # data:image/png;base64,XXXX
            idx = s.find('base64,')
            if idx >= 0:
                s = s[idx + 7:]
        return base64.b64decode(s) if s else None

    def _image_white_to_transparent(self, image_binary, soma_limite=700):
        """
        Remove o fundo claro da imagem (lógica do test_remover_fundo_pil.py).
        Pixels com soma R+G+B > soma_limite viram transparentes; saída em PNG.
        Aceita PNG, JPEG ou JPG.
        :param image_binary: bytes, base64 ou data URI
        :param soma_limite: pixels com R+G+B > soma_limite viram transparentes (default 700)
        :return: string base64 da PNG, ou None em caso de erro / imagem inválida
        """
        raw = self._binary_to_bytes(image_binary)
        if not raw:
            return None
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw)).convert('RGBA')
            pixels = img.getdata()
            new_data = []
            for pixel in pixels:
                # Fundo claro (soma R+G+B > 700) -> transparente; senão mantém o pixel
                if sum(pixel[:3]) > 700:  # fundo claro
                    new_data.append((255, 255, 255, 0))  # transparente
                else:
                    new_data.append(pixel)
            img.putdata(new_data)
            out = io.BytesIO()
            img.save(out, format='PNG')
            return base64.b64encode(out.getvalue()).decode('ascii')
        except Exception:
            return None

    def _assinatura_to_data_uri(self, image_binary):
        """
        Retorna data URI da assinatura com fundo removido (PIL: soma R+G+B > 700 → transparente).
        Se o processamento falhar, retorna a imagem original.
        """
        raw_bytes = self._binary_to_bytes(image_binary)
        if not raw_bytes:
            return ''
        # PIL: fundo claro (soma > 700) → transparente; saída PNG
        b64 = self._image_white_to_transparent(image_binary)
        if b64:
            return 'data:image/png;base64,%s' % b64
        # Imagem original (ex.: JPEG)
        b64 = base64.b64encode(raw_bytes).decode('ascii')
        mime = 'image/jpeg' if raw_bytes[:2] == b'\xff\xd8' else 'image/png'
        return 'data:%s;base64,%s' % (mime, b64)

    def get_assinatura_instrutor_data_uri(self):
        """
        Retorna data URI da assinatura do instrutor para o certificado.
        Ordem: assinatura do curso > assinatura do professor em res.partner > image_1920.
        """
        self.ensure_one()
        raw = (
            self.assinatura_instrutor
            or (self.instrutor_id and getattr(self.instrutor_id, 'assinatura_professor', None))
            or (self.instrutor_id and self.instrutor_id.image_1920)
        )
        if not raw:
            return ''
        return self._assinatura_to_data_uri(raw)

    def get_assinatura_responsavel_tecnico_data_uri(self):
        """
        Retorna data URI da assinatura do responsável técnico para o certificado.
        Ordem: assinatura do curso > assinatura do professor em res.partner > image_1920.
        """
        self.ensure_one()
        if not self.responsavel_tecnico_id:
            return ''
        raw = (
            self.assinatura_responsavel_tecnico
            or getattr(self.responsavel_tecnico_id, 'assinatura_professor', None)
            or self.responsavel_tecnico_id.image_1920
        )
        if not raw:
            return ''
        return self._assinatura_to_data_uri(raw)
