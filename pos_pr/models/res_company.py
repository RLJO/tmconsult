# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """ Added some field to easier point of sale javascript """
    _inherit = "res.company"

    pos_pr_surcharge_product_id = fields.Many2one(
        "product.product", string="Surcharge Product",
        default=lambda self: self.env.ref('pos_pr.default_surcharge_product', raise_if_not_found=False))
    pos_pr_discount_product_id = fields.Many2one(
        "product.product", string="Discount Product",
        default=lambda self: self.env.ref('pos_pr.default_discount_product', raise_if_not_found=False))
    pos_pr_surcharge_default_amount = fields.Monetary(default=200)
    pos_pr_discount_default_account_id = fields.Many2one(
        'account.account', string="Default discount account")
