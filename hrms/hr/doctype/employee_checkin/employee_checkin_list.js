frappe.listview_settings["Employee Checkin"] = {
    has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		var status_color = {
			'Attendance Application': 'red',    
            'Bio Metric':'green',
            'Employee Check In':'pink'

		};
       
        return [__(doc.status), status_color[doc.status], 'status,=,'+doc.status];
    
	}
};