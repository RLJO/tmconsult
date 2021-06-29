# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
import requests
import json
from odoo.exceptions import Warning
from datetime import date
from odoo.http import request
from datetime import timezone, timedelta
import datetime
from dateutil.relativedelta import relativedelta


_logger = logging.getLogger(__name__)


class accountInvoice(models.Model):
    _inherit = 'account.move'

    def _payment_remainder_send_message(self):
        account_invoice_ids = self.env['account.move'].search([('state', 'in', ['draft', 'posted']), ('invoice_date_due', '<', datetime.datetime.now())])
        Param = self.env['res.config.settings'].sudo().get_values()

        for account_invoice_id in account_invoice_ids:
            if account_invoice_id.partner_id.country_id.phone_code and account_invoice_id.partner_id.mobile:
                msg = "Hello " + account_invoice_id.partner_id.name + "\nYour invoice"
                if account_invoice_id.state == 'draft':
                    msg += " *" + "draft" + "* "
                else:
                    msg += " *" + account_invoice_id.name + "* "
                msg += "is pending"
                msg += "\nTotal Amount: " + self.env['whatsapp.msg'].format_amount(account_invoice_id.amount_total, account_invoice_id.currency_id) + " & Due Amount: " + str(
                    round(account_invoice_id.partner_id.credit, 2)) + "."

                whatsapp_msg_number = account_invoice_id.partner_id.mobile
                whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "")
                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(account_invoice_id.partner_id.country_id.phone_code), "")
                url = Param.get('whatsapp_endpoint') + '/sendMessage?token=' + Param.get('whatsapp_token')
                headers = {
                    "Content-Type": "application/json",
                }
                a = "+" + str(account_invoice_id.partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code
                tmp_dict = {
                    "phone": a,
                    "body": msg
                }
                response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                if response.status_code == 201 or response.status_code == 200:
                    _logger.info("\nSend Message successfully")

                    # if response.status_code == 201 or response.status_code == 200:
                    #     _logger.info("\nSend Message successfully")

                    mail_message_obj = self.env['mail.message']
                    mail_message_id = mail_message_obj.sudo().create({
                        'res_id': account_invoice_id.id,
                        'model': 'account.move',
                        'body': msg,
                    })

    # def _payment_remainder_send_message(self):
    #     print("\n\n\n\nIn _payment_remainder_send_message")
    #     account_invoice_ids = self.env['account.move'].search([('state', 'in', ['draft','posted']),('invoice_date_due', '<=', datetime.datetime.now())])
    #     Param = self.env['res.config.settings'].sudo().get_values()
    #     print("\naccount_invoice_ids:::",account_invoice_ids)
    #
    #     for account_invoice_id in account_invoice_ids:
    #         print("\naccount_invoice_id---------: ",account_invoice_id)
    #             print("\nIn if payment remainder interval")
    #             remainder_date = datetime.datetime.strptime(Param.get('payment_remainder_date'), '%Y-%m-%d').date()
    #             print("\n\ndate.today(): ",date.today(),"type: ",type(date.today()),"\nremainder_date: ",remainder_date,"\ttype: ",type(remainder_date))
    #             if date.today() >= remainder_date:
    #                 print("\n\nIn if today date & payment remainder date same")
    #                 if account_invoice_id.partner_id.country_id.phone_code and account_invoice_id.partner_id.mobile:
    #                     msg = "Hello "+account_invoice_id.partner_id.name+ "\nYour invoice"
    #                     if account_invoice_id.state == 'draft':
    #                         msg += " *" + "draft" + "* "
    #                     else:
    #                         msg += " *" + account_invoice_id.name + "* "
    #                     msg += "is pending"
    #                     msg += "\nTotal Amount: " + self.env['whatsapp.msg'].format_amount(account_invoice_id.amount_total, account_invoice_id.currency_id) + " & Due Amount: " + str(
    #                         round(account_invoice_id.partner_id.total_due, 2)) + "."
    #
    #                     whatsapp_msg_number = account_invoice_id.partner_id.mobile
    #                     whatsapp_msg_number_without_space = whatsapp_msg_number.replace(" ", "")
    #                     whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(account_invoice_id.partner_id.country_id.phone_code), "")
    #                     url = Param.get('whatsapp_endpoint') + '/sendMessage?token=' + Param.get('whatsapp_token')
    #                     headers = {
    #                         "Content-Type": "application/json",
    #                     }
    #                     a= "+" + str(account_invoice_id.partner_id.country_id.phone_code) + "" + whatsapp_msg_number_without_code
    #                     tmp_dict = {
    #                         "phone": a,
    #                         "body": msg
    #                     }
    #                     response = requests.post(url, json.dumps(tmp_dict), headers=headers)
    #                     if response.status_code == 201 or response.status_code == 200:
    #                         _logger.info("\nSend Message successfully")
    #                         print("\nres_config_update_date::::",res_config_update_date)
    #                         self.env['ir.config_parameter'].sudo().set_param('pragmatic_odoo_whatsapp_integration.payment_remainder_date', res_config_update_date )
    #
    #                         mail_message_obj = self.env['mail.message']
    #                         mail_message_id = mail_message_obj.sudo().create({
    #                             'res_id': account_invoice_id.id,
    #                             'model': 'account.move',
    #                             'body': msg,
    #                         })


