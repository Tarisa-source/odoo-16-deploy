# attendance_machine/__manifest__.py
{
    'name': 'Attendance Machine',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Module for Attendance Machine',
    'description': """
        This module stores custom attendance data machine and displays it in a tree view.
    """,
    'author': 'Dian',
    'depends': ['base', 'hr_attendance'],
    'data': [
        'views/attendance_view.xml',
        'data/schedule_action.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
}
