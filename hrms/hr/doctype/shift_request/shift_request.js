frappe.ui.form.on('Shift Request', {
	setup: function(frm) {
		frm.set_query("employee", erpnext.queries.employee);
		},
	employee: function(frm){
		if(frm.doc.docstatus == 0){
			frm.trigger('request_action')
		}
	},

    refresh: function(frm) {
		// check whether approver has right to Approve Approval
        var isApprover = frm.doc.approver === frappe.user.name || frm.doc.hod_approver === frappe.user.name || frm.doc.cho_approver === frappe.user.name;
		
		// Set status options based on user role and fields in the employee document
		//frappe.user_roles variable is used in Frappe to retrieve the list of roles assigned 
		// to the currently logged-in user. It returns an array of role names.
		var user_roles = frappe.user_roles;
		//if HR Manager/HR user creates records for the employee they can directly approvers
		var hasRolePermission = user_roles.includes("HR Manager") || user_roles.includes("HR User");


		console.log("user_roles--",user_roles)
		console.log("isApprover --",isApprover)
		console.log("hasRolePermission--",hasRolePermission)
		console.log("frappe.session.user--",frappe.session.user)
		console.log("frappe.user.name--",frappe.user.name)
		console.log("frm.doc.reporting_incharge--",frm.doc.approver)
		console.log("frm.doc.hod_approver--",frm.doc.hod_approver)

        if (isApprover || hasRolePermission) {
			// if doc is in the first stage of Approval Don't show any Request Actions for any Approver Default will be Draft
			if(!frm.doc.reporting_incharge_status && !frm.doc.hod_approver_status && !frm.doc.cho_approver_status){
				// Hide Request Action field
				frm.set_df_property("request_action", "hidden", true);
			}else{
				// Show Request Action field for approvers with Approved and Rejected options
				frm.set_df_property("request_action", "hidden", false);
				frm.set_df_property("request_action", "options", ["Approved", "Rejected"]);
			}

			console.log("!frm.doc.hod_approver--",!frm.doc.reporting_incharge_status && !frm.doc.hod_approver_status)
        } else{
			// Hide Request Action field for non-approvers
            frm.set_df_property("request_action", "hidden", true);
		}
		
		if(frm.doc.docstatus == 0){
			frm.trigger('request_action')
		}
    },
	request_action:function(frm){
		console.log("frm.doc.status---",frm.doc.status)
		console.log("frm.doc.request_action---",frm.doc.request_action)

		// check whether approver has right to Approve Approval
        var isApprover = frm.doc.approver === frappe.user.name || frm.doc.hod_approver === frappe.user.name || frm.doc.cho_approver === frappe.user.name;
		
		// Set status options based on user role and fields in the employee document
		//frappe.user_roles variable is used in Frappe to retrieve the list of roles assigned 
		// to the currently logged-in user. It returns an array of role names.
		var user_roles = frappe.user_roles;
		//if HR Manager/HR user creates records for the employee they can directly approvers
		var hasRolePermission = user_roles.includes("HR Manager") || user_roles.includes("HR User");

		// after proper Request action is selected 

		if(frm.doc.request_action == "Approved" && (isApprover || hasRolePermission)){
			if(frm.doc.employee){
				// if Reporting Incharge Exists and Reporting Incharge is the current Approver
				if(frm.doc.approver && frm.doc.approver === frappe.user.name){ // if Reporting Incharge Exists
					//if HOD Exists 
					if(frm.doc.hod_approver){

						frm.set_value('status',"Awaiting HOD Approval")
						frm.set_value("reporting_incharge_status","Approved by Reporting Incharge")
						frm.set_value("hod_approver_status","Awaiting HOD Approval")
						frm.set_value("cho_approver_status","")
						refresh_field('status')
						refresh_field('reporting_incharge_status')
						refresh_field('hod_approver_status')
						refresh_field('cho_approver_status')
						
					}
					// if HOD Doesn't Exists - Reporting Incharge is doing Final Approval 
					else{

						frm.set_value("status","Approved by Reporting Incharge")
						frm.set_value("reporting_incharge_status","Approved by Reporting Incharge")
						frm.set_value("hod_approver_status","")
						frm.set_value("cho_approver_status","")
						refresh_field('status')
						refresh_field('reporting_incharge_status')
						refresh_field('hod_approver_status')						
						refresh_field('cho_approver_status')
					}
				}
				
				// if HOD Exists and HOD is the current Approver then HOD will be the Final Approver

				else if(frm.doc.hod_approver && frm.doc.hod_approver == frappe.user.name){ // if Reporting Incharge Doesn't Exists
					
					// if HOD Exists										
						frm.set_value('status',"Approved by HOD")
						frm.set_value("hod_approver_status","Approved by HOD")
						refresh_field('status')
						refresh_field('hod_approver_status')
					
				}
				
				// if CHO Exists and CHO is the current Approver then CHO will be the Final Approver

				else if (frm.doc.cho_approver && frm.doc.cho_approver == frappe.user.name){ // if CHO Exists
					
						frm.set_value('status',"Approved by CHO")
						frm.set_value("cho_approver_status","Approved by CHO")
						refresh_field('status')
						refresh_field('cho_approver_status')

				}
				
				else if (hasRolePermission){
					frm.set_value('status',"Approved by HR")
					refresh_field('status')
				}
				
				else{
					frappe.throw("You are not allowed to Approve!");
				}
			}
		}
		
		else if(frm.doc.request_action == "Rejected"  && (isApprover || hasRolePermission)){
			if(frm.doc.employee){
				// if Reporting Incharge Exists and Reporting Incharge is the current Approver
				if(frm.doc.approver && frm.doc.approver === frappe.user.name){ // if Reporting Incharge Exists

					frm.set_value('status',"Rejected by Reporting Incharge")
					frm.set_value("reporting_incharge_status","Rejected by Reporting Incharge")
					frm.set_value("hod_approver_status","")
					frm.set_value("cho_approver_status","")
					refresh_field('status')
					refresh_field('reporting_incharge_status')
					refresh_field('hod_approver_status')
					refresh_field('cho_approver_status')

				}
				
				// if HOD Exists and HOD is the current Approver then HOD will be the Final Approver

				else if(frm.doc.hod_approver && frm.doc.hod_approver == frappe.user.name){ // if Reporting Incharge Doesn't Exists
					
					// if HOD Exists										
					frm.set_value('status',"Rejected by HOD")
					frm.set_value("hod_approver_status","Rejected by HOD")
					refresh_field('status')
					refresh_field('hod_approver_status')
					
				}
				
				// if CHO Exists and CHO is the current Approver then CHO will be the Final Approver

				else if (frm.doc.cho_approver && frm.doc.cho_approver == frappe.user.name){ // if CHO Exists
					
					frm.set_value('status',"Rejected by CHO")
					frm.set_value("cho_approver_status","Rejected by CHO")
					refresh_field('status')
					refresh_field('cho_approver_status')

				}
				
				else if (hasRolePermission){
					frm.set_value('status',"Rejected by HR")
					refresh_field('status')
				}
				
				else{
					frappe.throw("You are not allowed to Reject!");
				}
			}
			
		}
				
		else if(frm.doc.request_action == "Draft"){

			if(frm.doc.employee){
				if(frm.doc.approver){ // if Reporting Incharge Exists
					frm.set_value('status',"Awaiting Reporting Incharge Approval")
					frm.set_value("reporting_incharge_status","Awaiting Reporting Incharge Approval")
					frm.set_value("hod_approver_status","")
					frm.set_value("cho_approver_status","")
					refresh_field('status')
					refresh_field('reporting_incharge_status')
					refresh_field('hod_approver_status')
					refresh_field('cho_approver_status')
				}else if (!frm.doc.approver){ // if Reporting Incharge Doesn't Exists
					if(frm.doc.hod_approver){ // if HOD Exists
						frm.set_value('status',"Awaiting HOD Approval")
						frm.set_value("reporting_incharge_status","")
						frm.set_value("hod_approver_status","Awaiting HOD Approval")
						refresh_field('status')
						refresh_field('reporting_incharge_status')
						refresh_field('hod_approver_status')
						refresh_field('cho_approver_status')
					}else if (frm.doc.cho_approver){ // if CHO Exists
						frm.set_value('status',"Awaiting CHO Approval")
						frm.set_value("reporting_incharge_status","")
						frm.set_value("hod_approver_status","")
						frm.set_value("cho_approver_status","Awaiting CHO Approval")
						refresh_field('status')
						refresh_field('reporting_incharge_status')
						refresh_field('hod_approver_status')
						refresh_field('cho_approver_status')
					}else{
						frappe.throw("No Approvers Found!");
					}
				}else{
					frappe.throw("No Approvers Found!");
				}
			}
		}

	}
});
