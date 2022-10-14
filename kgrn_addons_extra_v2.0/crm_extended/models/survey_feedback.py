from odoo import models, fields, exceptions, api, _


class Survey(models.Model):
    _inherit = 'survey.survey'
    _description = 'Survey'

    service_engagement_ids = fields.One2many('service.engagement.survey', 'survey_id')


class ServiceEngagementSurveyDetails(models.Model):
    _name = "service.engagement.survey"
    _description = "Service Engagement Survey Details"

    survey_id = fields.Many2one('survey.survey', string='Survey ID')
    service_engagement_id = fields.Many2one('sale.order', string='Service Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_mail = fields.Char(string='Customer Email')


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    def action_invite(self):
        res = super(SurveyInvite, self).action_invite()
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['sale.order'].search([('id', '=', applicant_id)])
        line_vals = []
        vals = [0, 0, {
          'service_engagement_id': active_id.id,
          'partner_id': active_id.partner_id.id,
          'partner_mail': active_id.partner_id.email
        }]
        line_vals.append(vals)
        active_id.feedback_id.service_engagement_ids = line_vals
        return res
