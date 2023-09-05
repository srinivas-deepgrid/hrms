frappe.ui.form.on('Over Time Application', {
	setup: function(frm) {
		frm.set_query("employee", erpnext.queries.employee);
		},
	employee: function(frm){
		if(frm.doc.docstatus == 0){
			frm.trigger('request_action')
		}
		if(!frm.doc.is_over_time_applicable){
			frappe.throw("You are not allowed to apply over time!")
		}
	},
	date:function(frm){

		if(frm.doc.employee && frm.doc.date){

			frappe.call({
				method: "hrms.hr.doctype.over_time_application.over_time_application.is_holiday",
				args: {
					employee: frm.doc.employee,
					attendance_date: frm.doc.date
				},
				callback: function(r) {
					// console.log("RESPONSE_____IS_HOLIDAY",r)
					 if (r.message == 1){
						frm.set_value("is_holiday",r.message)
						refresh_field('is_holiday')
						frm.trigger('is_holiday')
					}else if (r.message == 0){
						frm.set_value("is_holiday",r.message)
						refresh_field('is_holiday')
						frm.trigger('is_holiday')
					}else{
						frappe.throw(_("Error While Fetching is_holiday Details!"))
					}
				}
			  });		
		}
	},

	is_holiday:function(frm){

		if(frm.doc.employee && frm.doc.date && (frm.doc.is_holiday == 0 || frm.doc.is_holiday == 1)){

			frappe.call({
				method: "hrms.hr.doctype.attendance_application.attendance_application.get_attendance_status",
				args: {
					employee: frm.doc.employee,
					attendance_date: frm.doc.date
				},
				callback: function(r) {
					// console.log("RESPONSE_____ATTENDANCE_STATUS",r)

					frm.set_value("over_time",0);
					refresh_field("over_time");

					frm.set_value("ot_start_time","");
					refresh_field("ot_start_time");
					frm.set_value("ot_end_time","");
					refresh_field("ot_end_time");

					frm.set_value("shift","");
					refresh_field("shift");
					frm.set_value("next_shift","");
					refresh_field("next_shift");

					frm.set_value("ot_shift_1","");
					refresh_field("ot_shift_1");
					frm.set_value("shift_1_allowance",0);
					refresh_field("shift_1_allowance");
					frm.set_value("ot_shift_2","");
					refresh_field("ot_shift_2");
					frm.set_value("shift_2_allowance",0);
					refresh_field("shift_2_allowance");

					 if(frm.doc.is_holiday == 0){
						
						frm.set_df_property("next_shift", "hidden", true);
						frm.set_df_property("shift_2_allowance", "hidden", true);

						if(r.message == "Present"){
							frm.set_value("attendance_status",r.message);
							refresh_field("attendance_status");
						}else if (r.message){
							frm.set_value("attendance_status","");
							refresh_field("attendance_status");
							frappe.throw(__("Attendance found is not Present on the Selected Date!"));
						}
						else{
							frm.set_value("attendance_status","");
							refresh_field("attendance_status");
							frappe.throw(__("No Attendance Record Found on the Selected Date!"));
						}

					 }else if(frm.doc.is_holiday == 1){
						
						frm.set_df_property("next_shift", "hidden", false);
						frm.set_df_property("shift_2_allowance", "hidden", false);

						if(r.message == "Present" || r.message == "Permission"){
							frm.set_value("attendance_status",r.message);
							refresh_field("attendance_status");
						}else{
							frm.set_value("attendance_status","");
							refresh_field("attendance_status");
							frappe.throw(__("No Attendance Record Found on the Selected Date(Holiday)!"));
						}

					 }else{
						
						frappe.throw(_("Error While Fetching attendance_status Details!"))

					}
					frm.trigger('attendance_status')
				}
				 
			  });
		}
	},

	attendance_status:function(frm){
		if(frm.doc.employee && frm.doc.date && frm.doc.attendance_status && (frm.doc.is_holiday == 0 || frm.doc.is_holiday == 1) ){
			// console.log("attendance status--",frm.doc.attendance_status)
			frappe.call({
				method: "hrms.hr.doctype.over_time_application.over_time_application.get_over_time",
				args: {
					employee: frm.doc.employee,
					attendance_date: frm.doc.date
				},
				callback: function(r) {
					// console.log("over time: " + r.message);
					 if (r.message){
						frm.set_value("over_time",r.message[0]);
						refresh_field("over_time");

						frm.set_value("ot_start_time",r.message[1]);
						refresh_field("ot_start_time");
						frm.set_value("ot_end_time",r.message[2]);
						refresh_field("ot_end_time");

						frm.set_value("shift",r.message[3]);
						refresh_field("shift");
						frm.set_value("next_shift",r.message[4]);
						refresh_field("next_shift");

						frm.set_value("ot_shift_1",r.message[5]);
						refresh_field("ot_shift_1");
						frm.set_value("shift_1_allowance",r.message[6]);
						refresh_field("shift_1_allowance");

						frm.set_value("ot_shift_2",r.message[7]);
						refresh_field("ot_shift_2");
						frm.set_value("shift_2_allowance",r.message[8]);
						refresh_field("shift_2_allowance");

					}else{
						frm.set_value("over_time",0);
						refresh_field("over_time");

						frm.set_value("ot_start_time","");
						refresh_field("ot_start_time");
						frm.set_value("ot_end_time","");
						refresh_field("ot_end_time");

						frm.set_value("shift","");
						refresh_field("shift");
						frm.set_value("next_shift","");
						refresh_field("next_shift");

						frm.set_value("ot_shift_1","");
						refresh_field("ot_shift_1");
						frm.set_value("shift_1_allowance",0);
						refresh_field("shift_1_allowance");

						frm.set_value("ot_shift_2","");
						refresh_field("ot_shift_2");
						frm.set_value("shift_2_allowance",0);
						refresh_field("shift_2_allowance");
					}
				}
			  });
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

