odoo.define('pos_pr.SynchInvoicePayment', function (require) {

    const core = require('web.core');
    const { useListener } = require('web.custom_hooks');
    const chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const _lt = core._lt;
    const { Component } = owl;
    const { useState } = owl;



    class SynchInvoicePayment extends PosComponent {

        previousPartner = {};
        constructor() {

            super(...arguments);
            useListener('synch_invoice_payments', this.synch_invoice_payments);
            const synch = this.env.pos.get('synch');
            this.state = useState({ status: synch.status, msg: synch.pending });
            this.status =  ['connected','connecting','disconnected','warning','error'];

        }

        mounted() {

            this.env.pos.on(
                'change:invoice-synch',
                (pos, synch) => {
                    this.state.status = synch.status;
                    this.state.msg = synch.pending;
                },
                this
            );

            const pendingInvoicePayments = this.env.pos.db.load('pending_invoice_payments', []);
            const pendingSurchargeInvoices = this.env.pos.db.load('pending_surcharge_invoices', []);

            const pendingPaymentsCount = pendingInvoicePayments.length + pendingSurchargeInvoices.length;

            if (pendingPaymentsCount > 0) {
                this.state.status = 'warning'
                this.state.msg = pendingPaymentsCount;
            }
        }

        willUnmount() {
            this.env.pos.on('change:invoice-synch', null, this);
        }


        /**
        * Sych point of sale invoice payments with server
         */
        synch_invoice_payments() {
            this.env.pos.synch_invoive_payment_and_surcharges();
        }


        set_status(status,msg) {
            for(var i = 0; i < this.status.length; i++){
                $(this.el).find('.js_'+this.status[i]).addClass('oe_hidden');
            }
            $(this.el).find('.js_'+status).removeClass('oe_hidden');

            if(msg){
                $(this.el).find('.js_msg').removeClass('oe_hidden').html(msg);
            }else{
                $(this.el).find('.js_msg').addClass('oe_hidden').html('');
            }
        }


    }
    SynchInvoicePayment.template = 'SynchInvoicePayment';
    Registries.Component.add(SynchInvoicePayment);

    return {SynchInvoicePayment};

});
