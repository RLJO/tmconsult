odoo.define('pos_pr.screens.surcharge_payment_receipt', function (require) {

    const screens = require('point_of_sale.PaymentScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const core = require('web.core');
    const gui = require('point_of_sale.Gui');

    const { Component } = owl;
    const QWeb = core.qweb;
    const _t = core._t;
    const reports = require('pos_pr.components.reports');
    const Registries = require('point_of_sale.Registries');

    class SurchargePaymentReceiptScreen extends PosComponent {

        constructor() {
            super(...arguments);
            this.surcharge = this.props.surcharge;
            this.invoiceAddress = this.props.invoiceAddress;
            this.copy = !!this.props.copy;

            // Default attributes
            this.company = this.env.pos.company;
            this.invoices = this.surcharge.move_ids || [];
        }


        orderDone() {
                this.showScreen('ProductScreen');
        }

        mounted() {
            var receipt = this.env.qweb.renderToString('SurchargePaymentReceipt', {
                surcharge: this.surcharge,
                env: this.env,
                customer: this.invoiceAddress || this.pos.get_client(),
                invoices: this.invoices,
            });

            $(this.el).find('#pos_payment_receipt_container').html(receipt);

            setTimeout(async () => await this.handleAutoPrint(), 0);
        }

        async printReceipt() {
           var receipt = this.env.qweb.renderToString('SurchargePaymentReceipt', {
                surcharge: this.surcharge,
                env: this.env,
                customer: this.invoiceAddress || this.pos.get_client(),
                invoices: this.invoices,
            });

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

    SurchargePaymentReceiptScreen.template = 'SurchargePaymentReceiptScreen';
    SurchargePaymentReceiptScreen.hideOrderSelector = true;
    Registries.Component.add(SurchargePaymentReceiptScreen);

    return {SurchargePaymentReceiptScreen};

});
