odoo.define('pos_pr.screens.invoice_payment_receipt', function (require) {

    const screens = require('point_of_sale.PaymentScreen');
    const core = require('web.core');
    const { useListener } = require('web.custom_hooks');
    const gui = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');

    const QWeb = core.qweb;
    const _t = core._t;
    const { Component } = owl;
    const reports = require('pos_pr.components.reports');
    const Registries = require('point_of_sale.Registries');


    class InvoicePaymentReceiptScreen extends PosComponent {

        constructor() {
            super(...arguments);
            this.paymentGroup = this.props.paymentGroup;
            this.invoiceAddress = this.props.invoiceAddress;
        }

        mounted() {
            var payment_data = this.paymentData()
            var receipt_data = {
                data: payment_data,
                copy: false
            }
            var receipt = this.renderPaymentReceipt(receipt_data);
            $(this.el).find('#pos_payment_receipt_container').html(receipt);

            receipt_data.copy = true
            var receipt_copy = this.renderPaymentReceipt(receipt_data)
            $(this.el).find('#pos_payment_receipt_container_copy').html(receipt_copy);

            setTimeout(async () => await this.handleAutoPrint(), 0);
        }

        paymentData() {

            var data = {};
            data['invoices'] = this._compute_invoice();
            data['discount_total'] = this._compute_discount_total();
            data['payments_by_invoice'] = this._compute_payments_by_invoice();
            data['payment_methods'] = this._compute_payment_methods();
            data['payment_totals_by_method'] = this._compute_payment_totals_by_method();

            return data

        }

        renderPaymentReceipt(add_params){
            var params = {
                paymentGroup: this.paymentGroup,
                env: this.env,
                customer: this.invoiceAddress,
            }

            var render_params = Object.assign(params,add_params)
            var receipt = this.env.qweb.renderToString('InvoicePaymentReceipt', render_params);

            return receipt

        }

        orderDone() {
                this.showScreen('ProductScreen');
        }

        async printReceipt() {
            var payment_data = this.paymentData()
            var receipt_data = {
                data: payment_data,
                copy: false
            }

            var receipt = this.renderPaymentReceipt(receipt_data);

            if (this.env.pos.proxy.printer) {
                await this._printIoT(receipt);
            } else {
                await this._printWeb(receipt);
            }
        }

        async _printIoT(receipt) {
            const printResult = await this.env.pos.proxy.printer.print_receipt(receipt);
            if (!printResult.successful) {
                await this.showPopup('ErrorPopup', {
                    title: printResult.message.title,
                    body: printResult.message.body,
                });
            }
        }

        async _printWeb(receipt) {
            try {
                $(this.el).find('#pos_payment_receipt_container').html(receipt);
                const isPrinted = document.execCommand('print', false, null);
                if (!isPrinted) window.print();
            } catch (err) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Printing is not supported on some browsers'),
                    body: this.env._t(
                        'Printing is not supported on some browsers due to no default printing protocol ' +
                            'is available. It is possible to print your tickets by making use of an IoT Box.'
                    ),
                });
            }
        }

        get ChangeValue (){
            return this.paymentGroup.payment_change;
        }

        _compute_invoice () {
            const invoices = [];
            _.each(this.paymentGroup.invoice_payment_ids, (invoicePayment) => {
            if (!invoices.some(invoice => invoice.id === invoicePayment.move_id.id)) {
                if (!invoicePayment.move_id.amount_total) {
                    invoicePayment.move_id = this.env.pos.db.due_invoices_by_id[invoicePayment.move_id.id]
                }
                invoices.push(invoicePayment.move_id);
            }
            });
            return invoices;
        }

        _compute_discount_total (){
            let discountTotal = 0;
            _.each(this.paymentGroup.invoice_payment_ids, function (invoicePayment) {
                if (invoicePayment.state !== 'cancelled') {
                    discountTotal += invoicePayment.discount_amount || 0;
                }
            });
            return discountTotal;
        }

        _compute_payments_by_invoice () {
            const paymentsByInvoice = {};
            _.each(this.paymentGroup.invoice_payment_ids, invoicePayment => {
                if (invoicePayment.payment_method_id.id !== this.env.pos.db.discount_payment_method.id) {
                    const invoicePaymentInvoice = invoicePayment.move_id;
                    if (!paymentsByInvoice[invoicePaymentInvoice.id]) {
                        paymentsByInvoice[invoicePaymentInvoice.id] = [];
                    }
                    console.log("invoicePayment"+ invoicePayment)
                    paymentsByInvoice[invoicePaymentInvoice.id].push(invoicePayment);
                }
            });
            return paymentsByInvoice;
        }

        _compute_payment_methods () {
            const paymentMethods = [];
            _.each(this.paymentGroup.invoice_payment_ids, invoicePayment => {
                if (invoicePayment.payment_method_id.id !== this.env.pos.db.discount_payment_method.id
                    && !paymentMethods.some(paymentMethod => paymentMethod.id === invoicePayment.payment_method_id.id)) {
                    paymentMethods.push(invoicePayment.payment_method_id);
                }
            });
            return paymentMethods;
        }

        _compute_payment_totals_by_method () {
            const paymentTotalsByMethod = {};
            _.each(this.paymentGroup.invoice_payment_ids, function (invoicePayment) {
                const paymentMethod = invoicePayment.payment_method_id;
                if (!paymentTotalsByMethod[paymentMethod.id]) {
                    paymentTotalsByMethod[paymentMethod.id] = 0;
                }
                if (invoicePayment.state !== 'cancelled') {
                    paymentTotalsByMethod[paymentMethod.id] += invoicePayment.payment_amount;
                }
            });
            return paymentTotalsByMethod;
        }

        async handleAutoPrint() {
            if (this._shouldAutoPrint()) {
                await this.printReceipt();
                if (this.currentOrder._printed && this._shouldCloseImmediately()) {
                    this.orderDone();
                }
            }
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

         _shouldAutoPrint() {
            return this.env.pos.config.iface_print_auto && !this.currentOrder._printed;
        }

        _shouldCloseImmediately() {
            var invoiced_finalized = this.currentOrder.is_to_invoice() ? this.currentOrder.finalized : true;
            return this.env.pos.proxy.printer && this.env.pos.config.iface_print_skip_screen && invoiced_finalized;
        }

    }

    InvoicePaymentReceiptScreen.template = 'InvoicePaymentReceiptScreen';
    InvoicePaymentReceiptScreen.hideOrderSelector = true;
    Registries.Component.add(InvoicePaymentReceiptScreen);

    return {InvoicePaymentReceiptScreen};


});
