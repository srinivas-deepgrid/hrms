// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');

cur_frm.cscript.onload = function(doc, cdt, cdn) {
	if(doc.__islocal) cur_frm.set_value("attendance_date", frappe.datetime.get_today());
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}
}

frappe.ui.form.on('Attendance', {
	
	onload:function(frm){

		if(frm.doc.__islocal){
			frm.trigger('status')
		}
	},
	
	status:function (frm) {
		if(frm.doc.status == "Present" || frm.doc.status == "Work From Home"){
			frm.set_value("count",1);
			refresh_field('count');
		}else if (frm.doc.status == "Half Day"){
			frm.set_value("count",0.5);
			refresh_field('count');
		}else {
			frm.set_value("count",0);
			refresh_field('count');
		}
	}
})