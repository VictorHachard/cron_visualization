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
    progress_estimated = fields.Char(string='Progress Estimated', compute='_compute_progress_estimated', help='Current progress of the cron (progress;duration)')
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
        """ Check history to know if cron is running. """
        for cron in self:
            cron.is_running = len(cron.cv_ir_cron_history_ids.filtered(lambda h: not h.state)) > 0

    def _compute_progress_estimated(self):
        """ Check history to estimate the progress of the current run. """
        for cron in self:
            if not cron.cv_ir_cron_history_ids or not cron.is_running:
                cron.progress_estimated = False
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
                cron.progress_estimated = False
                continue
            running_sql = """
                SELECT started_at
                FROM cv_ir_cron_history
                WHERE state is NULL AND ir_cron_id = %s
                ORDER BY started_at;
            """
            self.env.cr.execute(running_sql, (cron.id,))
            running_sql = self.env.cr.fetchall()
            if not running_sql:
                cron.progress_estimated = False
                continue
            progress_estimated = []
            for history in running_sql:
                duration = (fields.Datetime.now() - history[0]).total_seconds() / 60
                if average_duration[0] > 0:
                    running_since = (fields.Datetime.now() - history[0]).total_seconds() / 60
                    progress = min(99, round(duration / average_duration[0] * 100, 2))
                    progress_estimated.append(str(progress) + ';' + str(running_since))
            if progress_estimated:
                cron.progress_estimated = ','.join(progress_estimated)
            else:
                cron.progress_estimated = False

    def _compute_history(self):
        for cron in self:
            if not cron.cv_ir_cron_history_ids:
                cron.history = ''
                continue
            res = []
            for history in cron.cv_ir_cron_history_ids[:10]:
                res.insert(0, '{};{}'.format(history.state if history.state else '', history.duration))
            cron.history = ','.join(res)

    def method_direct_trigger(self):
        """ Override the method to setup is_running. """
        history = self.env['cv.ir.cron.history'].create({'ir_cron_id': self.id, 'type': 'manual'})
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
        history = self.env['cv.ir.cron.history'].create({'ir_cron_id': job_id, 'type': 'automatic'})
        self.env.cr.commit()
        super()._callback(cron_name, server_action_id, job_id)
        if history.ended_at is False:
            history.finish(True)

    @api.model
    def _handle_callback_exception(self, cron_name, server_action_id, job_id, job_exception):
        super()._handle_callback_exception(cron_name, server_action_id, job_id, job_exception)
        history = self.env['cv.ir.cron.history'].search([
            ('ir_cron_id', '=', job_id), ('user_id', '=', self.env.user.id), ('type', '=', 'automatic')
        ], limit=1, order='id DESC')
        history.finish(False, str(job_exception))
