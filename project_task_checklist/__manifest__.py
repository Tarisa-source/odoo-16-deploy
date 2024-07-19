{
    'name': "Project Task Check List",
    'version': '16.0.1.0.0',
    'summary': """Check-list task""",
    'description': """Create and check task completion on the basis of checklists""",
    'category': 'Project',
    'author': 'Tarisa dan Dian',
    'depends': ['project', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_check_list.xml',
        'wizard/project_task_checklist_template_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_task_checklist/static/src/scss/project_check_list.scss',
            'project_task_checklist/static/src/js/checklist_title_one2many.js',
            'project_task_checklist/static/src/js/checklist_title_list_renderer.js',
            'project_task_checklist/static/src/js/checklist_title_one2many_field.js',
            'project_task_checklist/static/src/xml/KanbanRender.xml',
        ]
    },

    'images': ['static/description/banner.gif'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
