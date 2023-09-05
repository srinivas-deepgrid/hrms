# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Criterion
from frappe.utils import get_link_to_form

from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings
from hrms.hr.utils import share_doc_with_approver, validate_active_employee
# from frappe.auth import User

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


class OverlappingShiftRequestError(frappe.ValidationError):
	pass


class ShiftRequest(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_from_to_dates("from_date", "to_date")
		self.validate_overlapping_shift_requests()
		# self.validate_approver()
		# self.validate_default_shift()

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
				assignment_doc = frappe.new_doc("Shift Assignment")
				assignment_doc.company = self.company
				assignment_doc.shift_type = self.shift_type
				assignment_doc.employee = self.employee
				assignment_doc.start_date = self.from_date
				if self.to_date:
					assignment_doc.end_date = self.to_date
				assignment_doc.shift_request = self.name
				assignment_doc.flags.ignore_permissions = 1
				assignment_doc.insert()
				assignment_doc.submit()

				frappe.msgprint(
					_("Shift Assignment: {0} created for Employee: {1}").format(
						frappe.bold(assignment_doc.name), frappe.bold(self.employee)
					)
				)

	def on_cancel(self):
		# print("Cancelling----")
		shift_assignment_list = frappe.get_list(
			"Shift Assignment", {"employee": self.employee, "shift_request": self.name}
		)
		if shift_assignment_list:
			for shift in shift_assignment_list:
				shift_assignment_doc = frappe.get_doc("Shift Assignment", shift["name"])
				shift_assignment_doc.cancel()

	def validate_default_shift(self):
		#  have to implement 
		default_shift = frappe.get_value("Employee", self.employee, "default_shift")
		if self.shift_type == default_shift:
			frappe.throw(
				_("You can not request for your Default Shift: {0}").format(frappe.bold(self.shift_type))
			)

	def validate_approver(self):
		approvers = get_department_approvers(self.employee)
		# print("******* validate_approver *****",approvers,"\n\n",self.approver)

		# if self.approver not in approvers:
		# 	frappe.throw(_("Only Approvers can Approve this Request."))
		
		

	def validate_overlapping_shift_requests(self):
		overlapping_dates = self.get_overlapping_dates()

		# print("overlapping_dates-----",overlapping_dates)

		if len(overlapping_dates):
			self.throw_overlap_error(overlapping_dates[0])
			# if dates are overlapping, check if timings are overlapping, else allow
			# overlapping_timings = has_overlapping_timings(self.shift_type, overlapping_dates[0].shift_type)
			# if overlapping_timings:
			# 	self.throw_overlap_error(overlapping_dates[0])

	def get_overlapping_dates(self):
		# print("self.name---",self.name)
		if not self.name:
			self.name = "New Shift Request"

		shift = frappe.qb.DocType("Shift Request")
		status_list = [
			"Approved by HR",
			"Approved by Reporting Incharge",
			"Approved by HOD",
			"Approved by CHO",
			"Awaiting Reporting Incharge Approval",
			"Awaiting HOD Approval",
			"Awaiting CHO Approval"
		]
		query = (
			frappe.qb.from_(shift)
			.select(shift.name, shift.shift_type)
			.where((shift.employee == self.employee) & (shift.docstatus < 2) & (shift.name != self.name) & shift.status.isin(status_list))
		)

		if self.to_date:
			query = query.where(
				Criterion.any(
					[
						Criterion.any(
							[
								shift.to_date.isnull(),
								((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date)),
							]
						),
						Criterion.any(
							[
								((self.to_date >= shift.from_date) & (self.to_date <= shift.to_date)),
								shift.from_date.between(self.from_date, self.to_date),
							]
						),
					]
				)
			)
		else:
			query = query.where(
				shift.to_date.isnull()
				| ((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date))
			)

		return query.run(as_dict=True)

	def throw_overlap_error(self, shift_details):
		shift_details = frappe._dict(shift_details)
		msg = _(
			"Employee {0} has already applied for Shift {1}: {2} that overlaps within this period"
		).format(
			frappe.bold(self.employee),
			frappe.bold(shift_details.shift_type),
			get_link_to_form("Shift Request", shift_details.name),
		)

		frappe.throw(msg, title=_("Overlapping Shift Requests"), exc=OverlappingShiftRequestError)


@frappe.whitelist()
def get_department_approvers(employee):
	# print("Employee----",employee)
	department = frappe.get_value("Employee", employee, "department")
	shift_approver = frappe.get_value("Employee",employee, "shift_request_approver")
	approvers = frappe.db.sql(
		"""select approver from `tabDepartment Approver` where parent= %s and parentfield = 'shift_request_approver'""",
		(department),
	)
	# print("---------approvers----0",approvers) #(('clintonlourthuraj@gmail.com',),)
	approvers = [approver[0] for approver in approvers]
	# print("---------approvers----1",approvers)
	approvers.insert(0,shift_approver)
	# print("---------approvers----2",approvers)
	return approvers

@frappe.whitelist()
def test_db(status):
	name = "HR-SHR-23-06-00009"
	frappe.db.set_value("Shift Request", name, "status", status)
	# print("test_db-------------------done")
# class ShiftRequest(Document):
# 	def validate(self):
# 		validate_active_employee(self.employee)
# 		self.validate_from_to_dates("from_date", "to_date")
# 		self.validate_overlapping_shift_requests()
# 		self.validate_approver()
# 		self.validate_default_shift()

# 	def on_update(self):
# 		share_doc_with_approver(self, self.approver)

# 	def on_submit(self):
# 		if self.status not in ["Approved", "Rejected"]:
# 			frappe.throw(_("Only Shift Request with status 'Approved' and 'Rejected' can be submitted"))
# 		if self.status == "Approved":
# 			assignment_doc = frappe.new_doc("Shift Assignment")
# 			assignment_doc.company = self.company
# 			assignment_doc.shift_type = self.shift_type
# 			assignment_doc.employee = self.employee
# 			assignment_doc.start_date = self.from_date
# 			if self.to_date:
# 				assignment_doc.end_date = self.to_date
# 			assignment_doc.shift_request = self.name
# 			assignment_doc.flags.ignore_permissions = 1
# 			assignment_doc.insert()
# 			assignment_doc.submit()

# 			frappe.msgprint(
# 				_("Shift Assignment: {0} created for Employee: {1}").format(
# 					frappe.bold(assignment_doc.name), frappe.bold(self.employee)
# 				)
# 			)

# 	def on_cancel(self):
# 		shift_assignment_list = frappe.get_list(
# 			"Shift Assignment", {"employee": self.employee, "shift_request": self.name}
# 		)
# 		if shift_assignment_list:
# 			for shift in shift_assignment_list:
# 				shift_assignment_doc = frappe.get_doc("Shift Assignment", shift["name"])
# 				shift_assignment_doc.cancel()

# 	def validate_default_shift(self):
# 		default_shift = frappe.get_value("Employee", self.employee, "default_shift")
# 		if self.shift_type == default_shift:
# 			frappe.throw(
# 				_("You can not request for your Default Shift: {0}").format(frappe.bold(self.shift_type))
# 			)

# 	def validate_approver(self):
# 		department = frappe.get_value("Employee", self.employee, "department")
# 		shift_approver = frappe.get_value("Employee", self.employee, "shift_request_approver")
# 		approvers = frappe.db.sql(
# 			"""select approver from `tabDepartment Approver` where parent= %s and parentfield = 'shift_request_approver'""",
# 			(department),
# 		)
# 		approvers = [approver[0] for approver in approvers]
# 		approvers.append(shift_approver)
# 		if self.approver not in approvers:
# 			frappe.throw(_("Only Approvers can Approve this Request."))

# 	def validate_overlapping_shift_requests(self):
# 		overlapping_dates = self.get_overlapping_dates()
# 		if len(overlapping_dates):
# 			# if dates are overlapping, check if timings are overlapping, else allow
# 			overlapping_timings = has_overlapping_timings(self.shift_type, overlapping_dates[0].shift_type)
# 			if overlapping_timings:
# 				self.throw_overlap_error(overlapping_dates[0])

# 	def get_overlapping_dates(self):
# 		if not self.name:
# 			self.name = "New Shift Request"

# 		shift = frappe.qb.DocType("Shift Request")
# 		query = (
# 			frappe.qb.from_(shift)
# 			.select(shift.name, shift.shift_type)
# 			.where((shift.employee == self.employee) & (shift.docstatus < 2) & (shift.name != self.name))
# 		)

# 		if self.to_date:
# 			query = query.where(
# 				Criterion.any(
# 					[
# 						Criterion.any(
# 							[
# 								shift.to_date.isnull(),
# 								((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date)),
# 							]
# 						),
# 						Criterion.any(
# 							[
# 								((self.to_date >= shift.from_date) & (self.to_date <= shift.to_date)),
# 								shift.from_date.between(self.from_date, self.to_date),
# 							]
# 						),
# 					]
# 				)
# 			)
# 		else:
# 			query = query.where(
# 				shift.to_date.isnull()
# 				| ((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date))
# 			)

# 		return query.run(as_dict=True)

# 	def throw_overlap_error(self, shift_details):
# 		shift_details = frappe._dict(shift_details)
# 		msg = _(
# 			"Employee {0} has already applied for Shift {1}: {2} that overlaps within this period"
# 		).format(
# 			frappe.bold(self.employee),
# 			frappe.bold(shift_details.shift_type),
# 			get_link_to_form("Shift Request", shift_details.name),
# 		)

# 		frappe.throw(msg, title=_("Overlapping Shift Requests"), exc=OverlappingShiftRequestError)
