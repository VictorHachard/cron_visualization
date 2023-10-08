# -*- coding: utf-8 -*-
import odoo
from odoo import fields, models, api, _


class IrCron(models.Model):
    _inherit = 'ir.cron'

    # Don't store data related to the history. The cursor crash when storing data.
    cv_ir_cron_history_ids = fields.One2many('cv.ir.cron.history', 'ir_cron_id', string='Cron History')
    cv_history_count = fields.Integer(string='History Count', compute='_compute_history_count')

    # ir_cron_info_id = fields.One2many('ir.cron.info', 'ir_cron_id', string='Cron Info', readonly=True)
    is_running = fields.Boolean(string='Is Running', compute='_compute_is_running', help='Is the cron currently running')
    progress_estimated = fields.Float(string='Progress Estimated', compute='_compute_progress_estimated', help='Estimated progress of the current run based on the history')
    running_since = fields.Float(string='Running Since', compute='_compute_running_since', help='How long the cron is running')
    history = fields.Char(string='History',  compute='_compute_history', help='History of the last 10 runs (success;duration)')

    check_history_integrity = fields.Boolean(string='Check History Integrity', compute='_compute_check_history_integrity', help='Check if the cron is still running (in case of a server restart) using the lock on cron.')

    def _compute_check_history_integrity(self):
        for cron in self:
            history = cron.cv_ir_cron_history_ids.filtered(lambda h: not h.state)
            if history:
                history.check_integrity()
            cron.check_history_integrity = True

    def _compute_history_count(self):
        for cron in self:
            cron.cv_history_count = len(cron.cv_ir_cron_history_ids)

    def open_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cron History'),
            'res_model': 'cv.ir.cron.history',
            'view_mode': 'tree',
            'domain': [('ir_cron_id', '=', self.id)],
        }

    def _compute_is_running(self):
        """ Check last history to know if the cron is running. """
        for cron in self:
            if not cron.cv_ir_cron_history_ids:
                cron.is_running = False
                continue
            cron.is_running = cron.cv_ir_cron_history_ids[-1].ended_at is False and not cron.cv_ir_cron_history_ids[-1].state

    def _compute_running_since(self):
        """ Check last history to know how long the cron is running. """
        now = fields.Datetime.now()
        for cron in self:
            if not cron.cv_ir_cron_history_ids or not cron.is_running:
                cron.running_since = False
                continue
            cron.running_since = (now - cron.cv_ir_cron_history_ids[-1].started_at).total_seconds() / 60

    def _compute_progress_estimated(self):
        """ Check history to estimate the progress of the current run. """
        for cron in self:
            if not cron.cv_ir_cron_history_ids or not cron.is_running:
                cron.progress_estimated = 0
                continue
            avg_sql = """
                SELECT AVG(duration) AS average_duration
                FROM (
                    SELECT ir_cron_id, duration
                    FROM cv_ir_cron_history
                    WHERE state = 'success' AND ir_cron_id = %s
                    ORDER BY id DESC
                    LIMIT 10
                ) AS recent_success_records;
            """
            self.env.cr.execute(avg_sql, (cron.id,))
            average_duration = self.env.cr.fetchone()
            if not average_duration:
                cron.progress_estimated = 0
                continue
            last_sql = """
                SELECT started_at
                FROM cv_ir_cron_history
                WHERE state is NULL AND id = (
                    SELECT id
                    FROM cv_ir_cron_history
                    WHERE ir_cron_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                );
            """
            self.env.cr.execute(last_sql, (cron.id,))
            started_at = self.env.cr.fetchone()
            if not started_at:
                cron.progress_estimated = 0
                continue
            duration = (fields.Datetime.now() - started_at[0]).total_seconds() / 60
            print('average_duration', average_duration[0])
            if average_duration[0] > 0:
                cron.progress_estimated = min(99, round(duration / average_duration[0] * 100, 2))
            else:
                cron.progress_estimated = 0

    def _compute_history(self):
        for cron in self:
            if not cron.cv_ir_cron_history_ids:
                cron.history = ''
                continue
            res = []
            for history in cron.cv_ir_cron_history_ids[-10:]:
                res.append('{};{}'.format(history.state, history.duration))
            cron.history = ','.join(res)

    def method_direct_trigger(self):
        """ Override the method to setup is_running. """
        history = self.env['cv.ir.cron.history'].create({'ir_cron_id': self.id})
        self.env.cr.commit()
        try:
            return super().method_direct_trigger()
        except Exception as e:
            # TODO roolbakc ?
            history.finish(False, str(e))
            self.env.cr.commit()
            raise e
        finally:
            history.finish(True)

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        """ Override the method to setup is_running. """
        history = self.env['cv.ir.cron.history'].create({'ir_cron_id': job_id})
        self.env.cr.commit()
        super()._callback(cron_name, server_action_id, job_id)
        if history.ended_at is False:
            history.finish(True)

    @api.model
    def _handle_callback_exception(self, cron_name, server_action_id, job_id, job_exception):
        super()._handle_callback_exception(cron_name, server_action_id, job_id, job_exception)
        history = self.env['cv.ir.cron.history'].search([('ir_cron_id', '=', job_id)], limit=1, order='id DESC')
        history.finish(False, str(job_exception))
