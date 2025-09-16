{
"name" : "Test App Odoo",
"version" : "1.0",
"summary" : "A test application for Odoo",
"description" : "This is a test application to demonstrate Odoo module structure.",
"category" : "Tools",
"author" : "Ibrahim Elmasry",
"website" : "https://www.woledge.com",
"license" : "LGPL-3",
"depends" : ["base"],
"data" : [
    "views/test_app_odoo_views.xml",
    "security/ir.model.access.csv",
],
"installable" : True,
"application" : True,
"auto_install" : False,

}
