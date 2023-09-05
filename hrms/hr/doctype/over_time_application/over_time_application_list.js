frappe.listview_settings["Over Time Application"] = {
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
