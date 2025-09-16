# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class ConstructionEVMBucket(models.Model):
    _name = "construction.evm.period"
    _description = "EVM Monthly Bucket (PV/EV/AC + Cumulative)"
    _auto = False

    company_id = fields.Many2one("res.company", string="الشركة", readonly=True)
    project_id = fields.Many2one("project.project", string="المشروع", readonly=True, index=True)
    period = fields.Date(string="الشهر", readonly=True)
    currency_id = fields.Many2one("res.currency", string="العملة", readonly=True)
    pv = fields.Monetary(string="PV", readonly=True)
    ev = fields.Monetary(string="EV", readonly=True)
    ac = fields.Monetary(string="AC", readonly=True)
    pv_cum = fields.Monetary(string="PV (تراكمي)", readonly=True)
    ev_cum = fields.Monetary(string="EV (تراكمي)", readonly=True)
    ac_cum = fields.Monetary(string="AC (تراكمي)", readonly=True)
    cpi = fields.Float(string="CPI", digits=(16, 4), readonly=True)
    spi = fields.Float(string="SPI", digits=(16, 4), readonly=True)

    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'construction_evm_period_view')
    #     self._cr.execute("""
    #         CREATE VIEW construction_evm_period_view AS
    #         WITH
    #         -- EV: من المستخلصات المعتمدة (construction_ipc)
    #         ev_src AS (
    #             SELECT
    #                 i.company_id,
    #                 i.project_id,
    #                 date_trunc('month', i.period_end)::date AS period,
    #                 SUM(i.gross_before_tax) AS ev
    #             FROM construction_ipc i
    #             WHERE i.state IN ('approved', 'invoiced')
    #             GROUP BY i.company_id, i.project_id, date_trunc('month', i.period_end)
    #         ),
    #         -- AC: من account_analytic_line المرتبط بالحركة المحاسبية (posted)
    #         -- الربط بالمشروع عبر الحساب التحليلي للمشروع (analytic_account_id)
    #         ac_src AS (
    #             SELECT
    #                 p.company_id,
    #                 p.id AS project_id,
    #                 date_trunc('month', m.date)::date AS period,
    #                 /* ملاحظة: في analytic line تكون المصاريف سالبة غالبًا؛
    #                    نأخذ الإشارة بحيث يكون AC موجبًا كمجموع تكاليف */
    #                 SUM(-aal.amount) AS ac
    #             FROM account_analytic_line aal
    #             JOIN account_move_line l ON l.id = aal.move_line_id
    #             JOIN account_move m ON m.id = l.move_id AND m.state = 'posted'
    #             JOIN project_project p ON p.analytic_account_id = aal.account_id
    #             GROUP BY p.company_id, p.id, date_trunc('month', m.date)
    #         ),
    #         -- PV: من baseline الشهري
    #         pv_src AS (
    #             SELECT
    #                 p.company_id,
    #                 b.project_id,
    #                 b.period,
    #                 b.pv_amount AS pv
    #             FROM construction_baseline_period b
    #             JOIN project_project p ON p.id = b.project_id
    #         ),
    #         merged AS (
    #             SELECT
    #                 COALESCE(pv.company_id, ev.company_id, ac.company_id) AS company_id,
    #                 COALESCE(pv.project_id, ev.project_id, ac.project_id) AS project_id,
    #                 COALESCE(pv.period, ev.period, ac.period) AS period,
    #                 COALESCE(pv.pv, 0) AS pv,
    #                 COALESCE(ev.ev, 0) AS ev,
    #                 COALESCE(ac.ac, 0) AS ac
    #             FROM pv_src pv
    #             FULL OUTER JOIN ev_src ev
    #                 ON pv.project_id = ev.project_id AND pv.period = ev.period
    #             FULL OUTER JOIN ac_src ac
    #                 ON COALESCE(pv.project_id, ev.project_id) = ac.project_id
    #                AND COALESCE(pv.period, ev.period) = ac.period
    #         ),
    #         ranked AS (
    #             SELECT
    #                 m.*,
    #                 SUM(m.pv) OVER (PARTITION BY m.project_id ORDER BY m.period
    #                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS pv_cum,
    #                 SUM(m.ev) OVER (PARTITION BY m.project_id ORDER BY m.period
    #                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ev_cum,
    #                 SUM(m.ac) OVER (PARTITION BY m.project_id ORDER BY m.period
    #                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ac_cum
    #             FROM merged m
    #         )
    #         SELECT
    #             ROW_NUMBER() OVER() AS id,
    #             r.company_id,
    #             r.project_id,
    #             r.period,
    #             (SELECT currency_id FROM res_company WHERE id = r.company_id) AS currency_id,
    #             r.pv, r.ev, r.ac,
    #             r.pv_cum, r.ev_cum, r.ac_cum,
    #             CASE WHEN NULLIF(r.ac, 0) IS NOT NULL THEN r.ev / NULLIF(r.ac, 0) ELSE NULL END AS cpi,
    #             CASE WHEN NULLIF(r.pv, 0) IS NOT NULL THEN r.ev / NULLIF(r.pv, 0) ELSE NULL END AS spi
    #         FROM ranked r
    #         ORDER BY r.project_id, r.period;
    #     """)
