# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    possible_referred_partner_ids = fields.Many2many("res.partner", string="Possible deferred partner", compute="_compute_possible_referred_partner_ids", store=True)
    referred_partner_id = fields.Many2one("res.partner", string="Referred partner", domain="[('id', '=', possible_referred_partner_ids)]")

    @api.depends("partner_id")
    def _compute_possible_referred_partner_ids(self):
        for move_id in self:
            move_id.possible_referred_partner_ids = move_id.partner_id.get_recursive_child_ids().sorted("parent_id")

    @api.model
    def create(self, vals_list):
        if "partner_id" in vals_list:
            partner_id = self.env["res.partner"].browse([vals_list["partner_id"]])
            looking_partner = partner_id
            if partner_id.company_type == 'person' and partner_id.parent_id:
                looking_partner = partner_id.parent_id
            partner_invoice_id = looking_partner.get_partner_invoice_id()
            vals_list["partner_id"] = partner_invoice_id.id
            vals_list["referred_partner_id"] = partner_id.id

        return super(AccountMove, self).create(vals_list)
