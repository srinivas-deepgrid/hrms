// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'employee_name', 'employee_name');
cur_frm.add_fetch('employee', 'company', 'company');

frappe.ui.form.on("Leave Application", {
	setup: function(frm) {
		frm.set_query("leave_approver", function() {
			return {
				query: "hrms.hr.doctype.department_approver.department_approver.get_approvers",
				filters: {
					employee: frm.doc.employee,
					// doctype: frm.doc.doctype 
					doctype:"Shift Request"
				}
			};
		});

		frm.set_query("employee", erpnext.queries.employee);
	},
	onload: function(frm) {

		frm.fields_dict.attachment_image.$input_wrapper.on('click', function() {
            var attachment_url = frm.doc.attachment_image;
            if (attachment_url) {
                window.open(attachment_url, '_blank');
            }
        });
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];

		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
		if (frm.doc.docstatus == 0) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_mandatory_approval",
				args: {
					doctype: frm.doc.doctype,
				},
				callback: function(r) {
					if (!r.exc && r.message) {
						// frm.toggle_reqd("leave_approver", true);
					}
				}
			});
		}
	},

	validate: function(frm) {
		if (frm.doc.from_date == frm.doc.to_date && frm.doc.half_day == 1) {
			frm.doc.half_day_date = frm.doc.from_date;
		} else if (frm.doc.half_day == 0) {
			frm.doc.half_day_date = "";
		}
		frm.toggle_reqd("half_day_date", frm.doc.half_day == 1);
	},

	make_dashboard: function(frm) {
		var leave_details;
		let lwps;
		if (frm.doc.employee) {
			frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_details",
				async: false,
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date || frm.doc.posting_date
				},
				callback: function(r) {
					if (!r.exc && r.message['leave_allocation']) {
						leave_details = r.message['leave_allocation'];
					}
					if (!r.exc && r.message['leave_approver']) {
						frm.set_value('leave_approver', r.message['leave_approver']);
					}
					lwps = r.message["lwps"];
				}
			});
			$("div").remove(".form-dashboard-section.custom");
			frm.dashboard.add_section(
				frappe.render_template('leave_application_dashboard', {
					data: leave_details
				}),
				__("Allocated Leaves")
			);
			frm.dashboard.show();
			let allowed_leave_types = Object.keys(leave_details);

			// lwps should be allowed, lwps don't have any allocation
			allowed_leave_types = allowed_leave_types.concat(lwps);

			frm.set_query('leave_type', function() {
				return {
					filters: [
						['leave_type_name', 'in', allowed_leave_types]
					]
				};
			});
		}
	},

	refresh: function(frm) {
		if (frm.is_new()) {
			frm.trigger("calculate_total_days");
		}
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !in_list(frappe.user_roles, "Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		if (!frm.doc.employee && frappe.defaults.get_user_permissions()) {
			const perm = frappe.defaults.get_user_permissions();
			if (perm && perm['Employee']) {
				frm.set_value('employee', perm['Employee'].map(perm_doc => perm_doc.doc)[0]);
			}
		}

		
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

	employee: function(frm) {
		frm.trigger("make_dashboard");
		frm.trigger("get_leave_balance");
		frm.trigger("set_leave_approver");
		if(frm.doc.docstatus == 0){
			frm.trigger('request_action')
		}
	},

	leave_approver: function(frm) {
		if (frm.doc.leave_approver) {
			frm.set_value("leave_approver_name", frappe.user.full_name(frm.doc.leave_approver));
		}
	},

	leave_type: function(frm) {
		frm.trigger("get_leave_balance");
		frm.trigger("calculate_total_days");
		frm.events.attachmenImageMandatory(frm);
	},

	attachmenImageMandatory : function(frm){
		if((frm.doc.leave_type == "Sick Leave") && (frm.doc.total_leave_days > 1)){
			frm.toggle_reqd("attachment_image", true);
		}else{
			frm.toggle_reqd("attachment_image", false);
		}
	},

	half_day: function(frm) {
		if (frm.doc.half_day) {
			if (frm.doc.from_date == frm.doc.to_date) {
				frm.set_value("half_day_date", frm.doc.from_date);
			} else {
				frm.trigger("half_day_datepicker");
			}
		} else {
			frm.set_value("half_day_date", "");
		}
		frm.trigger("calculate_total_days");
	},

	from_date: function(frm) {
		frm.trigger("make_dashboard");
		frm.trigger("half_day_datepicker");
		frm.trigger("calculate_total_days");
		frm.events.hide_half_day(frm);
	},

	to_date: function(frm) {
		frm.trigger("make_dashboard");
		frm.trigger("half_day_datepicker");
		frm.trigger("calculate_total_days");
		frm.events.hide_half_day(frm);
	},

	half_day_date(frm) {
		frm.trigger("calculate_total_days");
	},

	half_day_datepicker: function(frm) {
		frm.set_value('half_day_date', '');
		var half_day_datepicker = frm.fields_dict.half_day_date.datepicker;
		half_day_datepicker.update({
			minDate: frappe.datetime.str_to_obj(frm.doc.from_date),
			maxDate: frappe.datetime.str_to_obj(frm.doc.to_date)
		});
	},

	get_leave_balance: function(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.from_date && frm.doc.to_date) {
			return frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date,
					to_date: frm.doc.to_date,
					leave_type: frm.doc.leave_type,
					consider_all_leaves_in_the_allocation_period: 1
				},
				callback: function (r) {
					if (!r.exc && r.message) {
						frm.set_value('leave_balance', r.message);
					} else {
						frm.set_value('leave_balance', "0");
					}
				}
			});
		}
	},

	calculate_total_days: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.employee && frm.doc.leave_type) {

			var from_date = Date.parse(frm.doc.from_date);
			var to_date = Date.parse(frm.doc.to_date);

			if (to_date < from_date) {
				frappe.msgprint(__("To Date cannot be less than From Date"));
				frm.set_value('to_date', '');
				return;
			}
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'hrms.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
				args: {
					"employee": frm.doc.employee,
					"leave_type": frm.doc.leave_type,
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"half_day": frm.doc.half_day,
					"half_day_date": frm.doc.half_day_date,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('total_leave_days', r.message);
						frm.trigger("get_leave_balance");
						frm.events.attachmenImageMandatory(frm);
					}
				}
			});
		}
	},

	set_leave_approver: function(frm) {
		if (frm.doc.employee) {
			// server call is done to include holidays in leave days calculations
			return frappe.call({
				method: 'hrms.hr.doctype.leave_application.leave_application.get_leave_approver',
				args: {
					"employee": frm.doc.employee,
				},
				callback: function(r) {
					if (r && r.message) {
						frm.set_value('leave_approver', r.message);
					}
				}
			});
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

	},

	hide_half_day :function(frm){
		if(frm.doc.from_date && frm.doc.to_date){
			if(frm.doc.from_date == frm.doc.to_date){
				frm.set_df_property("half_day", "hidden", false);
			}else{
				frm.set_value('half_day',0);
				frm.set_df_property("half_day", "hidden", true);
			}
		}
	}
});

frappe.tour["Leave Application"] = [
	{
		fieldname: "employee",
		title: "Employee",
		description: __("Select the Employee.")
	},
	{
		fieldname: "leave_type",
		title: "Leave Type",
		description: __("Select type of leave the employee wants to apply for, like Sick Leave, Privilege Leave, Casual Leave, etc.")
	},
	{
		fieldname: "from_date",
		title: "From Date",
		description: __("Select the start date for your Leave Application.")
	},
	{
		fieldname: "to_date",
		title: "To Date",
		description: __("Select the end date for your Leave Application.")
	},
	{
		fieldname: "half_day",
		title: "Half Day",
		description: __("To apply for a Half Day check 'Half Day' and select the Half Day Date")
	},
	{
		fieldname: "leave_approver",
		title: "Leave Approver",
		description: __("Select your Leave Approver i.e. the person who approves or rejects your leaves.")
	}
];
