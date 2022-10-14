from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import werkzeug

import time


class Lead(models.Model):
    _inherit = "crm.lead"

    date_deadline = fields.Date(string='Estimated Date (Closed Date)')

    # close_date = fields.Date(string='Closed Date')

    def get_comercial_head_recepients(self):
        cc = ''
        for notify in self.team_id.member_ids:
            cc = str(notify.partner_id.email) + ',' + cc
        cc = cc.rstrip(',')
        return cc

    def action_new_quotation(self):
        action = self.env['ir.actions.actions']._for_xml_id("sale_crm.sale_action_quotations_new")
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.team_id:
            action['context']['default_team_id'] = self.team_id.id,
            action['context']['default_team_members_mail'] = self.get_comercial_head_recepients()
        if self.user_id:
            action['context']['default_user_id'] = self.user_id.id
        return action


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Proposal'),
        ('sent', 'Proposal Sent'),
        ('sale', 'Service Engagement'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    team_members = fields.Many2many('res.users', string='Team Members')
    team_members_mail = fields.Char(string='Team Members Mail')
    mail_to_team = fields.Boolean(string='Mail to Team')
    remainder_date = fields.Date(string='Remainder Date')
    remainder_datetime = fields.Datetime(string='Remainder Date')
    next_invoice_date = fields.Date(string='Next Invoice Date')
    next_invoice_date_num = fields.Integer(string='Days')
    invoice_terms_id = fields.Many2one('invoice.terms', string='Invoice Terms')
    payment_id = fields.Many2one('account.payment', string='Payment Id')
    advance_amount = fields.Float(string='Advance')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', journal_type)]")
    journal_type = fields.Selection([
        ('bank', 'Bank'),
        ('cash', 'Cash')], string="Journal Type")
    feedback_id = fields.Many2one('survey.survey', string='FeedBack ID')
    survey_start_url = fields.Char('Survey URL', compute='_compute_survey_start_url')

    @api.depends('feedback_id.access_token')
    def _compute_survey_start_url(self):
        for invite in self:
            invite.survey_start_url = werkzeug.urls.url_join(invite.feedback_id.get_base_url(),
                                                             invite.feedback_id.get_start_url()) if invite.feedback_id else False

    @api.onchange('next_invoice_date_num')
    def onchange_duration(self):
        if self.date_order:
            my_str = str(self.date_order.date())  # 👉️ (mm-dd-yyyy)
            date_1 = datetime.strptime(my_str, '%Y-%m-%d')
            result_1 = date_1 + timedelta(days=self.next_invoice_date_num)
            self.write({
                'next_invoice_date': result_1,
            })

    def get_advance_payment(self):
        hotel_advance_pay = self.env["account.payment"]
        for value in self:
            if self.advance_amount > 0.00:
                rec = hotel_advance_pay.create(
                    {
                        "partner_id": value.partner_id.id,
                        "amount": value.advance_amount,
                        "journal_id": value.journal_id.id,
                        "service_id": value.id,
                    }
                )
            else:
                raise UserError(_('Please add some items to move.'))
            journal = self.env['account.payment'].search([
                ('partner_id', '=', value.partner_id.id), ('amount', '=', value.advance_amount),
            ])
            journal.action_post()
            self.write({
                'payment_id': journal.id,
            })

    def send_feedback_screen(self):
        template = self.env.ref('crm_extended.customer_feed_back_form_sssuu', False)
        template.sudo().send_mail(self.id, force_send=True)

    def cron_service_proposal_reminder(self):
        service_proposal = self.env['sale.order'].sudo().search([('state', 'in', ['draft', 'sent'])])
        cur_date = str(date.today())
        dt21 = datetime.strptime(cur_date, '%Y-%m-%d')
        for order in service_proposal:
            ctx = self.env.context.copy()
            current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            current_user = self.env.user.name
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            current_url += '/web#id=%d&view_type=form&model=%s' % (order.id, order._name)
            cc = ''
            ctx = self.env.context.copy()
            ctx.update({
                'name': order.name,
                'url': current_url,
                'email_to': order.team_members_mail,
                'sale_amount': order.amount_total,
                'team_name': order.team_id.name,
                'team_leader': order.team_id.user_id.employee_id.work_email,
                'company_website': order.company_id.website,
                'company_email': order.company_id.email,
                'company_phone': order.company_id.phone,
            })
            datetime_check = (timedelta(hours=00, minutes=00, days=2))
            datetime_after = (timedelta(hours=00, minutes=00, days=1))
            datetime_in = str(order.remainder_date)
            dt22 = datetime.strptime(datetime_in, '%Y-%m-%d')
            difff = dt22 - dt21
            if datetime_in > cur_date:
                if difff <= datetime_check:
                    template = self.env.ref('crm_extended.service_proposal_followup_mailllll',
                                            False)
                    template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
            elif datetime_in < cur_date:
                if abs(difff) == datetime_after:
                    template = self.env.ref('crm_extended.service_proposal_alert_mailll',
                                            False)
                    template.with_context(ctx).sudo().send_mail(self.id, force_send=True)

    # Get Accountant List
    def get_accountant_list(self):
        cc = ''
        account_user = self.env['res.groups']. \
            sudo().search([('name', '=', 'Accountant')])
        for group_user in account_user.users:
            cc = str(group_user.employee_id.work_email) + ',' + cc
        cc = cc.rstrip(',')
        return cc

    # @api.onchange('remainder_date')
    def get_record_ids(self):
        service_proposal = self.env['sale.order'].sudo().search([('state', '=', 'sale')])
        records = []
        for service_id in service_proposal:
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            current_url += '/web#id=%d&view_type=form&model=%s' % (service_id.id, service_id._name)
            service = {}
            # if order.invoice_count == 0:
            if service_id:
                service['name'] = service_id.name
                service['team'] = service_id.team_id.name
                service['date'] = service_id.date_order
                service['url'] = current_url
                records.append(service)
        return records

    # Cron For Advance Payment Notification
    def cron_advance_payment_notification(self):
        ctx = self.env.context.copy()
        ctx.update({
            'email_to': self.get_accountant_list(),
            'company_website': self.company_id.website,
            'company_email': self.company_id.email,
            'company_phone': self.company_id.phone,
        })
        template = self.env.ref('crm_extended.aassasa', False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)

    def get_service_team_members(self):
        service_team = self.env['crm.team'].sudo().search([('name', '=', self.team_id.name)])
        self.update({
            'team_members': service_team.member_ids.ids,
        })

    def action_confirm(self):
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        ctx.update({
            'url': current_url,
        })
        template = self.env.ref('crm_extended.service_engagemnet_confirmation_maiiissieitlwii', False)
        template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
        return super(SaleOrder, self).action_confirm()


class Team(models.Model):
    _inherit = 'crm.team'


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    future_follow_date = fields.Datetime(string='Future Follow Date')


class InvoiceTerms(models.Model):
    _name = "invoice.terms"

    name = fields.Char(string='Invoice Terms')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    service_id = fields.Many2one('sale.order', string='Service Order')
