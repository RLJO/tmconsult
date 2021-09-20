# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    """ Setting for surcharge """
    _inherit = "account.journal"

    surcharge_product_id = fields.Many2one(
        "product.product", string="Surcharge Product",
        default=lambda self: self.env.company.pos_pr_surcharge_product_id)

    surcharge_amount = fields.Monetary(
        default=lambda self: self.env.company.pos_pr_surcharge_default_amount)
