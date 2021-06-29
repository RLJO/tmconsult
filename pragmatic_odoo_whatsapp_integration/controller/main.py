import requests

from odoo import http, _, models, api
import logging
import json
import base64
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request

import phonenumbers
import datetime
import time
import pytz
from odoo.tools import ustr
from PIL import Image
import requests
from io import BytesIO
import base64




_logger = logging.getLogger(__name__)


class SendMessage(http.Controller):
    _name = 'send.message.controller'

    def format_amount(self, amount, currency):
        fmt = "%.{0}f".format(currency.decimal_places)
        lang = http.request.env['res.lang']._lang_get(http.request.env.context.get('lang') or 'en_US')

        formatted_amount = lang.format(fmt, currency.round(amount), grouping=True, monetary=True)\
            .replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = u''
        if currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=currency.symbol or '')

        return u'{pre}{0}{post}'.format(formatted_amount, pre=pre, post=post)

    @http.route('/whatsapp/send/message', type='http', auth='public', website=True, csrf=False)
    def sale_order_paid_status(self, **post):
        # ref_name = post.get('order')
        # ref_id = 'Shop/' + ref_name[-4:]
        pos_order = http.request.env['pos.order'].sudo().search([('pos_reference', '=', post.get('order'))])
        if pos_order.partner_id:
            if pos_order.partner_id.mobile and pos_order.partner_id.country_id.phone_code:
                doc_name = 'POS'
                # res_user_id = self.env['res.users'].search([('id', '=', self.env.user.id)])
                msg = "Hello " + pos_order.partner_id.name
                if pos_order.partner_id.parent_id:
                    msg += "(" + pos_order.partner_id.parent_id.name + ")"
                msg += "\n\nYour "
                msg += doc_name + " *" + pos_order.name + "* "

                msg += " with Total Amount " + self.format_amount(pos_order.amount_total, pos_order.pricelist_id.currency_id) + "."
                msg += "\n\nFollowing is your order details."
                for line_id in pos_order.lines:
                    msg += "\n\n*Product:* " + line_id.product_id.name + "\n*Qty:* " + str(line_id.qty) + " " + "\n*Unit Price:* " + str(
                        line_id.price_unit) + "\n*Subtotal:* " + str(line_id.price_subtotal)
                    msg += "\n------------------"

                Param = http.request.env['res.config.settings'].sudo().get_values()
                url = Param.get('whatsapp_endpoint') + '/sendMessage?token=' + Param.get('whatsapp_token')
                headers = {
                    "Content-Type": "application/json",
                }
                whatsapp_number =  pos_order.partner_id.mobile
                whatsapp_msg_number_without_space = whatsapp_number.replace(" ", "")
                whatsapp_msg_number_without_code = whatsapp_msg_number_without_space.replace('+' + str(pos_order.partner_id.country_id.phone_code), "")
                tmp_dict = {
                    "phone": "+" + str(pos_order.partner_id.country_id.phone_code) + "" +whatsapp_msg_number_without_code,
                    "body": msg}
                response = requests.post(url, json.dumps(tmp_dict), headers=headers)

                if response.status_code == 201 or response.status_code == 200:
                    _logger.info("\nSend Message successfully")
                    return json.dumps({'msg_response': response.status_code})

class AuthSignupHomeDerived(AuthSignupHome):

    def get_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""
        get_param = request.env['ir.config_parameter'].sudo().get_param
        countries = request.env['res.country'].sudo().search([])
        return {
            'signup_enabled': request.env['res.users']._get_signup_invitation_scope() == 'b2c',
            'reset_password_enabled': get_param('auth_signup.reset_password') == 'True',
            'countries': countries
        }

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'mobile', 'country_id') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()



class Whatsapp(http.Controller):

    def convert_epoch_to_unix_timestamp(self, msg_time):
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg_time))
        date_time_obj = datetime.datetime.strptime(formatted_time, '%Y-%m-%d %H:%M:%S')
        dt = False
        if date_time_obj:
            timezone = pytz.timezone(request.env['res.users'].
                                     sudo().browse([int(2)]).tz or 'UTC')
        dt = pytz.UTC.localize(date_time_obj)
        dt = dt.astimezone(timezone)
        dt = ustr(dt).split('+')[0]
        return date_time_obj

    @http.route(['/whatsapp/responce/message'], type='json', auth='public')
    def whatsapp_responce(self):
        data = json.loads(request.httprequest.data)
        _request = data
        if 'messages' in data and data['messages']:
            msg_list=[]
            msg_dict={}
            res_partner_obj = request.env['res.partner']
            whatapp_msg = request.env['whatsapp.messages']
            for msg in data['messages']:
                if 'chatId' in msg and msg['chatId']:
                    res_partner_obj = res_partner_obj.sudo().search([('chatId','=',msg['chatId'])])
                    if res_partner_obj:
                        if msg['type'] == 'image' and res_partner_obj:
                            url = msg['body']
                            data = base64.b64encode(requests.get(url.strip()).content).replace(b'\n', b'')
                            msg_dict = {
                                'name': msg['body'],
                                'message_body': msg['caption'],
                                'message_id': msg['id'],
                                'fromMe': msg['fromMe'],
                                'to': msg['chatName'] if msg['fromMe']==True else 'To Me',
                                'chatId': msg['chatId'],
                                'type': msg['type'],
                                'senderName': msg['senderName'],
                                'chatName': msg['chatName'],
                                'author': msg['author'],
                                'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                'partner_id': res_partner_obj.id,
                                'state': 'sent' if msg['fromMe'] == True else 'recived',
                                'msg_image':data
                            }
                        if res_partner_obj and msg['type'] == 'chat':
                            msg_dict = {
                                'name':msg['body'],
                                'message_body':msg['body'],
                                'message_id':msg['id'],
                                'fromMe':msg['fromMe'],
                                'to':msg['chatName'] if msg['fromMe']==True else 'To Me',
                                'chatId':msg['chatId'],
                                'type':msg['type'],
                                'senderName':msg['senderName'],
                                'chatName':msg['chatName'],
                                'author':msg['author'],
                                'time':self.convert_epoch_to_unix_timestamp(msg['time']),
                                'partner_id':res_partner_obj.id,
                                'state':'sent' if msg['fromMe'] == True else 'recived',
                            }

                    else:
                        chat_id = msg['chatId']
                        chatid_split = chat_id.split('@')
                        mobile = '+'+chatid_split[0]
                        mobile_coutry_code = phonenumbers.parse(mobile,None)
                        mobile_number = mobile_coutry_code.national_number
                        res_partner_obj = res_partner_obj.sudo().search([('mobile','=',mobile_number)])
                        if not res_partner_obj:
                            mobile_coutry_code = phonenumbers.parse(mobile, None)
                            mobile_number = mobile_coutry_code.national_number
                            country_code = mobile_coutry_code.country_code
                            mobile = '+'+str(country_code)+' '+str(mobile_number)
                            res_partner_obj = res_partner_obj.sudo().search([('mobile', '=', mobile)])
                        if not res_partner_obj:
                            mobile_coutry_code = phonenumbers.parse(mobile, None)
                            mobile_number = mobile_coutry_code.national_number
                            country_code = mobile_coutry_code.country_code
                            mobile = '+' + str(country_code) + ' ' + str(int(str(mobile_number)[:5]))+' '+str(int(str(mobile_number)[-5:]))
                            res_partner_obj = res_partner_obj.sudo().search([('mobile', '=', mobile)])
                        if res_partner_obj:
                            res_partner_obj.chatId = chat_id
                            msg_dict = {
                                'name': msg['body'],
                                'message_body': msg['body'],
                                'message_id': msg['id'],
                                'fromMe': msg['fromMe'],
                                'to': msg['chatName'] if msg['fromMe']==True else 'To Me',
                                'chatId': msg['chatId'],
                                'type': msg['type'],
                                'senderName': msg['senderName'],
                                'chatName': msg['chatName'],
                                'author': msg['author'],
                                'time': self.convert_epoch_to_unix_timestamp(msg['time']),
                                'partner_id': res_partner_obj.id,
                                'state': 'sent' if msg['fromMe'] == True else 'recived'
                            }
                    msg_list.append(msg_dict)
            for msg in msg_list:
                whatapp_msg.sudo().create(msg)

        return 'OK'

