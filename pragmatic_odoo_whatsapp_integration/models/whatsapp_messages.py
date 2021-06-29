import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class WhatsappMessages(models.Model):
    _name = 'whatsapp.messages'
    name=fields.Char('Name')
    message_body = fields.Char('Message')
    message_id = fields.Text('Message Id')
    fromMe = fields.Boolean('Form Me')
    from_contact = fields.Char('To')
    to = fields.Char('To')
    chatId = fields.Char('Chat ID')
    type = fields.Char('Type')
    msg_image = fields.Binary('Image')
    senderName = fields.Char('Sender Name')
    chatName = fields.Char('Chat Name')
    author = fields.Char('Author')
    time = fields.Datetime('Date and time')
    partner_id = fields.Many2one('res.partner','Partner')
    state= fields.Selection([('sent', 'Sent'),('recived', 'Recived')])


