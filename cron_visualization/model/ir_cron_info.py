# -*- coding: utf-8 -*-
import odoo
from odoo import fields, models, api


class IrCronInfo(models.Model):
    _name = 'ir.cron.info'
    # TODO: When restarting the server, the cron info can be still running. Need to reset all data at startup.

    ir_cron_id = fields.Many2one('ir.cron', string='Cron', required=True, ondelete='cascade')
    is_running = fields.Boolean(string='Is Running', readonly=True, default=False)
    started_at = fields.Datetime(string='Started At', readonly=True)
    history = fields.Char(string='History', readonly=True)

    def add_history(self, success):
        # Add the duration to the history and keep only the last 10 runs
        self.ensure_one()
        history = self.history.split(',') if self.history else []
        duration = (fields.Datetime.now() - self.started_at).total_seconds() / 60
        history.append('{};{}'.format(success, duration))
        self.history = ','.join(history[-10:])
