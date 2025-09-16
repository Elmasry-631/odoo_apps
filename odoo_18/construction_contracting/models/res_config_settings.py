# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Enterprise Feature Flags (Global)
    enable_project_scheduling_gantt = fields.Boolean(
        string="تفعيل Gantt",
        config_parameter="construction.enable_project_scheduling_gantt",
    )
    enable_cpm = fields.Boolean(
        string="تفعيل CPM (Critical Path)",
        config_parameter="construction.enable_cpm",
    )
    enable_agile_mode = fields.Boolean(
        string="تفعيل Agile/Sprints",
        config_parameter="construction.enable_agile_mode",
    )
    enable_estimate_wbs_structure = fields.Boolean(
        string="WBS داخل المقايسة",
        config_parameter="construction.enable_estimate_wbs_structure",
    )
    enable_contract_phasing_wbs = fields.Boolean(
        string="مراحل العقد/دفعات",
        config_parameter="construction.enable_contract_phasing_wbs",
    )
    enable_risk_register = fields.Boolean(
        string="سجل المخاطر",
        config_parameter="construction.enable_risk_register",
    )
    enable_qaqc_hse_advanced = fields.Boolean(
        string="QA/QC & HSE متقدم",
        config_parameter="construction.enable_qaqc_hse_advanced",
    )
    enable_docs_advanced = fields.Boolean(
        string="Document Control متقدم",
        config_parameter="construction.enable_docs_advanced",
    )
    enable_cashflow_forecast = fields.Boolean(
        string="Cash Flow Forecast",
        config_parameter="construction.enable_cashflow_forecast",
    )
    enable_subcontractor_advanced = fields.Boolean(
        string="Subcontractor Advanced",
        config_parameter="construction.enable_subcontractor_advanced",
    )
    enable_resource_planning = fields.Boolean(
        string="تخطيط الموارد",
        config_parameter="construction.enable_resource_planning",
    )
    enable_integrations = fields.Boolean(
        string="تكاملات (P6/MSP/BIM)",
        config_parameter="construction.enable_integrations",
    )
    enable_multi_stage_consultant_approval = fields.Boolean(
        string="اعتماد استشاري متعدد المراحل",
        config_parameter="construction.enable_multi_stage_consultant_approval",
    )
    require_attachments_on_consultant_approval = fields.Boolean(
        string="إلزام مرفقات عند الاعتماد",
        config_parameter="construction.require_attachments_on_consultant_approval",
    )

    # سياسات العقد الافتراضية (Per Company via res.company)
    default_retention_rate = fields.Float(
        string="Retention % افتراضي",
        default_model="res.company",
    )
    default_advance_percent = fields.Float(
        string="Advance % افتراضي",
        default_model="res.company",
    )
    default_advance_recovery_ipcs = fields.Integer(
        string="عدد المستخلصات لاسترداد المقدّم",
        default_model="res.company",
    )
    default_ld_rate_per_day = fields.Float(
        string="LDs نسبة/يوم",
        default_model="res.company",
    )
    default_ld_cap_percent = fields.Float(
        string="LDs سقف %",
        default_model="res.company",
    )
