from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _

import time


class Lead(models.Model):
    _inherit = "crm.lead"

    estimate_date = fields.Datetime(string='Estimated Date')

    def get_comercial_head_recepients(self):
        cc = ''
        for notify in self.team_id.member_ids:
            cc = str(notify.partner_id.email) + ',' + cc
        cc = cc.rstrip(',')
        return cc

    def action_new_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
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
                    template = self.env.ref('crm_extended.service_proposal_followup_mai',
                                            False)
                    template.with_context(ctx).sudo().send_mail(self.id, force_send=True)
            elif datetime_in < cur_date:
                if abs(difff) == datetime_after:
                    template = self.env.ref('crm_extended.service_proposal_alert_mai',
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
        template = self.env.ref('crm_extended.mlmlmadmmlml', False)
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
        template = self.env.ref('crm_extended.service_engagemnet_confirmation_maiiii', False)
        template.send_mail(self.id, force_send=True)
        return super(SaleOrder, self).action_confirm()


class Team(models.Model):
    _inherit = 'crm.team'


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    future_follow_date = fields.Datetime(string='Future Follow Date')
