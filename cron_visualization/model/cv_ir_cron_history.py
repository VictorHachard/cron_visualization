# -*- coding: utf-8 -*-
import odoo
from odoo import fields, models, api
from odoo.exceptions import UserError


class CvIrCronHistory(models.Model):
    _name = 'cv.ir.cron.history'
    _description = 'Cron History'

    ir_cron_id = fields.Many2one('ir.cron', string='Cron', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    state = fields.Selection([('success', 'Success'), ('fail', 'Failed'), ('interruption', 'Interruption')], string='State', readonly=True)

    started_at = fields.Datetime(string='Started At', readonly=True, default=fields.Datetime.now)
    ended_at = fields.Datetime(string='Ended At', readonly=True)
    duration = fields.Float(string='Duration', readonly=True)

    error = fields.Text(string='Error', readonly=True)

    def finish(self, success, error=False):
        self.ensure_one()
        update = {
            'state': 'success' if success else 'fail',
            'ended_at': fields.Datetime.now(),
            'duration': (fields.Datetime.now() - self.started_at).total_seconds() / 60,
        }
        if error:
            update['error'] = error
        self.write(update)

    def check_integrity(self):
        # Check if cron are still running (in case of a server restart) using the lock on cron.
        for rec in self:
            cron = rec.ir_cron_id
            try:
                cron._try_lock()
                rec.state = 'interruption'
            except UserError as e:
                pass

    def name_get(self):
        return [(cron.id, '{}'.format(cron.ir_cron_id.name)) for cron in self]
