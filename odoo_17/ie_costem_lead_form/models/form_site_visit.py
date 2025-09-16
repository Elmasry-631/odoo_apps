from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'crm.lead'

    # === Shared Header Fields ===
    sales_eng = fields.Char(string="Sales Eng")
    company_reference = fields.Char(string="Company Reference")
    date = fields.Date(string="Date")

    # === SITE VISIT FORM ===

    # A - Project Details
    site_company_name = fields.Char(string="Company Name")
    site_project_name = fields.Char(string="Project Name")
    site_project_address = fields.Char(string="Project Address")

    contractor_name = fields.Char(string="Contractor Site Eng Name")
    contractor_mobile = fields.Char(string="Contractor Site Eng Mobile No.")
    contractor_email = fields.Char(string="Contractor Site Eng Email")

    consultant_name = fields.Char(string="Consultant Name")
    consultant_email = fields.Char(string="Consultant Email")

    consultant_site_name = fields.Char(string="Consultant Site Eng Name")
    consultant_site_mobile = fields.Char(string="Consultant Site Eng Mobile No.")
    consultant_site_email = fields.Char(string="Consultant Site Eng Email")

    supervisor_name = fields.Char(string="Supervisor Consultant Name")
    supervisor_mobile = fields.Char(string="Supervisor Consultant Mobile No.")
    supervisor_email = fields.Char(string="Supervisor Consultant Email")

    # B - Systeme Supplier
    fire_alarm_supplier = fields.Char(string="Fire Alarm - Supplier Company")
    fire_alarm_engineer = fields.Char(string="Fire Alarm - Engineer")
    fire_alarm_mobile = fields.Char(string="Fire Alarm - Mobile No")

    public_address_supplier = fields.Char(string="Public Address - Supplier Company")
    public_address_engineer = fields.Char(string="Public Address - Engineer")
    public_address_mobile = fields.Char(string="Public Address - Mobile No")

    data_system_supplier = fields.Char(string="Data System - Supplier Company")
    data_system_engineer = fields.Char(string="Data System - Engineer")
    data_system_mobile = fields.Char(string="Data System - Mobile No")

    access_control_supplier = fields.Char(string="Access Control - Supplier Company")
    access_control_engineer = fields.Char(string="Access Control - Engineer")
    access_control_mobile = fields.Char(string="Access Control - Mobile No")

    bms_supplier = fields.Char(string="BMS - Supplier Company")
    bms_engineer = fields.Char(string="BMS - Engineer")
    bms_mobile = fields.Char(string="BMS - Mobile No")

    cctv_supplier = fields.Char(string="CCTV - Supplier Company")
    cctv_engineer = fields.Char(string="CCTV - Engineer")
    cctv_mobile = fields.Char(string="CCTV - Mobile No")

    matv_supplier = fields.Char(string="MATV - Supplier Company")
    matv_engineer = fields.Char(string="MATV - Engineer")
    matv_mobile = fields.Char(string="MATV - Mobile No")

    other_supplier = fields.Char(string="Other - Supplier Company")
    other_engineer = fields.Char(string="Other - Engineer")
    other_mobile = fields.Char(string="Other - Mobile No")

    # C - Requirements
    fire_alarm_note = fields.Text(string="Fire Alarm - Notes")
    fire_alarm_requirement = fields.Text(string="Fire Alarm - Requirement")

    public_address_note = fields.Text(string="Public Address - Notes")
    public_address_requirement = fields.Text(string="Public Address - Requirement")

    data_system_note = fields.Text(string="Data System - Notes")
    data_system_requirement = fields.Text(string="Data System - Requirement")

    access_control_note = fields.Text(string="Access Control - Notes")
    access_control_requirement = fields.Text(string="Access Control - Requirement")

    bms_note = fields.Text(string="BMS - Notes")
    bms_requirement = fields.Text(string="BMS - Requirement")

    cctv_note = fields.Text(string="CCTV - Notes")
    cctv_requirement = fields.Text(string="CCTV - Requirement")

    matv_note = fields.Text(string="MATV - Notes")
    matv_requirement = fields.Text(string="MATV - Requirement")

    other_note = fields.Text(string="Other - Notes")
    other_requirement = fields.Text(string="Other - Requirement")

    site_signature = fields.Binary(string="Site Visit Signature")

    # === COMPANY VISIT FORM ===

    company_name = fields.Char(string="Company Name")
    tax_id = fields.Char(string="Tax ID")
    address = fields.Char(string="Address")
    telephone = fields.Char(string="Telephone No.")
    company_email = fields.Char(string="Company Email")

    general_manager_name = fields.Char()
    general_manager_mobile = fields.Char()
    general_manager_email = fields.Char()

    projects_manager_name = fields.Char()
    projects_manager_mobile = fields.Char()
    projects_manager_email = fields.Char()

    electrical_manager_name = fields.Char()
    electrical_manager_mobile = fields.Char()
    electrical_manager_email = fields.Char()

    purchasing_manager_name = fields.Char()
    purchasing_manager_mobile = fields.Char()
    purchasing_manager_email = fields.Char()

    financial_manager_name = fields.Char()
    financial_manager_mobile = fields.Char()
    financial_manager_email = fields.Char()

    # ثابت: بيانات 2 مشروع فقط (مثال، ممكن تزود)
    project_name_1 = fields.Char()
    location_1 = fields.Char()
    consultant_1 = fields.Char()
    site_eng_1 = fields.Char()
    mobile_1 = fields.Char()
    specifications_1 = fields.Text()

    project_name_2 = fields.Char()
    location_2 = fields.Char()
    consultant_2 = fields.Char()
    site_eng_2 = fields.Char()
    mobile_2 = fields.Char()
    specifications_2 = fields.Text()

    # Requirements
    req_project_name_1 = fields.Char()
    req_system_1 = fields.Char()
    req_notes_1 = fields.Text()

    req_project_name_2 = fields.Char()
    req_system_2 = fields.Char()
    req_notes_2 = fields.Text()

    company_signature = fields.Binary(string="Company Visit Signature")
