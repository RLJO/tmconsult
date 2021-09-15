# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models, SUPERUSER_ID, exceptions

_logger = logging.getLogger(__name__)


class Settings(models.TransientModel):
    """ Setting for surcharge """
    _inherit = "res.config.settings"

    pos_pr_surcharge_product_id = fields.Many2one(
        "product.product", string="Surcharge Product", 
        readonly=False, related='company_id.pos_pr_surcharge_product_id')

    pos_pr_discount_product_id = fields.Many2one(
        "product.product", string="Discount Product", 
        readonly=False, related='company_id.pos_pr_discount_product_id')

    pos_pr_surcharge_default_amount = fields.Monetary(
        readonly=False, related='company_id.pos_pr_surcharge_default_amount')
    pos_pr_discount_default_account_id = fields.Many2one(
        'account.account', string="Default discount account",
        readonly=False, related='company_id.pos_pr_discount_default_account_id')

    def apply_surcharge_amount_to_sale_journals(self):
        self.env['account.journal'].search([('type', '=', 'sale')]).write({
            'surcharge_amount': self.pos_pr_surcharge_default_amount
        })

    def apply_surcharge_product_to_sale_journals(self):
        self.env['account.journal'].search([('type', '=', 'sale')]).write({
            'surcharge_product_id': self.pos_pr_surcharge_product_id.id
        })

    def recompute_surcharge_amounts(self):
        unpaid_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('surcharge_invoice_id', '=', False),
            ('payment_state', '!=', 'paid')])
        unpaid_invoices.recompute_surcharge_amount()
