# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    child_company_ids = fields.Many2many("res.partner", compute='_compute_child_company_ids')
    possible_partner_invoice_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="invoice_possible_partner_invoices",
        column1="partner_id",
        column2="possible_partner_invoice_id",
        string="Possible partner invoices",
        compute='_compute_possible_partner_invoice_ids',
        store=True)
    partner_invoice_id = fields.Many2one("res.partner", string="Invoice address", domain="[('id', 'in', possible_partner_invoice_ids)]")

    def get_recursive_child_ids(self):
        """ It return all their children and their child's' children """
        child_ids = self.mapped("child_ids")
        child_ids_of_childs = child_ids.mapped("child_ids")
        if child_ids_of_childs:
            child_ids += child_ids.get_recursive_child_ids()

        return child_ids

    def get_partner_invoice_id(self):
        """ This method will return the real invoice id for the current partner,
            It will find until find one that doesn't have invoice address """
        self.ensure_one()
        if not self.partner_invoice_id:
            return self
        elif self.partner_invoice_id.company_type == 'person' or self.partner_invoice_id == self:
            return self.partner_invoice_id
        else:
            return self.partner_invoice_id.get_partner_invoice_id()

    @api.depends("child_ids")
    def _compute_child_company_ids(self):
        for partner_id in self:
            partner_id.child_company_ids = partner_id.child_ids.filtered(lambda child_id: child_id.company_type == 'company')

    @api.depends("child_ids", "parent_id")
    def _compute_possible_partner_invoice_ids(self):
        for partner_id in self:
            # This create a empty "list" of partner, that way we can use += operator.
            partner_invoice_ids = self.env["res.partner"]

            # We will use this to browse throught parents
            lookin_parent_id = partner_id.parent_id
            while lookin_parent_id:
                partner_invoice_ids += lookin_parent_id
                lookin_parent_id = lookin_parent_id.parent_id

            partner_invoice_ids += partner_id

            # If we allow also choosing companies, that will create a recursive behaviour, even a bucle... so...
            partner_invoice_ids += partner_id.child_ids.filtered(lambda child_id: child_id.company_type == 'person')

            partner_id.possible_partner_invoice_ids = partner_invoice_ids
