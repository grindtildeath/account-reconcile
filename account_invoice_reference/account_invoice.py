# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    def _ref_from_invoice(self, cr, uid, invoice, context=None):
        if invoice.type in ('out_invoice', 'out_refund'):
            return invoice.origin
        elif invoice.type in ('in_invoice', 'in_refund'):
            return invoice.supplier_invoice_number

    def action_number(self, cr, uid, ids, context=None):
        # force the number of the invoice to be updated for the
        # subsequent browse
        self.write(cr, uid, ids, {})

        for invoice in self.browse(cr, uid, ids, context=context):
            ref = self._ref_from_invoice(cr, uid, invoice, context=context)
            if not ref:
                ref = invoice.number
            move_id = invoice.move_id.id if invoice.move_id else False

            self.write(cr, uid, ids, {'internal_number': invoice.number},
                       context=context)
            cr.execute('UPDATE account_move SET ref=%s '
                       'WHERE id=%s AND (ref is null OR ref = \'\')',
                       (ref, move_id))
            cr.execute('UPDATE account_move_line SET ref=%s '
                       'WHERE move_id=%s AND (ref is null OR ref = \'\')',
                       (ref, move_id))
            cr.execute(
                'UPDATE account_analytic_line SET ref=%s '
                'FROM account_move_line '
                'WHERE account_move_line.move_id = %s '
                'AND account_analytic_line.move_id = account_move_line.id',
                (ref, move_id))
        return True

    def create(self, cr, uid, vals, context=None):
        if (vals.get('supplier_invoice_number') and not
                vals.get('reference')):
            vals = vals.copy()
            vals['reference'] = vals['supplier_invoice_number']
        return super(AccountInvoice, self).create(cr, uid, vals,
                                                  context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('supplier_invoice_number'):
            for invoice in self.browse(cr, uid, ids, context=context):
                loc_vals = None
                if not invoice.reference:
                    loc_vals = vals.copy()
                    loc_vals['reference'] = vals['supplier_invoice_number']
                super(AccountInvoice, self).write(cr, uid, [invoice.id],
                                                  loc_vals or vals,
                                                  context=context)
            return True
        else:
            return super(AccountInvoice, self).write(cr, uid, ids, vals,
                                                     context=context)
