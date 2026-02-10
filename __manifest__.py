# -*- coding: utf-8 -*-
{
    'name': "Geracad Certificados",
    'summary': "Cadastro de edições de curso para certificação e emissão de certificados com verificação por QR code",
    'description': """
        Módulo independente para cadastro de edições de curso (certificação),
        alunos por edição, geração de certificado PDF (frente e verso) com QR code
        e verificação pública de autenticidade via URL.
    """,
    'author': "Afonso Carvalho",
    'website': "http://www.netcom-ma.com.br",
    'category': 'Academico',
    'version': '14.0.1.0',
    'depends': ['base', 'web', 'geracad_curso'],
    'external_dependencies': {'python': ['Pillow']},
    'data': [
        'security/geracad_certificados_security.xml',
        'security/ir.model.access.csv',
        'views/geracad_certificados_views.xml',
        'views/res_partner_professor_inherit_view.xml',
        'reports/report_certificado_template.xml',
        'reports/report_lista_entrega_certificado_template.xml',
        'reports/report_actions.xml',
        'views/certificado_verificar_templates.xml',
    ],
    'installable': True,
    'application': False,
}
