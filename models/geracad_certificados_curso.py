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
from odoo.exceptions import UserError


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
    # Dados administrativos da turma: usados no Registro de Treinamento (lista de
    # presença), não aparecem no certificado.
    codigo_treinamento = fields.Char(
        string='Código do treinamento',
        help='Código interno do treinamento (ex.: DD-001).',
    )
    turma = fields.Char(
        string='Turma',
        help='Identificação da turma (ex.: T-2026/01).',
    )
    local = fields.Char(
        string='Local',
        help='Local onde o treinamento foi realizado (ex.: Sala 2 - NetCom).',
    )
    horario = fields.Char(
        string='Horário',
        help='Horário das aulas em texto livre (ex.: 08:00 às 12:00).',
    )
    e_direcao_defensiva = fields.Boolean(
        string='Direção Defensiva',
        help='Define o tipo do Registro de Treinamento: marcado, a tabela sai '
             'com as colunas de CNH (Categoria / Registro / RENACH); '
             'desmarcado, sai a tabela geral (Matrícula / Assinatura / '
             'Gerência-Empresa).',
    )
    data_dia_1 = fields.Date(
        string='1º dia',
        help='Vira o cabeçalho da coluna de presença correspondente no '
             'Registro de Treinamento; em branco, a coluna sai sem cabeçalho.',
    )
    data_dia_2 = fields.Date(
        string='2º dia',
        help='Vira o cabeçalho da coluna de presença correspondente no '
             'Registro de Treinamento; em branco, a coluna sai sem cabeçalho.',
    )
    data_dia_3 = fields.Date(
        string='3º dia',
        help='Vira o cabeçalho da coluna de presença correspondente no '
             'Registro de Treinamento; em branco, a coluna sai sem cabeçalho.',
    )
    data_dia_4 = fields.Date(
        string='4º dia',
        help='Vira o cabeçalho da coluna de presença correspondente no '
             'Registro de Treinamento; em branco, a coluna sai sem cabeçalho.',
    )
    data_dia_5 = fields.Date(
        string='5º dia',
        help='Vira o cabeçalho da coluna de presença correspondente no '
             'Registro de Treinamento; em branco, a coluna sai sem cabeçalho.',
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
    instrutor_matricula = fields.Char(
        string='Matrícula (Instrutor)',
        help='Matrícula do instrutor; sai no Registro de Treinamento.',
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

    def action_gerar_todos_certificados(self):
        """Gera um único PDF com o certificado de todos os alunos da edição.

        Os alunos saem em ordem alfabética para facilitar a conferência da pilha
        impressa. Usa o mesmo relatório do botão individual.
        """
        self.ensure_one()
        alunos = self.aluno_ids.sorted(lambda a: (a.nome_aluno or '').lower())
        if not alunos:
            raise UserError('Nenhum aluno cadastrado nesta edição do curso.')
        return self.env.ref('geracad_certificados.action_report_certificado').report_action(alunos)

    def action_imprimir_registro_treinamento(self):
        """Abre o PDF do Registro de Treinamento (lista de presença) desta edição."""
        self.ensure_one()
        if not self.aluno_ids:
            raise UserError('Nenhum aluno cadastrado nesta edição do curso.')
        return self.env.ref(
            'geracad_certificados.action_report_registro_treinamento'
        ).report_action(self)

    def get_alunos_ordenados(self):
        """Alunos em ordem alfabética, como saem nas listas impressas."""
        self.ensure_one()
        return self.aluno_ids.sorted(lambda a: (a.nome_aluno or '').lower())

    def get_nome_arquivo_registro_treinamento(self):
        """Nome do PDF do Registro de Treinamento: "<curso> - <dd-mm-aaaa>"."""
        self.ensure_one()
        data = self.date_inicio.strftime('%d-%m-%Y') if self.date_inicio else ''
        nome = 'Registro de Treinamento - %s' % (self.name or '')
        if data:
            nome = '%s - %s' % (nome, data)
        # barras quebram o nome do arquivo no navegador
        return nome.replace('/', '-').replace('\\', '-')

    # Acima deste tanto de texto o conteúdo programático vai para duas colunas.
    #
    # Medido contra os 29 cursos de produção (text_content, a mesma unidade que
    # o método usa): os que estouram para 2 páginas vão de 1173 a 2138, mas o
    # maior que ainda cabe tem 1538 — não há corte limpo por caracteres, porque
    # o que ocupa altura é o número de parágrafos (cada um com sua margem) tanto
    # quanto o texto. 850 fica abaixo de todos os que estouram, com margem; o
    # preço é que ~5 cursos que hoje cabem em coluna única também passam a sair
    # em duas.
    LIMITE_TEXTO_DUAS_COLUNAS = 850

    def _bloco_sem_texto(self, elemento):
        """True se `elemento` (e sua subárvore) não carrega texto visível."""
        texto = elemento.text_content()
        return not texto or not texto.strip()

    def _stripar_bordas_vazias(self, pai):
        """Remove, dos filhos diretos de `pai`, a sequência inicial e a final
        que não carregam texto (ver _bloco_sem_texto). Blocos vazios NO MEIO
        são preservados — uma linha em branco deixada de propósito entre duas
        seções não é nossa para tirar.

        Qualquer .tail (texto solto) de um bloco removido é preservado,
        prendendo-o no texto do vizinho que sobrar (ou de `pai`, se não sobrar
        vizinho desse lado) — para não perder conteúdo por causa de um <p>
        vazio colado nele.
        """
        filhos = list(pai)
        inicio = 0
        while inicio < len(filhos) and self._bloco_sem_texto(filhos[inicio]):
            removido = filhos[inicio]
            if removido.tail and removido.tail.strip():
                pai.text = (pai.text or '') + removido.tail
            pai.remove(removido)
            inicio += 1
        filhos = filhos[inicio:]
        fim = len(filhos) - 1
        while fim >= 0 and self._bloco_sem_texto(filhos[fim]):
            removido = filhos[fim]
            if removido.tail and removido.tail.strip():
                anterior = filhos[fim - 1] if fim > 0 else None
                if anterior is not None:
                    anterior.tail = (anterior.tail or '') + removido.tail
                else:
                    pai.text = (pai.text or '') + removido.tail
            pai.remove(removido)
            fim -= 1

    def get_conteudo_programatico_render(self):
        """HTML do conteúdo programático pronto para o certificado.

        Conteúdo longo sai em duas colunas. O wkhtmltopdf desta versão ignora
        column-count do CSS (testado), então a divisão é feita aqui: os blocos
        de topo do HTML (os <p>) são repartidos em duas metades de texto
        equilibrado e remontados dentro de uma tabela de duas células.

        Antes de mais nada, blocos vazios (sem texto) do início e do fim do
        conteúdo são removidos — ver comentário junto de _stripar_bordas_vazias
        sobre o porquê. Devolve esse HTML já limpo em todo caminho de saída:
        quando ele é curto, quando já vem em duas colunas (marcador cp-2col,
        para o caso de o dado já ter sido normalizado — esse caso não passa
        pela limpeza, pois já foi normalizado antes), quando não há blocos
        suficientes para repartir, ou quando o conteúdo é uma lista única
        (<ol>/<ul>) — ver comentário mais abaixo sobre por que listas ficam de
        fora.
        """
        self.ensure_one()
        html = self.conteudo_programatico or ''
        if not html.strip():
            return ''
        if 'cp-2col' in html:
            return html
        try:
            from lxml import html as lxml_html
            raiz = lxml_html.fragment_fromstring(html, create_parent='div')
        except Exception:
            return html

        # Conteúdo colado do Word: além do texto real, vem com parágrafos
        # vazios do editor (<p></p>, <p><br></p>) e, às vezes, o parágrafo de
        # quebra de página que o Word insere depois do <div> que envolve tudo.
        # Isso é ~90pt de espaço morto. O certificado é calibrado para caber
        # numa folha só com pouquíssima folga (~22px, ver
        # reports/report_certificado_template.xml) porque o bloco de
        # assinaturas fica ancorado ao fundo da folha (vertical-align: bottom)
        # — então esse espaço morto é o que empurra QR e assinaturas para a
        # página 2. Medido em produção no curso "Direção Defensiva -
        # Reciclagem": o certificado de WANDERSON NUNES SANTOS foi de 2
        # páginas para 1 ao remover esses blocos; nos demais alunos da mesma
        # turma a folga no rodapé praticamente dobrou (de ~43-53pt para
        # ~85-105pt). Por isso a limpeza roda incondicionalmente, antes de
        # qualquer outra decisão — o espaço morto prejudica a coluna única
        # tanto quanto a divisão em duas colunas.
        #
        # As sobras costumam estar em dois níveis: soltas no topo (o
        # parágrafo de quebra de página do Word, por exemplo) e dentro do
        # <div> que envolve o conteúdo real (parágrafo vazio antes da tabela,
        # parágrafos vazios depois dela) — por isso a limpeza roda no nível
        # de cima e, se sobrar um único <div> envolvendo tudo, de novo dentro
        # dele.
        self._stripar_bordas_vazias(raiz)
        if len(raiz) == 1 and raiz[0].tag == 'div':
            self._stripar_bordas_vazias(raiz[0])

        html = (raiz.text or '') + ''.join(
            lxml_html.tostring(filho, encoding='unicode') for filho in raiz
        )
        if not html.strip():
            return ''

        if len(raiz.text_content() or '') <= self.LIMITE_TEXTO_DUAS_COLUNAS:
            return html

        # Texto solto antes do primeiro elemento fica em raiz.text e não entra
        # em list(raiz); vira um <p> para não sumir do certificado. (As caudas
        # não precisam disso: tostring já inclui o .tail de cada elemento.)
        if raiz.text and raiz.text.strip():
            primeiro = raiz.makeelement('p')
            primeiro.text = raiz.text
            raiz.text = None
            raiz.insert(0, primeiro)

        # Desce por wrappers. Vários cursos guardam tudo dentro de um <div>
        # único; repartir o nível de cima daria uma coluna com todo o texto e
        # outra vazia, o que deixa o certificado MAIOR, não menor.
        for _ in range(4):
            filhos = list(raiz)
            if not filhos:
                break
            pesos = [len(b.text_content() or '') for b in filhos]
            total = sum(pesos) or 1
            maior = pesos.index(max(pesos))
            # Não descer para dentro de uma <ol>/<ul>: ela seria "consumida"
            # aqui e os <li> virariam os próprios blocos a repartir, saindo
            # soltos no HTML final (sem <ol>/<ul> em volta) e perdendo a
            # numeração. Isso também é o que permite detectar, logo abaixo,
            # que o conteúdo é uma lista única — caso em que não se reparte.
            if (pesos[maior] / float(total) > 0.85 and len(list(filhos[maior])) > 1
                    and filhos[maior].tag not in ('ol', 'ul')):
                raiz = filhos[maior]
                continue
            break

        blocos = list(raiz)
        # Lista única: NÃO reparte. Medido em PDF renderizado: uma ementa de
        # 22 itens (média 83 caract.) foi de 176.5pt a 307.5pt (+74%) e outra
        # de 24 itens (média 73 caract.) de 192.6pt a 296.0pt (+54%) ao virar
        # duas colunas — o oposto do que a divisão busca. A causa é estrutural:
        # cada <li> carrega recuo e marcador, um custo horizontal fixo que não
        # encolhe quando a coluna é partida ao meio, então cada item ganha
        # linhas mais rápido do que reduzir a quantidade de itens economiza.
        # Uma segunda medição com listas sintéticas confirmou a direção e não
        # achou tamanho de item (testado até 800 caract.) em que a lista passe
        # a compensar. Por isso listas ficam de fora da divisão em colunas.
        if len(blocos) == 1 and blocos[0].tag in ('ol', 'ul'):
            return html
        if len(blocos) < 2:
            return html

        pesos_blocos = [len(b.text_content() or '') for b in blocos]
        metade = sum(pesos_blocos) / 2.0
        acumulado = 0
        corte = len(blocos) - 1
        for i, peso in enumerate(pesos_blocos):
            if acumulado + peso / 2.0 >= metade:
                corte = max(1, i)
                break
            acumulado += peso

        def montar(parte):
            return ''.join(
                lxml_html.tostring(b, encoding='unicode') for b in parte
            )

        # Divisão muito torta não compensa: a coluna cheia fica estreita, quebra
        # em mais linhas e o resultado ocupa mais altura do que a coluna única.
        esquerda = sum(pesos_blocos[:corte])
        if max(esquerda, sum(pesos_blocos) - esquerda) > 0.70 * (sum(pesos_blocos) or 1):
            return html

        return (
            '<table class="cp-2col"><tr>'
            '<td>%s</td><td>%s</td>'
            '</tr></table>'
        ) % (montar(blocos[:corte]), montar(blocos[corte:]))

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
        """Retorna a data de conclusão por extenso (ex.: "7 de agosto de 2026")
        para a linha de local/data do certificado.

        Usa date_fim; se não preenchida (curso em um só dia, ver help do
        campo), cai para date_inicio. Sem nenhuma das duas, retorna ''.
        O dia não sai com zero à esquerda.
        """
        self.ensure_one()
        data = self.date_fim or self.date_inicio
        if not data:
            return ''
        return '%d de %s de %d' % (
            data.day, self.MES_COMPLETO[data.month - 1], data.year,
        )

    # Hardcoded em vez de strftime('%b')/('%B'): o container roda em locale C,
    # que devolveria 'Jan', 'Feb', 'Mar' / 'January' etc. em inglês.
    MES_ABREV = ('jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set',
                 'out', 'nov', 'dez')
    MES_COMPLETO = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                     'julho', 'agosto', 'setembro', 'outubro', 'novembro',
                     'dezembro')

    def get_dias_registro(self):
        """Datas dos 5 dias formatadas ("01/jan") para o cabeçalho das colunas
        de presença do Registro de Treinamento.

        Sempre devolve 5 posições (dia vazio vira ''), para o relatório poder
        iterar sem checar quantos dias foram preenchidos.
        """
        self.ensure_one()
        dias = [self.data_dia_1, self.data_dia_2, self.data_dia_3,
                self.data_dia_4, self.data_dia_5]
        return [
            '%02d/%s' % (d.day, self.MES_ABREV[d.month - 1]) if d else ''
            for d in dias
        ]

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
