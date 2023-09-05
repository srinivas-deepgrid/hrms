# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, format_date, getdate

from hrms.hr.utils import (
	create_additional_leave_ledger_entry,
	get_holiday_dates_for_employee,
	get_leave_period,
	validate_active_employee,
	validate_dates,
	validate_overlap,
)

from hrms.hr.doctype.over_time_application.over_time_application import (
	get_over_time
)


def validate_overlap_(doc):
	existing_records = frappe.get_all(
		"Compensatory Leave Request",
		filters={
			 "employee": doc.employee,
			 "date": doc.date,
			 "name": ("!=", doc.name)  # Exclude the current document
		}
	)

	if existing_records:
		frappe.throw("Compensatory Leave Request - Overlapping records already exist for the selected date and employee")

	existing_records_ = frappe.get_all(
		"Over Time Application",
		filters={
			 "employee": doc.employee,
			 "date": doc.date,
			 "docstatus" : 1
		}
	)

	if existing_records_:
		frappe.throw("Over Time Application Applied for the Selected Date!")



def share_doc_with_approver__(doc, user, ptype):
	# if approver does not have permissions, share
	if not frappe.has_permission(doc=doc, ptype=ptype, user=user):
		if ptype == "submit":
			submit = 1
			write = 0
		elif ptype == "write":
			submit = 0
			write  = 1
		frappe.share.add_docshare(
			doc.doctype, doc.name, user, write=write,submit=submit, flags={"ignore_share_permission": True},notify=1
		)

		# frappe.msgprint(
		# 	_("Shared with the user {0} with {1} access").format(user, frappe.bold(ptype), alert=True)
		# )



# class CompensatoryLeaveRequest(Document):
# 	def validate(self):
# 		validate_active_employee(self.employee)
# 		validate_dates(self, self.work_from_date, self.work_end_date)
# 		if self.half_day:
# 			if not self.half_day_date:
# 				frappe.throw(_("Half Day Date is mandatory"))
# 			if (
# 				not getdate(self.work_from_date) <= getdate(self.half_day_date) <= getdate(self.work_end_date)
# 			):
# 				frappe.throw(_("Half Day Date should be in between Work From Date and Work End Date"))
# 		validate_overlap(self, self.work_from_date, self.work_end_date)
# 		self.validate_holidays()
# 		self.validate_attendance()
# 		if not self.leave_type:
# 			frappe.throw(_("Leave Type is madatory"))

# 	def validate_attendance(self):
# 		attendance = frappe.get_all(
# 			"Attendance",
# 			filters={
# 				"attendance_date": ["between", (self.work_from_date, self.work_end_date)],
# 				"status": "Present",
# 				"docstatus": 1,
# 				"employee": self.employee,
# 			},
# 			fields=["attendance_date", "status"],
# 		)

# 		if len(attendance) < date_diff(self.work_end_date, self.work_from_date) + 1:
# 			frappe.throw(_("You are not present all day(s) between compensatory leave request days"))

# 	def validate_holidays(self):
# 		holidays = get_holiday_dates_for_employee(self.employee, self.work_from_date, self.work_end_date)
# 		if len(holidays) < date_diff(self.work_end_date, self.work_from_date) + 1:
# 			if date_diff(self.work_end_date, self.work_from_date):
# 				msg = _("The days between {0} to {1} are not valid holidays.").format(
# 					frappe.bold(format_date(self.work_from_date)), frappe.bold(format_date(self.work_end_date))
# 				)
# 			else:
# 				msg = _("{0} is not a holiday.").format(frappe.bold(format_date(self.work_from_date)))

# 			frappe.throw(msg)

# 	def on_submit(self):
# 		company = frappe.db.get_value("Employee", self.employee, "company")
# 		date_difference = date_diff(self.work_end_date, self.work_from_date) + 1
# 		if self.half_day:
# 			date_difference -= 0.5
# 		leave_period = get_leave_period(self.work_from_date, self.work_end_date, company)
# 		if leave_period:
# 			leave_allocation = self.get_existing_allocation_for_period(leave_period)
# 			if leave_allocation:
# 				print("leave_allocation.new_leaves_allocated---1",leave_allocation.new_leaves_allocated)
# 				leave_allocation.new_leaves_allocated += date_difference
# 				print("leave_allocation.new_leaves_allocated---2",leave_allocation.new_leaves_allocated)
# 				leave_allocation.validate()
# 				leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
# 				leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)

# 				# generate additional ledger entry for the new compensatory leaves off
# 				create_additional_leave_ledger_entry(
# 					leave_allocation, date_difference, add_days(self.work_end_date, 1)
# 				)

# 			else:
# 				leave_allocation = self.create_leave_allocation(leave_period, date_difference)
# 			self.db_set("leave_allocation", leave_allocation.name)
# 		else:
# 			frappe.throw(
# 				_("There is no leave period in between {0} and {1}").format(
# 					format_date(self.work_from_date), format_date(self.work_end_date)
# 				)
# 			)

# 	def on_cancel(self):
# 		if self.leave_allocation:
# 			date_difference = date_diff(self.work_end_date, self.work_from_date) + 1
# 			print("date_difference----",date_difference)
# 			if self.half_day:
# 				date_difference -= 0.5
# 			leave_allocation = frappe.get_doc("Leave Allocation", self.leave_allocation)
# 			print("leave_allocation---",leave_allocation)
# 			if leave_allocation:
# 				leave_allocation.new_leaves_allocated -= date_difference
# 				print("leave_allocation.new_leaves_allocated----1",leave_allocation.new_leaves_allocated)
# 				if leave_allocation.new_leaves_allocated - date_difference <= 0:
# 					leave_allocation.new_leaves_allocated = 0
# 				print("leave_allocation.new_leaves_allocated----2",leave_allocation.new_leaves_allocated)
# 				leave_allocation.validate()
# 				leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
# 				leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)

# 				# create reverse entry on cancelation
# 				create_additional_leave_ledger_entry(
# 					leave_allocation, date_difference * -1, add_days(self.work_end_date, 1)
# 				)

# 	def get_existing_allocation_for_period(self, leave_period):
# 		leave_allocation = frappe.db.sql(
# 			"""
# 			select name
# 			from `tabLeave Allocation`
# 			where employee=%(employee)s and leave_type=%(leave_type)s
# 				and docstatus=1
# 				and (from_date between %(from_date)s and %(to_date)s
# 					or to_date between %(from_date)s and %(to_date)s
# 					or (from_date < %(from_date)s and to_date > %(to_date)s))
# 		""",
# 			{
# 				"from_date": leave_period[0].from_date,
# 				"to_date": leave_period[0].to_date,
# 				"employee": self.employee,
# 				"leave_type": self.leave_type,
# 			},
# 			as_dict=1,
# 		)

# 		if leave_allocation:
# 			return frappe.get_doc("Leave Allocation", leave_allocation[0].name)
# 		else:
# 			return False

# 	def create_leave_allocation(self, leave_period, date_difference):
# 		is_carry_forward = frappe.db.get_value("Leave Type", self.leave_type, "is_carry_forward")
# 		allocation = frappe.get_doc(
# 			dict(
# 				doctype="Leave Allocation",
# 				employee=self.employee,
# 				employee_name=self.employee_name,
# 				leave_type=self.leave_type,
# 				from_date=add_days(self.work_end_date, 1),
# 				to_date=leave_period[0].to_date,
# 				carry_forward=cint(is_carry_forward),
# 				new_leaves_allocated=date_difference,
# 				total_leaves_allocated=date_difference,
# 				description=self.reason,
# 			)
# 		)
# 		allocation.insert(ignore_permissions=True)
# 		allocation.submit()
# 		return allocation


class CompensatoryLeaveRequest(Document):
	def validate(self):
		validate_active_employee(self.employee)
		validate_dates(self, self.work_from_date, self.work_end_date)
		# if self.half_day:
		# 	if not self.half_day_date:
		# 		frappe.throw(_("Half Day Date is mandatory"))
		# 	if (
		# 		not getdate(self.work_from_date) <= getdate(self.half_day_date) <= getdate(self.work_end_date)
		# 	):
		# 		frappe.throw(_("Half Day Date should be in between Work From Date and Work End Date"))
		validate_overlap_(self)
		# self.validate_holidays()
		self.validate_attendance()
		if not self.leave_type:
			frappe.throw(_("Leave Type is madatory"))

	def validate_attendance(self):
		attendance = frappe.get_all(
			"Attendance",
			filters={
				"attendance_date": ["between", (self.work_from_date, self.work_end_date)],
				"status":["in",["Present","Permission"]],
				"docstatus": 1,
				"employee": self.employee,
			},
			fields=["attendance_date", "status"],
		)

		if len(attendance) < date_diff(self.work_end_date, self.work_from_date) + 1:
			frappe.throw(_("You are not present on compensatory leave request day"))

	# def validate_holidays(self):
	# 	holidays = get_holiday_dates_for_employee(self.employee, self.work_from_date, self.work_end_date)
	# 	if len(holidays) < date_diff(self.work_end_date, self.work_from_date) + 1:
	# 		if date_diff(self.work_end_date, self.work_from_date):
	# 			msg = _("The days between {0} to {1} are not valid holidays.").format(
	# 				frappe.bold(format_date(self.work_from_date)), frappe.bold(format_date(self.work_end_date))
	# 			)
	# 		else:
	# 			msg = _("{0} is not a holiday.").format(frappe.bold(format_date(self.work_from_date)))

	# 		frappe.throw(msg)

	def on_update(self):

		# approvers = get_department_approvers(self.employee)
		user_roles = frappe.get_user().get_roles()
		# print("user_roles----",user_roles)
		hr_roles = ["HR User", "HR Manager"]
		
	
		name = frappe.get_user().name
		# frappe.user.name doesn't work
		# print("name--0--",name)

		# check whether approver has right to Approve Approval
		isApprover = (name == self.approver) or (name == self.hod_approver) or (name == self.cho_approver)
		# print("isApprover---",isApprover,"\n",self.approver,"\n",self.hod_approver)

		if self.request_action == 'Draft':
			# if Reporting Incharge Exists
			if (
				self.approver
				and
				self.status == 'Awaiting Reporting Incharge Approval'
				and
				self.reporting_incharge_status == 'Awaiting Reporting Incharge Approval'
			):
				# if HOD Exists
				if self.hod_approver:
					#  Share Doc to Repoting Incharge for Level-1 Approval
					share_doc_with_approver__(self,self.approver,"write")
					frappe.msgprint(_("Sent to Reporting Incharge {0} to Approve").format(frappe.bold(self.approver)))
				# if HOD Doesn't Exists
				else:
					# Share doc to Reporting Incharge for Direct Approval
					share_doc_with_approver__(self,self.approver,"submit")
					frappe.msgprint(_("Directly Sent to Reporting Incharge {0} to Approve").format(frappe.bold(self.approver)))
			# if Reporting Incharge Doesn't Exists
			else:
				# if HOD Exists
				if (
					self.hod_approver
					and
					self.status ==  'Awaiting HOD Approval'
					and
					self.hod_approver_status == 'Awaiting HOD Approval'
				):
					# Share doc to HOD for Direct Approval
					share_doc_with_approver__(self,self.hod_approver,"submit")
					frappe.msgprint(_("Directly Sent to HOD {0} to Approve").format(frappe.bold(self.hod_approver)))
				# if HOD Doesn't Exists
				elif(
					(not self.hod_approver)
					and 
					self.cho_approver
					and 
					self.status ==  'Awaiting CHO Approval'
					and
					self.cho_approver_status == 'Awaiting CHO Approval'
				):
					# Share doc to CHO for Direct Approval
					share_doc_with_approver__(self,self.cho_approver,"submit")
					frappe.msgprint(_("Diectly Sent to CHO {0} to Approve").format(frappe.bold(self.cho_approver)))
				else:
					# NO Approvers
					frappe.throw("There are no Approvers Assigned to Approve")

			
		elif self.request_action == 'Approved' and isApprover:
			# if Reporting Incharge Exists and Reporting Incharge is the current Approver
			if self.approver and (self.approver == name):
				# if HOD Exists
				if (
					self.hod_approver
					and 
					self.status == 'Awaiting HOD Approval'
					and
					self.reporting_incharge_status == 'Approved by Reporting Incharge'
					and
					self.hod_approver_status == 'Awaiting HOD Approval'
				):
					#  Share Doc to HOD for Level-2 Approval
					share_doc_with_approver__(self,self.hod_approver,"submit")
					frappe.msgprint(_("Sent to HOD {0} for Final Approval").format(frappe.bold(self.hod_approver)))
				# if HOD Doesn't Exists - Reporting Incharge is doing Final Approval 
				elif(
					self.status == 'Approved by Reporting Incharge'
					and
					self.reporting_incharge_status == 'Approved by Reporting Incharge'
				):
					frappe.msgprint(_("Approved by Reporting Incharge {0}").format(frappe.bold(self.approver)))
			
			# if HOD Exists and HOD is the current Approver then HOD will be the Final Approver
			elif(
				self.hod_approver 
				and 
				(self.hod_approver == name)
				and
				self.status == 'Approved by HOD'
				and
				self.hod_approver_status == 'Approved by HOD'
			):
				frappe.msgprint(_("Approved by HOD {0}").format(frappe.bold(self.hod_approver)))
				
			# if CHO Exists and CHO is the current Approver then CHO will be the Final Approver
			elif(
				self.cho_approver 
				and 
				(self.cho_approver == name)
				and
				self.status == 'Approved by CHO'
				and
				self.cho_approver_status == 'Approved by CHO'
			):
				frappe.msgprint(_("Approved by CHO {0}").format(frappe.bold(self.cho_approver)))
				
		
		elif self.request_action == 'Rejected' and isApprover:
			# if Reporting Incharge Exists and Reporting Incharge is the current Approver
			if (
				self.approver 
				and 
				(self.approver == name)
				and
				self.status == 'Rejected by Reporting Incharge'
				and
				self.reporting_incharge_status == 'Rejected by Reporting Incharge'
			):
				# if HOD Exists
				if self.hod_approver:
					#  Get back  Doc from HOD which went for Level-2 Approval
					if frappe.has_permission(doc=self, ptype="submit", user=self.hod_approver):
						frappe.share.add_docshare(
							self.doctype, self.name, self.hod_approver,read=0,submit=0, flags={"ignore_share_permission": True},notify=1
							)
					frappe.msgprint(_("Request is got Rejected by reporting Incharge {0}").format(frappe.bold(self.approver)))
				# if HOD Doesn't Exists - Reporting Incharge is doing Final Approval 
				else:
					frappe.msgprint(_("Request is got Rejected by reporting Incharge {0}").format(frappe.bold(self.approver)))
			
			# if HOD Exists and HOD is the current Approver then HOD will be the Final Approver
			elif(
				self.hod_approver 
				and 
				(self.hod_approver == name)
				and
				self.status == 'Rejected by HOD'
				and
				self.hod_approver_status == 'Rejected by HOD'
			):
				frappe.msgprint(_("Request is got Rejected by HOD {0}").format(frappe.bold(self.hod_approver)))
				
			# if CHO Exists and CHO is the current Approver then CHO will be the Final Approver
			elif(
				self.cho_approver 
				and 
				(self.cho_approver == name)
				and
				self.status == 'Rejected by CHO'
				and
				self.cho_approver_status == 'Rejected by CHO'
			):
				frappe.msgprint(_("Request is got Rejected by CHO {0}").format(frappe.bold(self.cho_approver)))
				
		elif any(role in user_roles for role in hr_roles):
			if self.request_action == 'Approved' and self.status == 'Approved by HR':
				frappe.msgprint(_("Approved by HR {0}").format(frappe.bold(name)))
			elif self.request_action == 'Rejected' and self.status == 'Rejected by HR':
				frappe.msgprint(_("Rejected by HR {0}").format(frappe.bold(name)))
			else:
				frappe.throw("Something went wrong HR")
		
		else:
			frappe.throw("You are not allowed to Edit")

	def on_submit(self):
		validate_overlap_(self)

		userid = frappe.db.get_value("Employee",self.employee,'user_id')
		name = frappe.get_user().name
		# print("userid----name",userid,name)

		if name == userid: #self Approver
			# print("Self Approval is not Allowed!")
			frappe.throw("Self Approval is not Allowed!")
		else: #if Approver and 	Applier are not equal
			# print("Applier and Approver are not equal")
			if self.status not in [
				"Approved", 
				"Rejected",
				"Approved by HR",
				"Rejected by HR",
				"Approved by CHO",
				"Rejected by CHO",
				"Approved by Reporting Incharge",
				"Rejected by Reporting Incharge",
				"Approved by HOD",
				"Rejected by HOD",
				"Awaiting Reporting Incharge Approval",
				"Awaiting HOD Approval",
				"Awaiting HR Approval",
				"Draft"
				]:
				frappe.throw(_("Only Shift Request with other status can't be submitted"))

			if self.request_action == "Draft":
				frappe.throw(_("Please select Request action Approve or Reject"))


			if self.status == 'Approved by Reporting Incharge' or self.status == "Approved by HR" or self.status == "Approved by HOD" or self.status == "Approved by CHO":
				# print("\ndocstatus before submitting---- ",self.docstatus)
				# print("\nstatus before submitting---- ",self.status)

				#  OT Calculation

				# frappe.msgprint(
				# 	_("Attendance Application created for Employee: {0}").format(
				# 		frappe.bold(self.employee)
				# 	)
				# )

				company = frappe.db.get_value("Employee", self.employee, "company")
				# date_difference = date_diff(self.work_end_date, self.work_from_date) + 1
				date_difference = get_compensatory_days(self.employee,self.date)
				# if self.half_day:
				# 	date_difference -= 0.5
				if not date_difference:
					frappe.throw("You are NOT eligible to Apply.Earned Compensatory Days are Zero!")
		
				leave_period = get_leave_period(self.work_from_date, self.work_end_date, company)
				if leave_period:
					leave_allocation = self.get_existing_allocation_for_period(leave_period)
					
					# print("get_existing_allocation_for_period---",leave_allocation)
					doc_dict = leave_allocation.as_dict()
					for fieldname, value in doc_dict.items():
						print(f"{fieldname}: {value}")
					
					if leave_allocation:
						# print("leave_allocation.new_leaves_allocated---1",leave_allocation.new_leaves_allocated)
						leave_allocation.new_leaves_allocated += date_difference
						# print("leave_allocation.new_leaves_allocated---2",leave_allocation.new_leaves_allocated)
						leave_allocation.validate()
						leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
						leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)
		
						leave_allocation.to_date = add_days(self.work_end_date, 121)
						# generate additional ledger entry for the new compensatory leaves off
						create_additional_leave_ledger_entry(
							leave_allocation, date_difference, add_days(self.work_end_date, 1)
						)
		
					else:
						leave_allocation = self.create_leave_allocation(leave_period, date_difference)
					self.db_set("leave_allocation", leave_allocation.name)
				else:
					frappe.throw(
						_("There is no leave period in between {0} and {1}").format(
							format_date(self.work_from_date), format_date(self.work_end_date)
						)
					)

	def on_cancel(self):
		if self.leave_allocation:
			# date_difference = date_diff(self.work_end_date, self.work_from_date) + 1
			date_difference = get_compensatory_days(self.employee,self.date)
			# print("date_difference----",date_difference)
			# if self.half_day:
			# 	date_difference -= 0.5
			leave_allocation = frappe.get_doc("Leave Allocation", self.leave_allocation)
			
			# print("leave_allocation---",leave_allocation)
			# doc_dict = leave_allocation.as_dict()
			# for fieldname, value in doc_dict.items():
			# 	print(f"{fieldname}: {value}")

			if leave_allocation:
				leave_allocation.new_leaves_allocated -= date_difference
				# print("leave_allocation.new_leaves_allocated----1",leave_allocation.new_leaves_allocated)
				if leave_allocation.new_leaves_allocated - date_difference <= 0:
					leave_allocation.new_leaves_allocated = 0
				# print("leave_allocation.new_leaves_allocated----2",leave_allocation.new_leaves_allocated)
				leave_allocation.validate()
				leave_allocation.db_set("new_leaves_allocated", leave_allocation.total_leaves_allocated)
				leave_allocation.db_set("total_leaves_allocated", leave_allocation.total_leaves_allocated)

				leave_allocation.to_date = add_days(self.work_end_date, 121)
				# create reverse entry on cancelation
				create_additional_leave_ledger_entry(
					leave_allocation, date_difference * -1, add_days(self.work_end_date, 1)
				)

	def get_existing_allocation_for_period(self, leave_period):
		leave_allocation = frappe.db.sql(
			"""
			select name
			from `tabLeave Allocation`
			where employee=%(employee)s and leave_type=%(leave_type)s
				and docstatus=1
				and (from_date between %(from_date)s and %(to_date)s
					or to_date between %(from_date)s and %(to_date)s
					or (from_date < %(from_date)s and to_date > %(to_date)s))
		""",
			{
				"from_date": leave_period[0].from_date,
				"to_date": leave_period[0].to_date,
				"employee": self.employee,
				"leave_type": self.leave_type,
			},
			as_dict=1,
		)

		if leave_allocation:
			return frappe.get_doc("Leave Allocation", leave_allocation[0].name)
		else:
			return False

	def create_leave_allocation(self, leave_period, date_difference):
		is_carry_forward = frappe.db.get_value("Leave Type", self.leave_type, "is_carry_forward")
		allocation = frappe.get_doc(
			dict(
				doctype="Leave Allocation",
				employee=self.employee,
				employee_name=self.employee_name,
				leave_type=self.leave_type,
				from_date=add_days(self.work_end_date, 1),
				to_date=leave_period[0].to_date,
				carry_forward=cint(is_carry_forward),
				new_leaves_allocated=date_difference,
				total_leaves_allocated=date_difference,
				description=self.reason,
			)
		)
		allocation.insert(ignore_permissions=True)
		allocation.submit()
		return allocation

@frappe.whitelist()
def get_compensatory_days(employee,attendance_date):
	days = get_over_time(employee,attendance_date)
	# print("days----",days)
	# print("days----",days[9])
	return days[9]