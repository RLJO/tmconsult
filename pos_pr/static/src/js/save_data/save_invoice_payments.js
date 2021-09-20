odoo.define("pos_pr.save_invoice_payments", function (require) {

    const { Gui } = require('point_of_sale.Gui');
    const models = require("point_of_sale.models");
    const rpc = require('web.rpc');

    const core = require("web.core");
    const _t = core._t;

    const PosModelSuper = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            PosModelSuper.prototype.initialize.apply(this, arguments);
            const self = this;
            this.ready.then(function () {
                const pendingInvoicePayments = self.db.load('pending_invoice_payments', []);
                const pendingSurchargeInvoices = self.db.load('pending_surcharge_invoices', []);

                self.db.save('pending_invoice_payments', pendingInvoicePayments);
                self.db.save('pending_surcharge_invoices', pendingSurchargeInvoices);
            });

            this.set({
                'invoice-synch': { status:'connected', pending:0 },

            });
        },

        send_surcharge: function (surchargesAsJson) {
            return new Promise((resolve, reject) => {
                if (surchargesAsJson && surchargesAsJson.length) {

                    rpc.query({
                        model: "pos_pr.invoice.surcharge",
                        method: "create",
                        args: [surchargesAsJson]
                    }, {}).then(function (data) {
                        resolve(data);
                    }).catch(function (error) {
                        reject(error);
                    });
                } else {
                    resolve();
                }
            });
        },

        send_invoice_payment_groups: async function (invoicePaymentsJson) {
            if (invoicePaymentsJson && invoicePaymentsJson.length) {
                return await rpc.query({
                    model: "pos_pr.payment_group",
                    method: "create",
                    args: [invoicePaymentsJson],
                }, {})
            }
        },

        async synch_invoive_payment_and_surcharges(invoicePaymentGroup, surcharges) {
            invoicePaymentGroup = invoicePaymentGroup || {};
            surcharges = surcharges || [];

            let newSurchargesJSON = [];
            let newInvoicePaymentsJSON = [];

            if (invoicePaymentGroup && invoicePaymentGroup.export_as_json) {
                const invoiceJSON = invoicePaymentGroup.export_as_json();
                invoiceJSON.invoice_payment_ids = invoiceJSON.invoice_payment_ids.map(payment => [0, 0, payment]);
                newInvoicePaymentsJSON.push(invoiceJSON);
            }

            if (surcharges && surcharges.length > 0) {
                _.each(surcharges, function (surcharge) {
                    const surchargeJSON = surcharge.export_as_json();
                    surchargeJSON.payment_ids = surchargeJSON.payment_ids.map(payment => [0, 0, payment]);
                    surchargeJSON.move_ids = surchargeJSON.move_ids.map(move => move.id);
                    newSurchargesJSON.push(surchargeJSON);
                });
            }

            const pendingInvoicePayments = this.db.load('pending_invoice_payments', []);
            const pendingSurchargeInvoices = this.db.load('pending_surcharge_invoices', []);

            const surchargesToSynch = pendingSurchargeInvoices.concat(newSurchargesJSON);
            const invoicePaymentsToSynch = pendingInvoicePayments.concat(newInvoicePaymentsJSON);

            this.db.save('pending_invoice_payments', []);
            this.db.save('pending_surcharge_invoices', []);
            this.set_synch('connecting', surchargesToSynch.length + + invoicePaymentsToSynch.length);

            if (surchargesToSynch.length > 0 || invoicePaymentsToSynch.length > 0) {
                try {
                    const data = await Promise.all([this.send_surcharge(surchargesToSynch),
                                                           this.send_invoice_payment_groups(invoicePaymentsToSynch)]);
                    const paymentGroupIds = data[1];

                    // Now we get every id from odoo
                    if (paymentGroupIds) {
                        const invoicePaymentIds = await rpc.query({
                            model: "pos_pr.invoice.payment",
                            method: "search_read",
                            domain: [['payment_group_id', '=', paymentGroupIds[0]]],
                            fields: [
                                'id',
                                'name',
                            ],
                        }, {})
                        _.each(invoicePaymentIds, invoicePaymentId => {
                            // If we are synching, the function arguments are empty, so...
                            // We need to find in all the payment groups for the payment
                            for (pGroup of this.db.invoice_payment_groups) {
                                const payment = _.find(pGroup.invoice_payment_ids, payment => payment.name === invoicePaymentId.name);
                                if (payment) {
                                    payment.id = invoicePaymentId.id;
                                    break;
                                }
                            }
                        })
                    }

                    this.set_synch('connected', 0);
                    Gui.showPopup('ConfirmPopup', {
                        title: _t('Changes saved correctly'),
                        body: _t('In order to apply the changes in backend the Point of sale needs to be closed and validated'),
                    });
                    return data;
                } catch (reason) {
                    const error = reason.message;
                    if (error.code === 200) {
                        // Business Logic Error, not a connection problem
                        //if warning do not need to display traceback!!
                        if (error.data.exception_type === 'warning') {
                            delete error.data.debug;
                        }

                        // Hide error if already shown before ...
                        this.gui.show_popup('error-traceback', {
                            'title': error.data.message,
                            'body': error.data.debug
                        });
                    }
                    this.set_synch('disconnected', surchargesToSynch.length + invoicePaymentsToSynch.length);

                    this.db.save('pending_invoice_payments', invoicePaymentsToSynch);
                    this.db.save('pending_surcharge_invoices', surchargesToSynch);
                    throw error;
                }
            } else {
                  this.set_synch('connected', 0);
            }
        },

        cancel_invoice_payment_ids(invoicePaymentIds) {
            return rpc.query({
                model: "pos_pr.invoice.payment",
                method: "write",
                args: [invoicePaymentIds, {state: 'cancelled'}],
            }, {});
        },

        set_synch: function(status, pending) {
            if (['connected', 'connecting', 'error', 'disconnected'].indexOf(status) === -1) {
                console.error(status, ' is not a known connection state.');
            }
             const pendingInvoicePayments = this.env.pos.db.load('pending_invoice_payments', []);
                const pendingSurchargeInvoices = this.env.pos.db.load('pending_surcharge_invoices', []);

                const pendingPaymentsCount = pendingInvoicePayments.length + pendingSurchargeInvoices.length;

                if (pendingPaymentsCount > 0) {
                    status = 'warning'
                    pending = pendingPaymentsCount;
                }

            this.set('invoice-synch', { status, pending });
        },


    });

});
