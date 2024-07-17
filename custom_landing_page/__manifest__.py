{
    'name': 'Custom Attendance or Project Redirection',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Redirect to Attendance or Project menu based on check-in status',
    'description': """
        This module redirects users to the Attendance menu if they haven't checked in today,
        and to the Project menu if they have already checked in.
    """,
    'author': 'Dian',
    'depends': ['base', 'hr_attendance', 'project'],
    'data': [
        'data/attendance_or_project_action.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
