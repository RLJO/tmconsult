odoo.define('pos_pr.components.reports', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const core = require('web.core');
    const gui = require('point_of_sale.Gui');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const { Component } = owl;

    const QWeb = core.qweb;
    const _t = core._t;


    class SurchargePaymentReceipt extends IndependentToOrderScreen {
        constructor() {
            super(...arguments);
            this.surcharge = this.props.surcharge || {};
            this.customer = this.props.customer || {};
            this.copy = !!this.props.copy;

            // Default attributes
            this.company = this.env.pos.company;
            this.invoices = this.surcharge.move_ids || [];
        }

    }

    SurchargePaymentReceipt.template = 'SurchargePaymentReceipt';
    Registries.Component.add(SurchargePaymentReceipt);

    return {SurchargePaymentReceipt};



    class InvoicePaymentReceipt extends Component {
//        template: 'InvoicePaymentReceipt',

        /**
         * This will be used to render payments receipts in POS.
         * @param {Object} parent The current parent
         * @param {Object} options Widget's options
         * @param {PaymentGroup} options.paymentGroup The payment group to rendered
         * @param {Object} options.customer The customer to rendered
         * @param {Boolean=false} options.copy The customer to rendered
         */

         constructor(parent, props) {

            super(...arguments);
            // Attributes by options
            this.paymentGroup = props.paymentGroup || {};
            this.customer = props.customer || {};
            this.copy = !!props.copy;

            //Default attributes
            this.company = this.pos.company;
        }


    }

    InvoicePaymentReceipt.template = 'InvoicePaymentReceipt';
    Registries.Component.add(InvoicePaymentReceipt);

    return {InvoicePaymentReceipt};


});
