# -*- coding: utf-8 -*-

from odoo import models, _, api, exceptions, fields, SUPERUSER_ID
from odoo.addons.point_of_sale.models.pos_config import PosConfig
import logging
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

def update_wrong_surcharge_journal_in_configs(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    pos_configs = env['pos.config'].search([])
    for config in pos_configs:
        logger.warning("Changing wrong surcharge journal in %s[%i] pos config" % (config.name, config.id))
        if config.surcharge_journal_id.company_id != config.company_id:
            # We use SQL just because we want to avoid the exception that is raised 
            # when trying to change a config with a opened session
            if config and config.journal_id:
                cr.execute("""UPDATE pos_config SET surcharge_journal_id = %s WHERE id = %s""", (config.journal_id.id, config.id))


class PosConfigInherit(models.Model):
    """ Adds constraints """
    _inherit = "pos.config"

    is_pos_pr_discount = fields.Boolean(default=False)

    def _default_sale_surcharge(self):
        company = self.company_id or self.env.company
        return self.env['account.journal'].search(
            [('type', '=', 'sale'),
             ('company_id', '=', company.id),
             ('code', '=', 'POSS')], limit=1)

    
    surcharge_journal_id = fields.Many2one(
        'account.journal', string='Surcharge Journal',
        domain=[('type', '=', 'sale')],
        help="Surcharge journal used to post surcharge entries.",
        default=_default_sale_surcharge,
        ondelete='restrict')

    @api.constrains('payment_method_ids')
    def check_if_there_is_discount_payment_method(self):
        for pos_config_id in self:
            discount_payment_method = pos_config_id.payment_method_ids.filtered(lambda payment_method: payment_method.is_pos_pr_discount)
            if discount_payment_method:
                raise exceptions.ValidationError(_("%s is only for aesthetic use") % discount_payment_method.name)

    def _check_surcharge_journal(self):
        self.ensure_one()
        if not self.sudo().surcharge_journal_id:
            raise ValidationError("You should use a surcharge journal")
        
        if self.sudo().surcharge_journal_id.company_id != self.company_id:
            raise ValidationError("You should use a surcharge journal")
    
    def _check_surcharge_and_discount(self):
        self.ensure_one()
        if not self.env['pos.payment.method'].search([('company_id', '=', self.company_id.id)]):
            pass

    def open_session_cb(self):
        self._check_surcharge_journal()
        self._check_surcharge_and_discount()
        return super().open_session_cb()
