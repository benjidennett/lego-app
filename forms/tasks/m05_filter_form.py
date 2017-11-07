# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------

from wtforms import RadioField
from wtforms.validators import InputRequired

from lego.forms.tasks.base_task_form import BaseTaskForm


class M05FilterForm(BaseTaskForm):
    title = 'Not set'
    info = 'Move the Filter north until the lock latch drops.'

    # fields
    task_complete = RadioField('Task complete:',
        choices=[('y', 'Yes (30 points)'),
                 ('n', 'No (0 points)')],
        validators=[InputRequired('Please make a choice for Task complete')])


    def points_scored(self) -> int:
        """Calculate the points scored for the task."""
        if self.task_complete.data == 'y':
            return 30

        return 0