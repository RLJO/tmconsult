odoo.define('pos_pr.components.buttons', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { posbus } = require('point_of_sale.utils');
    const { useListener } = require('web.custom_hooks');
    const { useState } = owl.hooks;
    const { Component } = owl;

    class PaymentRegisterButton extends PosComponent {
        onClick() {
            if (this.props.isTicketScreenShown) {
                posbus.trigger('ticket-button-clicked');
            } else {
                this.showScreen('InvoiceScreen');
            }
        }
        willPatch() {
            posbus.off('order-deleted', this);
        }
        patched() {
            posbus.on('order-deleted', this, this.render);
        }
        mounted() {
            posbus.on('order-deleted', this, this.render);
        }
        willUnmount() {
            posbus.off('order-deleted', this);
        }
        get count() {
            if (this.env.pos) {
                return this.env.pos.get_order_list().length;
            } else {
                return 0;
            }
        }

    }

    class InvoicePaymentRow extends PosComponent {

        cancel() {
            this.trigger('cancel_payment', this.props.payment);
        }
    }

    class InvoicePaymentGroupRow extends PosComponent {
        static components = {InvoicePaymentRow};
        constructor(parent, props) {
            super(...arguments);
            this.state = useState({
                paymentGroup: props.paymentGroup || {}
            })
        }

        print() {
            const paymentGroupCloned = _.clone(this.props.paymentGroup);
            this.trigger('print_payment_group', paymentGroupCloned);
        }

        get arePaymentCancelled() {
            return _.reduce(this.props.paymentGroup.invoice_payment_ids, (memo, payment) => memo & payment.state === 'cancelled', 1);
        }

        onCancelPayment(event) {
            this.trigger('cancel_payments', [event.detail]);
        }

        onCancelAllPayments() {
            this.trigger('cancel_payments', this.props.paymentGroup.invoice_payment_ids);
        }
    }

    class InvoicePaymentListScreen extends PosComponent {
        static components = {InvoicePaymentGroupRow};
         constructor() {

            super(...arguments);
            useListener('cancel-screen', this._go_to_back_screen);
            this.state = useState({
                 partner: {},
                paymentGroupList: [],
            });
            this.state.partner = this.env.pos.get_client();
            this.updateGroupList();
        }


        _go_to_back_screen () {
            this.showScreen('InvoiceScreen');
        }

        updateGroupList() {
            if (this.state.partner) {
                this.state.paymentGroupList = _.filter(this.env.pos.db.invoice_payment_groups, paymentGroup => paymentGroup.partner_id.id == this.state.partner.id);
            } else {
                this.state.paymentGroupList = this.env.pos.db.invoice_payment_groups;
            }
        }

         onPrintPaymentGroup(event) {
            const paymentGroup = event.detail;
            this.showScreen('InvoicePaymentReceiptScreen', {
                    paymentGroup,
                    invoiceAddress: this.env.pos.db.partner_by_id[paymentGroup.partner_id.id],
                    changeAmount: 0,
            });
        }

        async onCancelPayment(event) {
            const payments = event.detail;
            const paymentIds = _.map(payments, payment => payment.id)
            await this.env.pos.cancel_invoice_payment_ids(paymentIds)
            _.each(payments, payment => {
                const invoice = this.env.pos.db.due_invoices_by_id[payment.move_id.id];
                invoice.amount_residual += payment.payment_amount + payment.discount_amount
//                this.env.pos.gui.screen_instances
//                    .invoice_payment_register_screen
//                    .invoicePaymentRegisterScreen.render()
                payment.state = 'cancelled';
            });
        }

    }





    InvoicePaymentListScreen.template = 'InvoicePaymentListScreen';
    Registries.Component.add(InvoicePaymentListScreen);

    PaymentRegisterButton.template = 'PaymentRegisterButton';
    Registries.Component.add(PaymentRegisterButton);
    return PaymentRegisterButton;
});
