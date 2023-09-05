// frappe.listview_settings["Leave Application"] = {
// 	add_fields: ["leave_type", "employee", "employee_name", "total_leave_days", "from_date", "to_date"],
// 	has_indicator_for_draft: 1,
// 	get_indicator: function (doc) {
// 		let status_color = {
// 			"Approved": "green",
// 			"Rejected": "red",
// 			"Open": "orange",
// 			"Cancelled": "red",
// 			"Submitted": "blue"
// 		};
// 		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
// 		// return [__(doc.docstatus), status_color[doc.status], "status,=," + doc.status];
// 	}
// };


frappe.listview_settings["Leave Application"] = {
	add_fields: ["leave_type", "employee", "employee_name", "total_leave_days", "from_date", "to_date"],
    has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		var status_color = {
			'Draft': 'red',

			'Awaiting HR Approval': 'yellow',
            'Awaiting Reporting Incharge Approval': 'yellow',
            'Awaiting HOD Approval': 'yellow',
            'Awaiting CHO Approval': 'yellow',

            'Approved by Reporting Incharge' : 'purple',
            'Approved by HR': 'green',       
            'Approved by CHO': 'green',  
            'Approved by HOD': 'purple', 

            'Rejected by HR': 'red', 
            'Rejected by Reporting Incharge' : 'red',
            'Rejected by HOD': 'red',
            'Rejected by CHO': 'red',    


		};
       
        return [__(doc.status), status_color[doc.status], 'status,=,'+doc.status];
    
	}
};
