frappe.listview_settings['Salary Slip'] = {
	add_fields: ["employee", "employee_name"],
	
	onload: function(list_view) {
		let me = this;
		list_view.page.add_inner_button(__("Glovis Export"), function() {
			// Custom export logic
			let selected_docs = list_view.get_checked_items();
			if (selected_docs.length > 0) {
				// var selected_slips = selected_docs.map(doc => doc.name);
				// var encoded_docs = encodeURIComponent(JSON.stringify(selected_slips));
				// console.log("encoded_docs----",encoded_docs)
				// var url = window.location.origin + '/api/method/hrms.payroll.doctype.salary_slip.salary_slip.on_glovis_export?selected_slips=' + encoded_docs;
				// var w = window.open(url);
				// if (!w) {
				// 	frappe.msgprint(__('Please enable pop-ups'));
				// }
				let selected_slips = selected_docs.map(doc => doc.name);
        		let postData = selected_slips
        	
			
        		let form = document.createElement("form");
        		form.method = "POST";
        		form.action = "/api/method/hrms.payroll.doctype.salary_slip.salary_slip.on_glovis_export";
        		form.target = "_blank"; // Open in a new tab/window
			
        		// Add CSRF token
        		let csrfInput = document.createElement("input");
        		csrfInput.type = "hidden";
        		csrfInput.name = "csrf_token";
        		csrfInput.value = frappe.csrf_token; // Include the CSRF token value
        		form.appendChild(csrfInput);

				let input = document.createElement("input");
        		input.type = "hidden";
        		input.name = "data";
        		input.value = JSON.stringify(postData);
			
        		form.appendChild(input);
        		document.body.appendChild(form);
        		form.submit();
    			}		
			
		});
	}
};
