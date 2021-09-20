from odoo import models, fields, api, _, exceptions
from odoo.addons import account

import logging

logger = logging.getLogger(__name__)


class InvoicePaymentSurcharge(models.Model):
    _name = "pos_pr.invoice.surcharge"

    move_ids = fields.Many2many("account.move")
    surcharge_move_id = fields.Many2one("account.move")
    payment_ids = fields.Many2many("pos_pr.invoice.payment")
    amount = fields.Float("Amount")
    pos_session_id = fields.Many2one("pos.session")
    free_of_surcharge = fields.Float("Free of surcharge", default=0)
    partner_id = fields.Many2one('res.partner', string=_("Customer"), store=True, compute='_compute_partner_id')
    company_id = fields.Many2one('res.company', related='pos_session_id.company_id')

    date = fields.Date()

    @api.depends('move_ids')
    def _compute_partner_id(self):
        for surcharge_id in self:
            partner_id = surcharge_id.mapped('move_ids.partner_id')
            if partner_id:
                partner_id.ensure_one()
                surcharge_id.partner_id = partner_id

    @api.model
    def create(self, vals_list):
        surcharge_ids = super().create(vals_list)
        surcharge_ids.refresh_surcharge_to_invoices()
        return surcharge_ids

    def apply_surcharge(self):
        for surcharge_id in self.filtered('move_ids'):
            if surcharge_id.amount > 0:
                surcharge_move_id = surcharge_id.create_invoice()
                surcharge_move_id.action_post()
                surcharge_id.surcharge_move_id = surcharge_move_id
                

                if surcharge_id.free_of_surcharge:
                    surcharge_id.create_credit_note()

                surcharge_id.apply_payments_to_surcharge()

    def create_credit_note(self):
        self.ensure_one()

        journal = self.surcharge_move_id.journal_id
        surcharge_product = journal.surcharge_product_id
        if not surcharge_product:
            logger.warning(_("using default company surcharge product"))
            surcharge_product = self.company_id.pos_pr_surcharge_product_id
            if not surcharge_product:
                raise exceptions.UserError(
                    _("The journal %s or the current company must have a surcharge product!") % journal.name)
        credit_note_id = self.env["account.move"].create({
            "move_type": "out_refund",
            "partner_id": self.surcharge_move_id.partner_id.id,
            "journal_id": self.surcharge_move_id.journal_id.id,
            "invoice_line_ids": [(0, 0, {
                "product_id": surcharge_product.id,
                "price_unit": self.free_of_surcharge,
                "quantity": 1,
            })],
        })
        credit_note_id.action_post()
        (credit_note_id | self.surcharge_move_id).get_receivable_line_ids().reconcile()

    def create_invoice(self):
        self.ensure_one()
        partner_id = self.move_ids.mapped("partner_id").ensure_one()
        journal = self.pos_session_id.config_id.surcharge_journal_id
        if not journal:
            raise exceptions.UserError(
                _("You need a surcharge journal to proceed"))
        surcharge_product = journal.surcharge_product_id
        if not surcharge_product:
            logger.warning(_("using default company surcharge product"))
            surcharge_product = self.company_id.pos_pr_surcharge_product_id
            if not surcharge_product:
                raise exceptions.UserError(
                    _("The journal %s or the current company must have a surcharge product!") % journal.name)
        surcharge_move_id = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner_id.id,
            "journal_id": journal.id,
            "invoice_line_ids": [(0, 0, {
                "product_id": surcharge_product.id,
                "price_unit": self.amount + self.free_of_surcharge,
                "quantity": 1,
            })],
        })
        return surcharge_move_id

    def apply_payments_to_surcharge(self):
        self.ensure_one()
        self.payment_ids.write({"move_id": self.surcharge_move_id.id})

    def refresh_surcharge_to_invoices(self):
        for surcharge_id in self:
            move_ids = surcharge_id.move_ids.sorted("invoice_date_due")
            move_amount = surcharge_id.amount + surcharge_id.free_of_surcharge
            for move_id in move_ids:
                amount_to_remove = min(move_id.surcharge_amount, move_amount)
                move_id.surcharge_amount -= amount_to_remove
                move_amount -= amount_to_remove
                if move_amount <= 0:
                    break
