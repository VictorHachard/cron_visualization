# -*- coding: utf-8 -*-
import datetime

from odoo import fields, models, api
from odoo.exceptions import UserError


class CvIrCronHistory(models.Model):
    _name = 'cv.ir.cron.history'
    _description = 'Cron History'
    _rec_name = 'ir_cron_id'
    _order = 'id desc'

    ir_cron_id = fields.Many2one('ir.cron', string='Cron', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
    type = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], string='Type', readonly=True)
    state = fields.Selection([('success', 'Success'), ('fail', 'Failed'), ('interruption', 'Interruption'), ('running', 'Running')],
                             string='State', readonly=True, default='running',
                             help="""Success: The cron finished successfully.
    Failed: The cron finished with an error.
    Interruption: The cron was interrupted (server restart, ...).
    Running: The cron is currently running.""")

    started_at = fields.Datetime(string='Started At', readonly=True, default=fields.Datetime.now)
    ended_at = fields.Datetime(string='Ended At', readonly=True)
    duration = fields.Float(string='Duration', readonly=True, group_operator="avg")

    error = fields.Text(string='Error', readonly=True, help='Error message if the cron failed.')

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
        for cron in self:
            if cron.started_at < fields.Datetime.now() - datetime.timedelta(minutes=1):
                try:
                    cron.ir_cron_id._try_lock()
                    cron.state = 'interruption'
                except UserError as e:
                    pass

    def name_get(self):
        return [(cron.id, '{}'.format(cron.ir_cron_id.name)) for cron in self]

    @api.autovacuum
    def _gc_history(self):
        # delete history older than 30 days
        domain = [('create_date', '<', fields.Datetime.now() - datetime.timedelta(days=30))]
        return self.sudo().search(domain).unlink()
